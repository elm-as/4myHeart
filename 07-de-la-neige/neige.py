# -*- coding: utf-8 -*-
"""
neige.py  --  De la neige qui tient.

Faire tomber des flocons, tout le monde sait le faire. Le sujet ici est
ailleurs : c'est que la neige **reste**.

Le sol n'est pas une image. C'est un tableau de 720 nombres -- une hauteur
par colonne de pixels. Quand un flocon touche, il ajoute un peu de matiere
a sa colonne et a ses voisines, puis il disparait. Et a chaque image, le
tableau se lisse legerement contre lui-meme :

    neige = neige * (1 - 2L)  +  L * (voisin_gauche + voisin_droit)

Cette seule ligne, repetee, est ce qui transforme des milliers de petits tas
en une congere lisse. C'est de la diffusion : exactement ce que fait la
chaleur dans une barre de metal, et exactement ce que fait la neige au vent.

    python neige.py

    ESPACE : deneiger     ECHAP : quitter
"""

import math
import sys

import numpy as np
import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
FPS = 60

NB_FLOCONS = 1700
CHUTE_MIN, CHUTE_MAX = 42.0, 105.0     # vitesses de chute, du fond au premier plan
VENT = 16.0                            # derive laterale moyenne, en pixels/seconde
DEPOT = 13.0                           # la matiere qu'un flocon depose, en pixels carres
ETALEMENT = 13                         # sur combien de colonnes, de part et d'autre
LISSAGE = 0.18                         # combien la congere se tasse a chaque image

SOL = 1120                             # la ligne de base du terrain

CIEL_HAUT = (8, 10, 20)
CIEL_BAS = (34, 38, 58)
COLLINE_LOIN = (22, 26, 42)
COLLINE_PRES = (14, 17, 28)
CROUTE = (250, 252, 255)
FLOCON = (236, 241, 250)
NEIGE = [(230, 236, 248), (203, 212, 233), (178, 189, 214)]   # du dessus vers le fond

# Un flocon ne se pose pas sur une colonne : il se pose autour. Cette petite
# cloche est ce qui evite que la congere ressemble a une scie.
_ecart = np.arange(-ETALEMENT, ETALEMENT + 1, dtype=np.float32)
CLOCHE = np.exp(-(_ecart / (ETALEMENT * 0.55)) ** 2)
CLOCHE *= DEPOT / CLOCHE.sum()


# ------------------------------------------------------------------ le sol

def terrain():
    x = np.arange(LARGEUR, dtype=np.float32)
    return (SOL
            - 34.0 * np.sin(x / 182.0)
            - 19.0 * np.sin(x / 71.0 + 1.2)
            - 9.0 * np.sin(x / 29.0 + 2.7)).astype(np.float32)


def tasser(neige):
    """La diffusion : chaque colonne partage un peu avec ses deux voisines."""
    milieu = neige[1:-1]
    neige[1:-1] = milieu * (1.0 - 2.0 * LISSAGE) + LISSAGE * (neige[:-2] + neige[2:])
    neige[0] = neige[1]
    neige[-1] = neige[-2]


# -------------------------------------------------------------- les flocons

def sprites_flocons():
    """Un flocon est toujours le meme petit rond : on le prepare une fois."""
    liste = []
    for rayon in range(1, 5):
        s = pygame.Surface((rayon * 6, rayon * 6), pygame.SRCALPHA)
        c = (rayon * 3, rayon * 3)
        pygame.draw.circle(s, (*FLOCON, 34), c, rayon * 2)
        pygame.draw.circle(s, (*FLOCON, 225), c, rayon)
        liste.append(s)
    return liste


class Flocons:
    def __init__(self):
        self.x = np.random.uniform(-60, LARGEUR + 60, NB_FLOCONS).astype(np.float32)
        # Il neige deja quand la video commence : le sujet, c'est ce qui s'accumule.
        self.y = np.random.uniform(-HAUTEUR, SOL, NB_FLOCONS).astype(np.float32)
        # La profondeur : elle decide de tout, la taille comme la vitesse.
        self.loin = np.random.random(NB_FLOCONS).astype(np.float32)
        self.vy = CHUTE_MIN + (CHUTE_MAX - CHUTE_MIN) * (1.0 - self.loin)
        self.taille = np.clip((1.0 - self.loin) * 4.0, 0, 3).astype(np.int32)
        self.ampleur = np.random.uniform(6, 30, NB_FLOCONS).astype(np.float32)
        self.cadence = np.random.uniform(0.4, 1.3, NB_FLOCONS).astype(np.float32)
        self.phase = np.random.uniform(0, math.tau, NB_FLOCONS).astype(np.float32)

    def renaitre(self, ou):
        n = int(ou.sum())
        if n == 0:
            return
        self.x[ou] = np.random.uniform(-60, LARGEUR + 60, n)
        self.y[ou] = np.random.uniform(-160, -10, n)

    def tomber(self, dt, t, hauteur_du_sol, neige):
        self.x += VENT * dt * (0.4 + 1.2 * (1.0 - self.loin))
        self.y += self.vy * dt

        # Le balancement : c'est lui qui empeche la neige de tomber comme de la pluie.
        vue = self.x + np.sin(t * self.cadence + self.phase) * self.ampleur
        np.mod(vue, LARGEUR, out=vue)

        colonne = vue.astype(np.int32)
        pose = self.y >= hauteur_du_sol[colonne]
        if pose.any():
            for c in colonne[pose]:
                a, b = c - ETALEMENT, c + ETALEMENT + 1
                debut, fin = max(0, a), min(LARGEUR, b)
                neige[debut:fin] += CLOCHE[debut - a:fin - a]
            self.renaitre(pose)
        return vue


# ------------------------------------------------------------------ le decor

def ciel():
    surface = pygame.Surface((LARGEUR, HAUTEUR))
    for y in range(HAUTEUR):
        k = (y / HAUTEUR) ** 0.8
        surface.fill(tuple(int(CIEL_HAUT[i] + (CIEL_BAS[i] - CIEL_HAUT[i]) * k)
                           for i in range(3)), (0, y, LARGEUR, 1))
    alea = np.random.RandomState(4)
    for _ in range(70):
        x, y = alea.randint(0, LARGEUR), alea.randint(0, 620)
        clair = alea.randint(70, 150)
        surface.set_at((x, y), (clair, clair, clair + 16))

    for decalage, couleur, creux in ((0, COLLINE_LOIN, 250), (1, COLLINE_PRES, 150)):
        points = [(x, SOL - creux - 70 * math.sin(x / 260.0 + decalage * 2.1)
                   - 30 * math.sin(x / 97.0 + decalage)) for x in range(0, LARGEUR + 8, 8)]
        points += [(LARGEUR, HAUTEUR), (0, HAUTEUR)]
        pygame.draw.polygon(surface, couleur, points)
    return surface


def dessiner_congere(toile, hauteur_du_sol):
    bord = [(x, float(hauteur_du_sol[x])) for x in range(0, LARGEUR, 3)]
    bord.append((LARGEUR - 1, float(hauteur_du_sol[-1])))

    # Trois couches decalees vers le bas : la neige s'assombrit en profondeur
    # tout en suivant exactement le relief de la croute.
    for couleur, dessous in zip(NEIGE, (0, 26, 130)):
        pygame.draw.polygon(toile, couleur,
                            [(x, y + dessous) for x, y in bord]
                            + [(LARGEUR, HAUTEUR), (0, HAUTEUR)])
    pygame.draw.lines(toile, CROUTE, False, bord, 3)


# -------------------------------------------------------------------- le film

def ouvrir(titre):
    """Une fenetre 9:16 qui tient sur l'ecran.

    On dessine toujours dans 720 x 1280. Si l'ecran est plus petit -- un
    portable de 14 pouces annonce souvent 720 pixels de haut -- la fenetre
    l'est aussi, mais garde exactement la meme forme. Ce qu'on capture
    reste donc du 9:16. Lancer avec --plein force la taille d'origine.
    """
    pygame.init()
    pygame.display.set_caption(titre)
    haut = HAUTEUR
    if "--plein" not in sys.argv:
        haut = max(420, min(HAUTEUR, int(pygame.display.Info().current_h * 0.88)))
    return pygame.display.set_mode((max(2, round(haut * LARGEUR / HAUTEUR)), haut))


def main():
    fenetre = ouvrir("de la neige")
    toile = pygame.Surface((LARGEUR, HAUTEUR))
    horloge = pygame.time.Clock()

    decor = ciel()
    sprites = sprites_flocons()
    base = terrain()
    neige = np.zeros(LARGEUR, np.float32)
    flocons = Flocons()
    etat = {"t": 0.0}

    def deneiger():
        neige[:] = 0.0
        etat["t"] = 0.0

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    deneiger()

        dt = min(horloge.tick(FPS) / 1000.0, 1 / 20)
        etat["t"] += dt
        t = etat["t"]

        hauteur_du_sol = base - neige
        vue = flocons.tomber(dt, t, hauteur_du_sol, neige)
        tasser(neige)

        toile.blit(decor, (0, 0))

        # Les flocons d'abord : la congere passera par-dessus, et les avalera.
        for i in range(NB_FLOCONS):
            s = sprites[flocons.taille[i]]
            m = s.get_width() // 2
            toile.blit(s, (int(vue[i]) - m, int(flocons.y[i]) - m))

        dessiner_congere(toile, hauteur_du_sol)
        pygame.transform.smoothscale(toile, fenetre.get_size(), fenetre)
        pygame.display.flip()


if __name__ == "__main__":
    sys.exit(main())
