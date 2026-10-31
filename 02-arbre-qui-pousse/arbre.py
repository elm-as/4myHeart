"""
arbre.py  --  Une graine, puis un arbre.

L'idee tient en une phrase :
    une branche, c'est un trait  --  puis deux branches plus petites au bout.
    Et on recommence. Dix fois.

C'est tout. Il n'y a pas d'arbre dans ce code : il y a juste une regle
qui se repete. L'arbre, c'est ce que la regle devient.

    python arbre.py

    ESPACE : replanter (nouvel arbre)     ECHAP : quitter
"""

import math
import random
import sys

import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280          # format vertical (Shorts / Reels / TikTok)
SS = 1.5                              # on dessine plus grand, on reduit : bords lisses
PROFONDEUR = 10                       # nombre de fois ou la regle se repete
DUREE_POUSSE = 11.0                   # secondes pour que l'arbre pousse
DUREE_GENERATION = 0.17               # part du temps que met une generation a sortir
FPS = 60

CIEL_HAUT = (14, 16, 26)
CIEL_BAS = (34, 28, 34)
BOIS_JEUNE = (150, 126, 112)
BOIS_VIEUX = (74, 58, 52)
FEUILLES = [(240, 196, 200), (232, 172, 186), (250, 222, 208), (214, 168, 178)]

GRANDE = (int(LARGEUR * SS), int(HAUTEUR * SS))
RAYON_FEUILLE = max(1, int(3.4 * SS))


def melange(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


# Calcule une fois pour toutes : couleur, epaisseur, vent et horaire de chaque generation.
COULEUR = [melange(BOIS_VIEUX, BOIS_JEUNE, d / PROFONDEUR) for d in range(PROFONDEUR + 1)]
EPAISSEUR = [max(1, int((1 - d / PROFONDEUR) ** 2 * 13 * SS + 1)) for d in range(PROFONDEUR + 1)]
DEBUT = [(d / PROFONDEUR) * (1 - DUREE_GENERATION) for d in range(PROFONDEUR + 1)]
VENT = [0.030 * (d / PROFONDEUR) ** 1.6 for d in range(PROFONDEUR + 1)]

# Une feuille est toujours la meme petite image : on la dessine une fois, a chaque
# taille d'eclosion, puis on ne fait plus que la coller. C'est ce qui permet d'en
# afficher deux mille sans que l'animation ralentisse.
SPRITES = []
for _teinte in FEUILLES:
    _tailles = []
    for _r in range(RAYON_FEUILLE + 1):
        _s = pygame.Surface((4 * _r + 2, 4 * _r + 2), pygame.SRCALPHA)
        _c = (2 * _r + 1, 2 * _r + 1)
        if _r:
            pygame.draw.circle(_s, (_teinte[0], _teinte[1], _teinte[2], 30), _c, 2 * _r)
            pygame.draw.circle(_s, (_teinte[0], _teinte[1], _teinte[2], 210), _c, _r)
        _tailles.append(_s)
    SPRITES.append(_tailles)


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


# ------------------------------------------------------- la regle, une fois

class Branche:
    """Une branche : un angle, une longueur, et ses enfants."""

    __slots__ = ("angle", "longueur", "profondeur", "phase", "teinte", "enfants")

    def __init__(self, angle, longueur, profondeur, alea):
        self.angle = angle              # inclinaison par rapport a sa mere
        self.longueur = longueur
        self.profondeur = profondeur
        self.phase = alea.uniform(0, math.tau)   # pour que le vent la prenne a son heure
        self.teinte = alea.randrange(len(FEUILLES))
        self.enfants = []

        if profondeur < PROFONDEUR:
            nb = 2 if alea.random() > 0.13 else 3       # parfois, une branche en plus
            for i in range(nb):
                ecart = alea.uniform(0.32, 0.62)
                sens = -1 if i % 2 == 0 else 1
                if nb == 3 and i == 2:
                    sens, ecart = 0, 0.0
                self.enfants.append(
                    Branche(
                        angle=sens * ecart + alea.uniform(-0.10, 0.10),
                        longueur=longueur * alea.uniform(0.70, 0.82),
                        profondeur=profondeur + 1,
                        alea=alea,
                    )
                )


def planter(graine):
    alea = random.Random(graine)
    return Branche(angle=alea.uniform(-0.05, 0.05), longueur=175 * SS, profondeur=0, alea=alea)


# ------------------------------------------------------------- le dessin

def dessiner(bois, branche, x, y, angle_mere, pousse, temps, eclosion):
    """Dessine une branche si son tour est venu, puis ses enfants."""

    d = branche.profondeur
    avance = (pousse - DEBUT[d]) / DUREE_GENERATION
    if avance <= 0.0:
        return
    if avance < 1.0:
        avance = avance * avance * (3 - 2 * avance)      # demarre et finit en douceur
        fini = False
    else:
        avance = 1.0
        fini = True

    # Le vent : plus la branche est fine, plus elle bouge.
    phase = branche.phase
    souffle = math.sin(temps * 0.85 + phase) * 0.7 + math.sin(temps * 0.31 + phase * 2) * 0.3
    angle = angle_mere + branche.angle + souffle * VENT[d]

    longueur = branche.longueur * avance
    x2 = x + math.sin(angle) * longueur
    y2 = y - math.cos(angle) * longueur

    couleur, ep = COULEUR[d], EPAISSEUR[d]
    pygame.draw.line(bois, couleur, (x, y), (x2, y2), ep)
    if ep > 3:
        pygame.draw.circle(bois, couleur, (int(x2), int(y2)), ep // 2)

    if not fini:
        return

    for enfant in branche.enfants:
        dessiner(bois, enfant, x2, y2, angle, pousse, temps, eclosion)

    # Au bout des plus petites branches : une feuille.
    if d == PROFONDEUR and eclosion > 0.0:
        sprite = SPRITES[branche.teinte][int(eclosion * RAYON_FEUILLE)]
        moitie = sprite.get_width() // 2
        bois.blit(sprite, (int(x2) - moitie, int(y2) - moitie))


def fond(surface):
    h, w = surface.get_height(), surface.get_width()
    for i in range(h):
        surface.fill(melange(CIEL_HAUT, CIEL_BAS, i / h), (0, i, w, 1))


# ---------------------------------------------------------------- le film

def main():
    fenetre = ouvrir("une graine")
    horloge = pygame.time.Clock()

    bois = pygame.Surface(GRANDE)
    ciel = pygame.Surface(GRANDE)
    fond(ciel)

    arbre = planter(random.randrange(10_000))
    temps = 0.0
    sol = GRANDE[1] - int(80 * SS)

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    arbre = planter(random.randrange(10_000))
                    temps = 0.0

        pousse = min(temps / DUREE_POUSSE, 1.0)
        eclosion = max(0.0, min((temps - DUREE_POUSSE * 0.80) / 3.0, 1.0))
        eclosion = eclosion * eclosion * (3 - 2 * eclosion)

        bois.blit(ciel, (0, 0))
        dessiner(bois, arbre, GRANDE[0] / 2, sol, 0.0, pousse, temps, eclosion)

        pygame.transform.smoothscale(bois, fenetre.get_size(), fenetre)
        pygame.display.flip()

        temps += horloge.tick(FPS) / 1000.0


if __name__ == "__main__":
    sys.exit(main())
