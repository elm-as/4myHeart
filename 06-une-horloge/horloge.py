# -*- coding: utf-8 -*-
"""
horloge.py  --  Une horloge, sans une seule image.

Il n'y a pas de fichier .png dans ce dossier. Pas de dessin, pas de police
d'icones, rien. Il y a un cercle, soixante traits, trois aiguilles -- et
une seule formule, celle qui transforme un instant en un angle :

    angle = 2*pi * (ce qui est passe / ce qui fait un tour)

Puis, pour poser un point sur le cercle a cet angle :

    x = centre + sin(angle) * rayon
    y = centre - cos(angle) * rayon

Le sinus et le cosinus sont inverses par rapport a l'habitude, et le y est
soustrait. Les deux pour la meme raison : on veut que zero soit en haut et
que ca tourne dans le sens des aiguilles. Ce qui, ici, tombe bien.

Au demarrage, l'horloge se dessine elle-meme.

    python horloge.py

    ESPACE : refaire le dessin     ECHAP : quitter
"""

import math
import sys
import time

import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
SS = 1.5               # on dessine plus grand, on reduit : des bords lisses
FPS = 60

GRANDE = (int(LARGEUR * SS), int(HAUTEUR * SS))
CENTRE = (LARGEUR // 2, 620)
RAYON = 268

TRACE_CERCLE = 1.4     # secondes : le cercle se dessine
TRACE_TRAITS = 1.7     # puis les soixante traits apparaissent
TRACE_MAINS = 0.9      # puis les aiguilles se mettent en place

FOND = (11, 12, 17)
CERCLE = (58, 60, 74)
TRAIT = (120, 122, 140)
TRAIT_FORT = (216, 214, 222)
AIGUILLE = (232, 228, 224)
SECONDE = (214, 122, 104)
CHIFFRES = (128, 126, 140)


def ep(n):
    """Une epaisseur, mise a l'echelle du grand dessin -- et entiere."""
    return max(1, int(round(n * SS)))


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


# ------------------------------------------------- un instant devient un angle

def sur_le_cercle(centre, rayon, tour):
    """`tour` va de 0 a 1. 0 est en haut, et ca tourne dans le bon sens."""
    angle = math.tau * tour
    return (centre[0] + math.sin(angle) * rayon,
            centre[1] - math.cos(angle) * rayon)


def maintenant():
    """L'heure, en trois fractions de tour. La seconde est fluide, pas saccadee."""
    t = time.localtime()
    frac = time.time() % 1.0
    secondes = t.tm_sec + frac
    minutes = t.tm_min + secondes / 60.0
    heures = (t.tm_hour % 12) + minutes / 60.0
    return heures / 12.0, minutes / 60.0, secondes / 60.0, t


# ------------------------------------------------------------------ le dessin

def adoucir(k):
    k = max(0.0, min(k, 1.0))
    return k * k * (3 - 2 * k)


def dessiner_cercle(surface, centre, part):
    """Le cercle se trace, d'un trait, en partant du haut."""
    if part <= 0.0:
        return
    pas = max(2, int(240 * part))
    points = [sur_le_cercle(centre, RAYON * SS, part * i / pas) for i in range(pas + 1)]
    if len(points) > 1:
        pygame.draw.lines(surface, CERCLE, False, points, ep(2))


def dessiner_traits(surface, centre, part):
    sortis = int(60 * part)
    for i in range(sortis):
        fort = (i % 5 == 0)
        dedans = RAYON - (26 if fort else 13)
        a = sur_le_cercle(centre, dedans * SS, i / 60.0)
        b = sur_le_cercle(centre, (RAYON - 3) * SS, i / 60.0)
        pygame.draw.line(surface, TRAIT_FORT if fort else TRAIT, a, b,
                         ep(3) if fort else ep(1))


def dessiner_aiguille(surface, centre, tour, longueur, epaisseur, couleur, queue=0):
    bout = sur_le_cercle(centre, longueur * SS, tour)
    pied = sur_le_cercle(centre, -queue * SS, tour)
    pygame.draw.line(surface, couleur, pied, bout, ep(epaisseur))


def dessiner_arc_seconde(surface, centre, tour):
    """Un fil clair sur le pourtour : la part de la minute deja ecoulee."""
    if tour <= 0.002:
        return
    pas = max(2, int(180 * tour))
    points = [sur_le_cercle(centre, (RAYON + 12) * SS, tour * i / pas)
              for i in range(pas + 1)]
    pygame.draw.lines(surface, SECONDE, False, points, ep(2))


# -------------------------------------------------------------------- le film

def main():
    fenetre = ouvrir("une horloge")
    horloge = pygame.time.Clock()

    grande = pygame.Surface(GRANDE)
    centre = (int(CENTRE[0] * SS), int(CENTRE[1] * SS))

    chemin = pygame.font.match_font("consolas") or pygame.font.match_font("segoeui")
    police = pygame.font.Font(chemin, ep(44))

    debut = time.perf_counter()

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    debut = time.perf_counter()

        age = time.perf_counter() - debut
        h, m, s, brut = maintenant()

        grande.fill(FOND)
        dessiner_cercle(grande, centre, adoucir(age / TRACE_CERCLE))

        apres_cercle = age - TRACE_CERCLE
        if apres_cercle > 0:
            dessiner_traits(grande, centre, adoucir(apres_cercle / TRACE_TRAITS))

        apres_traits = apres_cercle - TRACE_TRAITS
        if apres_traits > 0:
            # Les aiguilles ne surgissent pas : elles partent de midi et vont
            # a leur place, en tournant, comme si on remontait l'horloge.
            k = adoucir(apres_traits / TRACE_MAINS)
            dessiner_aiguille(grande, centre, h * k, 150, 7, AIGUILLE, queue=24)
            dessiner_aiguille(grande, centre, m * k, 222, 4, AIGUILLE, queue=34)
            if k >= 1.0:
                dessiner_arc_seconde(grande, centre, s)
                dessiner_aiguille(grande, centre, s, 238, 2, SECONDE, queue=54)
                pygame.draw.circle(grande, SECONDE, centre, ep(5))
            pygame.draw.circle(grande, AIGUILLE, centre, ep(9))
            pygame.draw.circle(grande, FOND, centre, ep(4))

        # L'heure est ecrite dans le grand dessin, pas par-dessus la fenetre :
        # une seule reduction, et le texte est lisse comme le reste.
        if apres_traits > TRACE_MAINS:
            img = police.render(time.strftime("%H:%M:%S", brut), True, CHIFFRES)
            grande.blit(img, (GRANDE[0] // 2 - img.get_width() // 2, int(1010 * SS)))

        pygame.transform.smoothscale(grande, fenetre.get_size(), fenetre)
        pygame.display.flip()
        horloge.tick(FPS)


if __name__ == "__main__":
    sys.exit(main())
