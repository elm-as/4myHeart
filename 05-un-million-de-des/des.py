# -*- coding: utf-8 -*-
"""
des.py  --  Cinq des, un million de fois.

On lance cinq des, on note la somme, on recommence. C'est tout le programme.

Personne ne dessine de courbe. Personne ne calcule de moyenne. On empile
betement des resultats -- et au bout d'un moment, une forme apparait,
toujours la meme, que personne n'a demandee.

A la fin, on superpose la courbe que les maths avaient prevue.
Elle tombe pile dessus.

    python des.py

    ESPACE : recommencer     ECHAP : quitter
"""

import math
import sys

import numpy as np
import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
FPS = 60

NB_DES = 5
FACES = 6
MINI, MAXI = NB_DES, NB_DES * FACES          # sommes possibles : 5 a 30

OBJECTIF = 1_000_000
DEPART = 2.0        # a quelle seconde part le premier lancer
DUREE = 20.0        # et en combien de temps on atteint le million
REVELATION = 1.8    # duree du fondu de la courbe theorique, a la fin

FOND = (12, 12, 18)
BARRE = (228, 178, 132)
BARRE_SOMBRE = (92, 66, 48)
COURBE = (150, 206, 226)
TEXTE = (236, 230, 222)
DISCRET = (104, 100, 110)

HAUT_DES = 190       # ou sont dessines les cinq des
HAUT_NOMBRE = 360    # ou est affiche le compteur
SOL = 1150           # la ligne du bas de l'histogramme
CIEL = 560           # et la hauteur maximale d'une barre
MARGE = 58


# ------------------------------------------------------------- les lancers

def combien_a_cet_instant(t):
    """Le nombre total de lancers effectues a l'instant t.

    On monte par puissances de dix : 1, puis 10, puis 100... C'est la seule
    facon de voir a la fois le premier lancer et le millionieme.
    """
    if t < DEPART:
        return 0
    avance = min((t - DEPART) / DUREE, 1.0)
    return min(OBJECTIF, int(10.0 ** (math.log10(OBJECTIF) * avance)))


def courbe_prevue(x):
    """Ce que les maths annoncaient, avant qu'on lance quoi que ce soit.

    Un de moyen vaut 3,5 et varie de 35/12. Cinq des, c'est cinq fois ca --
    et la somme de plusieurs hasards independants tend vers cette cloche.
    """
    moyenne = NB_DES * (FACES + 1) / 2.0
    variance = NB_DES * (FACES * FACES - 1) / 12.0
    return math.exp(-((x - moyenne) ** 2) / (2.0 * variance))


# ---------------------------------------------------------------- le dessin

PIONS = {                                    # ou sont les points, sur une face
    1: [(1, 1)],
    2: [(0, 0), (2, 2)],
    3: [(0, 0), (1, 1), (2, 2)],
    4: [(0, 0), (2, 0), (0, 2), (2, 2)],
    5: [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)],
    6: [(0, 0), (2, 0), (0, 1), (2, 1), (0, 2), (2, 2)],
}


def dessiner_des(toile, faces):
    cote, ecart = 78, 22
    total = NB_DES * cote + (NB_DES - 1) * ecart
    x0 = (LARGEUR - total) // 2
    for i, face in enumerate(faces):
        x = x0 + i * (cote + ecart)
        pygame.draw.rect(toile, (30, 30, 40),
                         pygame.Rect(x, HAUT_DES, cote, cote), border_radius=16)
        pygame.draw.rect(toile, (72, 70, 84),
                         pygame.Rect(x, HAUT_DES, cote, cote), 2, border_radius=16)
        for cx, cy in PIONS[int(face)]:
            pygame.draw.circle(toile, TEXTE,
                               (x + 19 + cx * 20, HAUT_DES + 19 + cy * 20), 7)


def dessiner_barres(toile, comptes):
    sommet = comptes.max()
    if sommet == 0:
        return
    nb = MAXI - MINI + 1
    large = (LARGEUR - 2 * MARGE) / nb
    for i in range(nb):
        h = int((comptes[MINI + i] / sommet) * CIEL)
        x = MARGE + i * large
        if h < 1:
            pygame.draw.line(toile, BARRE_SOMBRE, (x + 2, SOL), (x + large - 4, SOL))
            continue
        rect = pygame.Rect(int(x + 2), SOL - h, int(large - 4), h)
        pygame.draw.rect(toile, BARRE, rect, border_radius=3)


def dessiner_courbe(toile, alpha):
    if alpha <= 0:
        return
    nb = MAXI - MINI + 1
    large = (LARGEUR - 2 * MARGE) / nb
    points = []
    for k in range(241):
        s = MINI + (MAXI - MINI) * k / 240.0
        x = MARGE + (s - MINI + 0.5) * large
        points.append((x, SOL - courbe_prevue(s) * CIEL))
    calque = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
    pygame.draw.lines(calque, (*COURBE, int(alpha * 255)), False, points, 3)
    toile.blit(calque, (0, 0))


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
    fenetre = ouvrir("un million de des")
    toile = pygame.Surface((LARGEUR, HAUTEUR))
    horloge = pygame.time.Clock()

    chemin = pygame.font.match_font("consolas") or pygame.font.match_font("segoeui")
    grande = pygame.font.Font(chemin, 76)
    petite = pygame.font.Font(chemin, 26)

    comptes = np.zeros(MAXI + 1, np.int64)
    faces = np.full(NB_DES, 1)
    etat = {"t": 0.0, "faits": 0}

    def recommencer():
        comptes[:] = 0
        etat.update(t=0.0, faits=0)

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    recommencer()

        etat["t"] += min(horloge.tick(FPS) / 1000.0, 1 / 20)
        t = etat["t"]

        # Combien de lancers depuis la derniere image ?
        vise = combien_a_cet_instant(t)
        neufs = vise - etat["faits"]
        if neufs > 0:
            tirage = np.random.randint(1, FACES + 1, (neufs, NB_DES))
            comptes += np.bincount(tirage.sum(axis=1), minlength=MAXI + 1)
            faces = tirage[-1]
            etat["faits"] = vise

        toile.fill(FOND)
        dessiner_des(toile, faces)

        nombre = grande.render("{:,}".format(etat["faits"]).replace(",", " "), True, TEXTE)
        toile.blit(nombre, (LARGEUR // 2 - nombre.get_width() // 2, HAUT_NOMBRE))
        mot = petite.render("lancers", True, DISCRET)
        toile.blit(mot, (LARGEUR // 2 - mot.get_width() // 2, HAUT_NOMBRE + 92))

        dessiner_barres(toile, comptes)
        pygame.draw.line(toile, DISCRET, (MARGE, SOL), (LARGEUR - MARGE, SOL))

        # Une fois le million atteint, on superpose ce que les maths prevoyaient.
        fini = etat["faits"] >= OBJECTIF
        if fini:
            trop = t - (DEPART + DUREE)
            dessiner_courbe(toile, min(trop / REVELATION, 1.0))

        for somme, cote in ((MINI, MARGE), (MAXI, LARGEUR - MARGE)):
            img = petite.render(str(somme), True, DISCRET)
            toile.blit(img, (cote - img.get_width() // 2, SOL + 14))

        pygame.transform.smoothscale(toile, fenetre.get_size(), fenetre)
        pygame.display.flip()


if __name__ == "__main__":
    sys.exit(main())
