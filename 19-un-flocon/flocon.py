# -*- coding: utf-8 -*-
"""
flocon.py  --  Une case de glace, de la vapeur autour, et la symetrie a six
                sort toute seule.

La symetrie n'est ecrite nulle part dans ce fichier. Cherche : il n'y a pas de
rotation, pas de miroir, pas de "et on recopie sur les six branches". Il y a une
grille hexagonale, une case de glace au milieu, et deux lignes de regle.

Le modele est celui de Clifford Reiter (2005), le plus simple qui donne de vrais
flocons. Chaque case porte un nombre s : la quantite d'eau qu'elle contient. Une
case est de la glace des que s >= 1.

A chaque pas, on partage l'eau de chaque case en deux :

  -  les cases **receptives** -- la glace, et tout ce qui la touche -- mettent
     leur eau de cote. Elle ne diffuse plus. Et elles en recoivent un peu plus,
     gamma, a chaque pas : c'est la vapeur du nuage qui vient se poser.
  -  les autres laissent leur eau diffuser vers les six voisines.

Puis on recolle les deux parts. C'est tout.

    u = eau qui diffuse      v = eau mise de cote
    u  <-  u + (alpha/2) . (moyenne des six voisines - u)
    s  <-  u + v

Ce qui se passe alors est la seule chose importante du programme : une pointe
qui depasse touche **plus de vapeur** qu'un creux, donc elle grossit plus vite,
donc elle depasse davantage. C'est l'instabilite de Mullins-Sekerka, et c'est
elle qui fabrique les branches. Personne ne les dessine.

Et la symetrie ? Elle vient de ce que les six directions de la grille sont
identiques, et que le depart est une seule case. Les six branches ne se
recopient pas l'une l'autre : elles subissent exactement la meme chose.

Trois nombres suffisent a changer completement le flocon :

    alpha   la vitesse de diffusion       1,0 a 2,0
    beta    la vapeur du depart           0,3 a 0,9  -- c'est lui qui compte
    gamma   ce qui se depose par pas      0 a 0,01

    python flocon.py

    ESPACE : un autre flocon     ECHAP : quitte
"""

import sys

import numpy as np
import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
FPS = 60

N = 261                 # le cote de la grille hexagonale : 68 121 cases
RMAX = 112              # le rayon ou on arrete : le flocon tient dans la largeur
RAYON = 2.70            # la taille d'une case a l'ecran, en pixels
ZOOM = 2                # on dessine en 360 x 640, puis on agrandit
DUREE = 26.0            # la duree visee pour la croissance, en secondes

T_NUIT = 1.2            # le noir du debut
T_APRES = 5.0           # ce qu'on laisse voir le flocon fini

# Les familles de flocons : (alpha, beta, gamma, pas mesures pour finir).
# Elles ne se ressemblent pas, et c'est le sujet. Le dernier nombre est
# mesure, pas choisi : une plaque est finie en 557 pas, une etoile a branches
# fines en met 3 283. On s'en sert pour donner a chacune la meme duree a
# l'ecran -- sinon la meme video dure entre 9 et 55 secondes selon le tirage.
FAMILLES = [
    (1.00, 0.40, 0.0001, 2422),   # l'etoile a six branches, la plus classique
    (1.00, 0.35, 0.0010, 3283),   # des branches plus fines, plus longues
    (2.00, 0.40, 0.0001, 1215),   # des aiguilles
    (1.00, 0.60, 0.0100, 557),    # une plaque, presque pleine
    (1.00, 0.50, 0.0010, 1220),   # des dendrites avec des plaques au bout
    (1.60, 0.45, 0.0005, 1106),   # un compromis, tres decoupe
]

GLACE = 1.0             # a partir de quelle valeur une case est de la glace

# --- couleurs
NUIT = (6, 8, 14)
VAPEUR = (16, 26, 48)           # la vapeur, a peine visible
BORD = (86, 132, 200)           # le pourtour de la glace : bleu
COEUR = (232, 244, 255)         # la glace epaisse : blanc bleute
HALO = 0.42                     # la lueur autour du flocon


# ------------------------------------------------------------- la palette

def palette():
    """De la vapeur (s petit) a la glace epaisse (s grand).

    La marche a s = 1 est la seule chose qu'on force a l'image : en dessous
    c'est de l'air, au-dessus c'est du solide. Le reste est continu.
    """
    d = np.zeros((512, 3), np.float32)
    s = np.linspace(0.0, 2.0, 512, dtype=np.float32)
    air = s / GLACE
    for c in range(3):
        d[:, c] = np.interp(np.clip(air, 0, 1), [0.0, 1.0],
                            [NUIT[c], VAPEUR[c]])
    glace = np.clip((s - GLACE) / 0.55, 0.0, 1.0)
    for c in range(3):
        froid = np.interp(glace, [0.0, 1.0], [BORD[c], COEUR[c]])
        d[:, c] = np.where(s >= GLACE, froid, d[:, c])
    return d.astype(np.uint8)


# ------------------------------------------------------------- le cristal

class Cristal:
    """La grille hexagonale et les deux lignes de regle.

    La grille est rangee en coordonnees axiales (q, r) : un simple tableau
    carre, dont les six voisines d'une case sont

        (q+1, r) (q-1, r) (q, r+1) (q, r-1) (q+1, r-1) (q-1, r+1)

    Autrement dit six decalages du tableau. C'est tout ce qu'il faut pour
    travailler sur des hexagones -- la difference avec un carre n'est pas dans
    le stockage, elle est dans le fait qu'il y a six voisines au lieu de
    quatre, et que les six sont a la meme distance.
    """

    def __init__(self, alpha, beta, gamma, attendus):
        self.alpha, self.beta, self.gamma = alpha, beta, gamma
        self.cadence = attendus / (DUREE * FPS)     # pas par image
        self.retard = 0.0
        self.s = np.full((N, N), np.float32(beta))
        self.s[N // 2, N // 2] = np.float32(GLACE)
        self.pas = 0
        self.fini = False
        self.u = np.empty((N, N), np.float32)
        self.v = np.empty((N, N), np.float32)
        self.somme = np.empty((N, N), np.float32)
        self.recept = np.zeros((N, N), bool)
        # l'anneau ou l'on declare le flocon fini : en hexagonal, la distance
        # entre deux cases vaut (|dq| + |dr| + |dq+dr|) / 2
        q, r = np.meshgrid(np.arange(N) - N // 2, np.arange(N) - N // 2,
                           indexing='ij')
        d = (np.abs(q) + np.abs(r) + np.abs(q + r)) // 2
        self.anneau = np.flatnonzero(((d >= RMAX) & (d <= RMAX + 1)).reshape(-1))

    def avancer(self):
        s, u, v = self.s, self.u, self.v

        # receptives : la glace et ses six voisines
        glace = s >= np.float32(GLACE)
        r = self.recept
        np.copyto(r, glace)
        r[1:, :] |= glace[:-1, :]
        r[:-1, :] |= glace[1:, :]
        r[:, 1:] |= glace[:, :-1]
        r[:, :-1] |= glace[:, 1:]
        r[1:, :-1] |= glace[:-1, 1:]
        r[:-1, 1:] |= glace[1:, :-1]

        # on partage l'eau : ce qui diffuse, ce qui reste
        np.copyto(u, s)
        u[r] = 0.0
        np.subtract(s, u, out=v)
        v[r] += np.float32(self.gamma)

        # diffusion sur les six voisines
        m = self.somme
        np.add(np.roll(u, 1, 0), np.roll(u, -1, 0), out=m)
        m += np.roll(u, 1, 1)
        m += np.roll(u, -1, 1)
        m += np.roll(np.roll(u, 1, 0), -1, 1)
        m += np.roll(np.roll(u, -1, 0), 1, 1)
        m *= np.float32(1.0 / 6.0)
        np.subtract(m, u, out=m)
        m *= np.float32(self.alpha * 0.5)
        u += m

        np.add(u, v, out=s)

        # le bord du tableau reste a la vapeur du depart : le nuage est grand,
        # il ne se vide pas. Sans ca, le flocon epuise l'air de la fenetre et
        # s'arrete de pousser avant d'etre beau.
        s[:2, :] = s[-2:, :] = self.beta
        s[:, :2] = s[:, -2:] = self.beta

        self.pas += 1
        if not self.fini:
            self.fini = bool((s.reshape(-1)[self.anneau] >= GLACE).any())

    def cases(self):
        return int((self.s >= GLACE).sum())


# ---------------------------------------------------------------- l'image

def table_hexagones(large, haut, rayon):
    """Pour chaque pixel, la case hexagonale sous lui.

    C'est la seule partie penible de la grille hexagonale, et on ne la fait
    qu'une fois. On inverse la transformation, ce qui donne des coordonnees
    fractionnaires ; puis on arrondit **en coordonnees cubiques** -- on arrondit
    les trois, et on corrige celle qui a le plus bouge. Arrondir simplement les
    deux coordonnees du tableau donnerait des losanges au lieu d'hexagones, et
    ca se verrait tout de suite : le flocon serait penche.
    """
    px = (np.arange(large, dtype=np.float32) - large * 0.5)[:, None]
    py = (np.arange(haut, dtype=np.float32) - haut * 0.5)[None, :]
    fr = py / (rayon * np.sqrt(3.0) * 0.5)
    fq = px / rayon - fr * 0.5

    x, z = fq, fr
    y = -x - z
    rx, ry, rz = np.round(x), np.round(y), np.round(z)
    dx, dy, dz = np.abs(rx - x), np.abs(ry - y), np.abs(rz - z)
    plus_x = (dx > dy) & (dx > dz)
    plus_y = (~plus_x) & (dy > dz)
    rx = np.where(plus_x, -ry - rz, rx)
    rz = np.where(plus_y | plus_x, rz, -rx - ry)

    q = np.clip(rx + N // 2, 0, N - 1).astype(np.int32)
    r = np.clip(rz + N // 2, 0, N - 1).astype(np.int32)
    return (q * N + r).astype(np.int32)


class Vue:
    def __init__(self):
        self.L, self.H = LARGEUR // ZOOM, HAUTEUR // ZOOM
        self.table = table_hexagones(self.L, self.H, RAYON / ZOOM)
        self.couleurs = palette()
        self.petite = pygame.Surface((self.L, self.H))
        self.floue = pygame.Surface((self.L // 4, self.H // 4))
        self.lueur = pygame.Surface((self.L, self.H))
        self.pixels = np.empty((self.L, self.H, 3), np.uint8)

    def dessiner(self, cristal, ecran):
        brut = cristal.s.reshape(-1)[self.table]
        brut *= np.float32(255.5)
        np.clip(brut, 0, 511, out=brut)
        np.take(self.couleurs, brut.astype(np.int32), axis=0, out=self.pixels)
        pygame.surfarray.blit_array(self.petite, self.pixels)

        # le halo : la meme image, reduite puis rendue, donc floue
        pygame.transform.smoothscale(self.petite, self.floue.get_size(), self.floue)
        pygame.transform.smoothscale(self.floue, (self.L, self.H), self.lueur)
        self.lueur.fill((int(255 * HALO),) * 3, special_flags=pygame.BLEND_MULT)
        self.petite.blit(self.lueur, (0, 0), special_flags=pygame.BLEND_ADD)

        pygame.transform.smoothscale(self.petite, ecran.get_size(), ecran)


# ---------------------------------------------------------------- la fenetre

def ouvrir(titre):
    """Une fenetre 9:16 qui tient sur l'ecran, comme partout dans ce dossier."""
    pygame.init()
    pygame.display.set_caption(titre)
    haut = HAUTEUR
    if "--plein" not in sys.argv:
        haut = max(420, min(HAUTEUR, int(pygame.display.Info().current_h * 0.88)))
    return pygame.display.set_mode((max(2, round(haut * LARGEUR / HAUTEUR)), haut))


def main():
    fenetre = ouvrir("un flocon")
    horloge = pygame.time.Clock()
    vue = Vue()

    def naitre():
        return Cristal(*FAMILLES[np.random.randint(len(FAMILLES))]), 0.0, None

    cristal, t, fin = naitre()

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    cristal, t, fin = naitre()

        t += min(horloge.tick(FPS) / 1000.0, 1 / 20)
        if t >= T_NUIT and not cristal.fini:
            cristal.retard += cristal.cadence
            while cristal.retard >= 1.0 and not cristal.fini:
                cristal.avancer()
                cristal.retard -= 1.0
            if cristal.fini:
                fin = t

        vue.dessiner(cristal, fenetre)
        pygame.display.flip()

        if fin is not None and t - fin > T_APRES:
            cristal, t, fin = naitre()


if __name__ == "__main__":
    sys.exit(main())
