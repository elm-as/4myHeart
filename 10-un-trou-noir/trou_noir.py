# -*- coding: utf-8 -*-
"""
trou_noir.py  --  Un nuage, puis un disque, puis plus rien.

Personne ne dessine de disque ici. On lache vingt mille poussieres autour
d'un point, avec une seule loi -- celle de Newton, vieille de 1687 :

    acceleration  =  GM * d / r^3

et un frottement minuscule, parce que ces poussieres se frottent les unes
aux autres. C'est tout.

Le nuage s'aplatit tout seul en un disque, parce que les orbites qui vont
a contresens s'annulent et que seules survivent celles qui tournent dans le
meme sens. Puis le frottement leur fait perdre, tour apres tour, ce qui les
tenait en l'air -- et elles tombent.

Le rond noir au centre n'est pas dessine non plus. C'est juste l'endroit
d'ou l'on ne revient pas.

    python trou_noir.py

    ESPACE : relancer le nuage     ECHAP : quitter
"""

import math
import sys

import numpy as np
import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
FPS = 60

NB = 20000
CENTRE = np.array([LARGEUR / 2, HAUTEUR / 2], np.float32)

GM = 1.452e7            # la masse, en pixels et secondes
HORIZON = 40.0          # le rayon d'ou l'on ne revient pas
FROTTEMENT = 0.040      # ce qui fait tomber les orbites, tour apres tour
DOUCEUR = 90.0          # evite l'infini quand une poussiere frole le centre

NAISSANCE_MIN, NAISSANCE_MAX = 300.0, 620.0
TRAINEE = 0.90          # 0 = des points, 0.96 = de longues tracees


def palette():
    """Du rouge sombre au blanc bleute : la vitesse fait la couleur."""
    arrets = [(0.00, (60, 10, 6)), (0.22, (150, 40, 12)), (0.45, (232, 110, 30)),
              (0.68, (255, 190, 96)), (0.86, (255, 242, 210)), (1.00, (214, 230, 255))]
    table = np.zeros((256, 3), np.float32)
    for c in range(3):
        table[:, c] = np.interp(np.linspace(0, 1, 256),
                                [a[0] for a in arrets], [a[1][c] for a in arrets])
    return table


PALETTE = palette()
VITESSE_MAX = 760.0


# ------------------------------------------------------------ la poussiere

class Nuage:
    def __init__(self):
        self.semer(np.ones(NB, bool))

    def semer(self, qui):
        """Naissance loin, sur une orbite presque ronde, toutes dans le meme sens.

        Presque -- pas tout a fait. C'est le petit desordre qu'on ajoute ici
        qui donne au disque son epaisseur et ses vagues.
        """
        n = int(qui.sum())
        if n == 0:
            return
        angle = np.random.uniform(0, math.tau, n)
        rayon = np.sqrt(np.random.uniform(NAISSANCE_MIN ** 2, NAISSANCE_MAX ** 2, n))

        pos = np.empty((n, 2), np.float32)
        pos[:, 0] = CENTRE[0] + np.cos(angle) * rayon
        pos[:, 1] = CENTRE[1] + np.sin(angle) * rayon

        # La vitesse qui tient une orbite ronde, a ce rayon-la.
        ronde = np.sqrt(GM / rayon) * np.random.uniform(0.72, 1.06, n)
        vit = np.empty((n, 2), np.float32)
        vit[:, 0] = -np.sin(angle) * ronde
        vit[:, 1] = np.cos(angle) * ronde
        vit += np.random.normal(0, 26, (n, 2))

        if not hasattr(self, "pos"):
            self.pos = np.zeros((NB, 2), np.float32)
            self.vit = np.zeros((NB, 2), np.float32)
        self.pos[qui] = pos
        self.vit[qui] = vit

    def avancer(self, dt):
        vers = CENTRE - self.pos
        r2 = (vers * vers).sum(1) + DOUCEUR
        r = np.sqrt(r2)

        # Newton, 1687. Une ligne.
        self.vit += vers * (GM * dt / (r2 * r))[:, None]
        self.vit *= 1.0 - FROTTEMENT * dt
        self.pos += self.vit * dt

        # Celles qui ont franchi l'horizon ne reviennent pas : on les renvoie
        # au loin, pour que le spectacle continue.
        perdues = r < HORIZON
        if perdues.any():
            self.semer(perdues)
        return r


# ---------------------------------------------------------------- le dessin

def peindre(champ, nuage, dt):
    champ *= TRAINEE ** (dt * FPS)

    x = nuage.pos[:, 0].astype(np.int32)
    y = nuage.pos[:, 1].astype(np.int32)
    dedans = (x >= 1) & (x < LARGEUR - 1) & (y >= 1) & (y < HAUTEUR - 1)
    x, y = x[dedans], y[dedans]

    vitesse = np.linalg.norm(nuage.vit[dedans], axis=1)
    niveau = np.clip(vitesse / VITESSE_MAX * 255.0, 0, 255).astype(np.int32)
    couleur = PALETTE[niveau] * 0.40

    champ[x, y] += couleur
    bord = couleur * 0.26
    champ[x + 1, y] += bord
    champ[x - 1, y] += bord
    champ[x, y + 1] += bord
    champ[x, y - 1] += bord


def trou(toile):
    """Le noir, et l'anneau de lumiere qui le cerne."""
    centre = (int(CENTRE[0]), int(CENTRE[1]))
    pygame.draw.circle(toile, (0, 0, 0), centre, int(HORIZON))
    anneau = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
    for i, (ecart, alpha) in enumerate(((0, 150), (2, 80), (4, 34), (7, 14))):
        pygame.draw.circle(anneau, (255, 238, 214, alpha), centre,
                           int(HORIZON) + ecart, 2)
    toile.blit(anneau, (0, 0), special_flags=pygame.BLEND_RGB_ADD)


# ------------------------------------------------------------------ le film

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
    fenetre = ouvrir("un trou noir")
    toile = pygame.Surface((LARGEUR, HAUTEUR))
    horloge = pygame.time.Clock()

    champ = np.zeros((LARGEUR, HAUTEUR, 3), np.float32)
    tampon = np.zeros((LARGEUR, HAUTEUR, 3), np.uint8)
    nuage = Nuage()

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    nuage = Nuage()
                    champ[:] = 0.0

        dt = min(horloge.tick(FPS) / 1000.0, 1 / 20)
        nuage.avancer(dt)
        peindre(champ, nuage, dt)

        np.clip(champ, 0, 255, out=champ)
        np.copyto(tampon, champ, casting="unsafe")
        pygame.surfarray.blit_array(toile, tampon)
        trou(toile)
        pygame.transform.smoothscale(toile, fenetre.get_size(), fenetre)
        pygame.display.flip()


if __name__ == "__main__":
    sys.exit(main())
