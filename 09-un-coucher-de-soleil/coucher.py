# -*- coding: utf-8 -*-
"""
coucher.py  --  Un ciel, un soleil, puis la premiere etoile.

Aucune photo, aucune texture, aucun degrade tout fait. Le ciel entier tient
dans quatre listes de couleurs -- quatre moments de la soiree :

    le jour  ->  l'or  ->  la braise  ->  la nuit

A chaque instant, on fabrique le ciel en melangeant les deux moments qui
entourent l'heure qu'il est. Une interpolation, rien de plus.

Et la mer n'est pas peinte non plus : c'est le ciel, retourne et assombri.

    mer[y] = ciel[2 * horizon - y] * facteur

Une ligne. Le soleil s'y reflete tout seul, et les couleurs du soir aussi,
parce que ce sont litteralement les memes.

    python coucher.py

    ESPACE : recommencer la soiree     ECHAP : quitter
"""

import math
import random
import sys

import numpy as np
import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
FPS = 60
DUREE = 42.0           # secondes, du plein jour a la nuit

HORIZON = 770
SOLEIL_X = int(LARGEUR * 0.44)
SOLEIL_HAUT = 300      # ou se trouve le soleil au debut
SOLEIL_BAS = 980       # et jusqu'ou il descend

PREMIERE_ETOILE = 0.63  # a quelle part de la soiree apparait la premiere
NB_ETOILES = 150

# Les quatre moments. Chaque ligne est une couleur du ciel, du haut de
# l'image jusqu'a l'horizon.
MOMENTS = [
    (0.00, [(38, 74, 132), (92, 132, 178), (176, 180, 178), (238, 206, 152)]),
    (0.45, [(42, 52, 106), (126, 88, 130), (226, 122, 88), (255, 188, 98)]),
    (0.70, [(24, 26, 64), (68, 42, 92), (156, 60, 70), (228, 112, 66)]),
    (1.00, [(6, 8, 22), (10, 14, 34), (22, 24, 52), (46, 38, 64)]),
]


# ------------------------------------------------------------------ le ciel

def moment(part):
    """Les quatre couleurs du ciel a cet instant de la soiree."""
    for i in range(len(MOMENTS) - 1):
        t0, a = MOMENTS[i]
        t1, b = MOMENTS[i + 1]
        if part <= t1 or i == len(MOMENTS) - 2:
            k = 0.0 if t1 == t0 else max(0.0, min((part - t0) / (t1 - t0), 1.0))
            return [tuple(a[j][c] + (b[j][c] - a[j][c]) * k for c in range(3))
                    for j in range(len(a))]
    return MOMENTS[-1][1]


def colonne(part):
    """Une colonne de 1280 couleurs : le ciel en haut, son reflet en bas."""
    arrets = moment(part)
    hauteurs = np.linspace(0, HORIZON, len(arrets))
    y = np.arange(HAUTEUR, dtype=np.float32)

    ciel = np.empty((HAUTEUR, 3), np.float32)
    for c in range(3):
        valeurs = [a[c] for a in arrets]
        ciel[:, c] = np.interp(np.clip(y, 0, HORIZON), hauteurs, valeurs)

    # La mer, c'est le ciel retourne -- et assombri d'autant plus qu'on approche.
    bas = np.arange(HORIZON, HAUTEUR)
    source = np.clip(2 * HORIZON - bas, 0, HORIZON - 1)
    profondeur = (bas - HORIZON) / float(HAUTEUR - HORIZON)
    facteur = (0.62 - 0.34 * profondeur)[:, None]
    ciel[HORIZON:] = ciel[source] * facteur
    return ciel


# --------------------------------------------------------------- le soleil

def halo(rayon):
    """Le soleil et sa lueur.

    Attention au piege : cette image est collee en addition, et une addition
    ignore le canal alpha. La decroissance de la lueur doit donc etre ecrite
    dans la *couleur* -- du gris de plus en plus sombre -- et surtout pas dans
    l'alpha, sinon les quarante cercles s'additionnent et le soleil devient
    un disque blanc plat.
    """
    marge = int(rayon * 4.4)
    s = pygame.Surface((marge * 2, marge * 2), pygame.SRCALPHA)
    centre = (marge, marge)
    s.fill((0, 0, 0, 255))
    for i in range(60, 0, -1):
        k = i / 60.0
        r = int(rayon + (marge - rayon) * k)
        v = int(215 * (1.0 - k) ** 2.9)
        pygame.draw.circle(s, (v, v, v, 255), centre, r)
    pygame.draw.circle(s, (255, 255, 255, 255), centre, rayon)
    return s


def couleur_du_soleil(part):
    """Blanc dore en plein jour, rouge profond quand il touche l'eau."""
    etapes = [(0.00, (255, 246, 214)), (0.32, (255, 214, 140)),
              (0.48, (255, 146, 78)), (0.62, (222, 78, 58))]
    for i in range(len(etapes) - 1):
        t0, a = etapes[i]
        t1, b = etapes[i + 1]
        if part <= t1 or i == len(etapes) - 2:
            k = max(0.0, min((part - t0) / (t1 - t0), 1.0))
            return tuple(int(a[c] + (b[c] - a[c]) * k) for c in range(3))
    return etapes[-1][1]


def scintillement(calque, temps, y_soleil, teinte):
    """Le chemin de lumiere sur l'eau. Des traits, rien de plus."""
    if y_soleil > HORIZON + 160:
        return
    eclat = max(0.0, min(1.0, 1.0 - (y_soleil - HORIZON + 40) / 200.0))
    if eclat <= 0.0:
        return
    for y in range(HORIZON + 2, HAUTEUR, 3):
        profondeur = (y - HORIZON) / float(HAUTEUR - HORIZON)
        alpha = int(165 * eclat * (1.0 - profondeur) ** 1.5)
        if alpha < 5:
            continue
        etalement = 30 + 260 * profondeur
        for brin in range(-2, 3):
            decalage = math.sin(y * 0.37 + temps * 1.9 + brin * 1.7) * etalement * 0.5
            longueur = (12 + 80 * profondeur) * (0.3 + 0.7 *
                        abs(math.sin(y * 0.79 + temps * 2.4 + brin * 2.3)))
            x = SOLEIL_X + decalage
            pygame.draw.line(calque, (*teinte, alpha),
                             (x - longueur / 2, y), (x + longueur / 2, y), 2)


# --------------------------------------------------------------- le reste

def nuages():
    """Un nuage n'est pas une ellipse : c'est huit ellipses qui se chevauchent.

    Chacune est posee avec un alpha faible, si bien que les recouvrements
    epaississent le nuage par endroits. C'est ce hasard d'empilement qui lui
    donne l'air d'un nuage plutot que d'un ovale.
    """
    alea = random.Random(11)
    bancs = []
    for _ in range(6):
        cx = alea.randint(-70, LARGEUR + 70)
        cy = alea.randint(380, HORIZON - 60)
        large = alea.randint(250, 520)
        epais = alea.randint(16, 30)
        bouts = []
        for _ in range(alea.randint(7, 11)):
            bl = alea.randint(large // 4, large // 2)
            bh = alea.randint(int(epais * 0.6), int(epais * 1.6))
            bx = cx + alea.randint(-large // 2, large // 2) - bl // 2
            by = cy + alea.randint(-epais // 2, epais // 2) - bh // 2
            bouts.append(pygame.Rect(bx, by, bl, bh))
        bancs.append((cy, alea.randint(52, 84), bouts))
    return bancs


def etoiles():
    """La toute premiere est seule, haute, et plus vive que les autres.
    Les suivantes attendent leur tour."""
    alea = random.Random(7)
    liste = [(int(LARGEUR * 0.68), 176, 0.0, 1.0, 0.0)]
    for _ in range(NB_ETOILES - 1):
        liste.append((alea.randint(0, LARGEUR), alea.randint(0, HORIZON - 90),
                      alea.uniform(0.16, 0.95), alea.uniform(0.40, 0.95),
                      alea.uniform(0, math.tau)))
    return liste


# ------------------------------------------------------------------- le film

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
    fenetre = ouvrir("un coucher de soleil")
    toile = pygame.Surface((LARGEUR, HAUTEUR))
    horloge = pygame.time.Clock()

    bande = pygame.Surface((1, HAUTEUR))
    calque = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
    disque = halo(46)
    colore = disque.copy()
    mes_nuages = nuages()
    mes_etoiles = etoiles()
    etat = {"t": 0.0}

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    etat["t"] = 0.0

        etat["t"] += min(horloge.tick(FPS) / 1000.0, 1 / 20)
        part = min(etat["t"] / DUREE, 1.0)

        # Le ciel : une colonne de pixels, etiree sur toute la largeur.
        couleurs = colonne(part)
        pygame.surfarray.blit_array(bande, np.clip(couleurs, 0, 255)
                                    .astype(np.uint8)[None, :, :])
        pygame.transform.scale(bande, (LARGEUR, HAUTEUR), toile)

        # Le soleil, qui descend et rougit. La mer le coupe net.
        y_soleil = SOLEIL_HAUT + (SOLEIL_BAS - SOLEIL_HAUT) * part / 0.62
        teinte = couleur_du_soleil(part)
        if y_soleil < HORIZON + disque.get_height() / 2:
            colore.blit(disque, (0, 0))
            colore.fill((*teinte, 255), special_flags=pygame.BLEND_RGBA_MULT)
            toile.set_clip(pygame.Rect(0, 0, LARGEUR, HORIZON))
            toile.blit(colore, (SOLEIL_X - colore.get_width() // 2,
                                int(y_soleil) - colore.get_height() // 2),
                       special_flags=pygame.BLEND_RGB_ADD)
            toile.set_clip(None)

        calque.fill((0, 0, 0, 0))
        scintillement(calque, etat["t"], y_soleil, teinte)

        # Les nuages passent devant le soleil : c'est ce qui les allume.
        for y, alpha, bouts in mes_nuages:
            base = couleurs[min(y, HAUTEUR - 1)]
            sombre = tuple(int(min(255, base[c] * 0.52 + teinte[c] * 0.14)) for c in range(3))
            for rect in bouts:
                pygame.draw.ellipse(calque, (*sombre, alpha), rect)
        toile.blit(calque, (0, 0))

        # Et la premiere etoile.
        if part > PREMIERE_ETOILE:
            for x, y, retard, force, phase in mes_etoiles:
                venue = (part - PREMIERE_ETOILE) / (1.0 - PREMIERE_ETOILE) - retard
                if venue <= 0:
                    continue
                vif = min(venue * 2.2, 1.0) * force
                vif *= 0.72 + 0.28 * math.sin(etat["t"] * 2.4 + phase)
                c = int(225 * vif)
                if c > 6:
                    # En addition, jamais en remplacement : une etoile ajoute
                    # de la lumiere. Peinte par-dessus, une etoile encore pale
                    # serait plus sombre que le ciel -- un point noir.
                    toile.fill((c, c, min(255, c + 16)), (x, y, 2, 2),
                               special_flags=pygame.BLEND_RGB_ADD)

        pygame.transform.smoothscale(toile, fenetre.get_size(), fenetre)
        pygame.display.flip()


if __name__ == "__main__":
    sys.exit(main())
