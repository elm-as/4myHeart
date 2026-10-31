# -*- coding: utf-8 -*-
"""
pluie.py  --  Une goutte. Puis la pluie.

Il n'y a pas d'image dans ce programme. Il y a un lac, vu de biais,
et une seule idee : un point du lac se trouve a une distance Z,
et plus Z est grand, plus ce point est petit et proche de l'horizon.

    echelle = F / Z

Tout le reste en decoule. Un rond dans l'eau, c'est un cercle -- mais
vu de biais, un cercle est une ellipse, d'autant plus ecrasee qu'elle
est loin. Cet ecrasement vaut exactement H / Z. Une ligne de code.

C'est pour ca que les ronds du fond ressemblent a des traits, et ceux
du bord a des cercles. Personne ne l'a dessine : c'est la geometrie.

    python pluie.py

    ESPACE : recommencer     ECHAP : quitter
"""

import math
import random
import sys

import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
FPS = 60

HORIZON = 420          # la ligne ou le lac rencontre le ciel
F = 900.0              # la focale : plus c'est grand, plus on est serre
H = 6.0                # la hauteur de la camera au-dessus de l'eau
PROCHE, LOIN = 9.0, 78.0

CHUTE = 18.0           # vitesse de chute d'une goutte
POUSSE_RIDE = 2.6      # vitesse a laquelle un rond s'agrandit
VIE_RIDE = 2.8         # secondes avant qu'un rond ait disparu

PREMIERE = 1.2         # a quelle seconde tombe LA goutte
SILENCE = 4.5          # puis on ne respire plus, jusqu'a cette seconde
MONTEE = 13.0          # et l'averse met ce temps a s'installer
AVERSE = 340.0         # gouttes par seconde, au maximum

CIEL_HAUT = (7, 9, 16)
CIEL_BAS = (26, 34, 48)
EAU_LOIN = (20, 27, 38)
EAU_PRES = (9, 12, 18)
LUEUR = (168, 196, 220)


# ------------------------------------------------------- voir en perspective

def projeter(x, z, y=0.0):
    """Un point du monde (x de cote, z en profondeur, y en hauteur) -> l'ecran."""
    echelle = F / z
    return (LARGEUR / 2 + x * echelle, HORIZON + (H - y) * echelle, echelle)


# ----------------------------------------------------------------- la scene

class Goutte:
    __slots__ = ("x", "z", "y")

    def __init__(self, x, z, y):
        self.x, self.z, self.y = x, z, y


class Ride:
    __slots__ = ("x", "z", "age")

    def __init__(self, x, z):
        self.x, self.z, self.age = x, z, 0.0


def tirer_une_goutte():
    """Une goutte au hasard -- mais au hasard sur le lac, pas au hasard a l'ecran.

    Une bande lointaine du lac est immense et n'occupe que trois pixels ; une
    bande proche est minuscule et remplit le bas de l'image. Si on tirait la
    profondeur uniformement, toute la pluie tomberait sur nos pieds. Il faut
    donc tirer proportionnellement a la surface, ce qui donne ce sqrt.
    """
    z = math.sqrt(PROCHE ** 2 + random.random() * (LOIN ** 2 - PROCHE ** 2))
    bord = 0.575 * LARGEUR * z / F          # a cette distance, l'ecran va de -bord a +bord
    return Goutte(random.uniform(-bord, bord), z, random.uniform(18, 46))


def intensite(t):
    """Combien de gouttes par seconde a l'instant t."""
    if t < SILENCE:
        return 0.0
    return AVERSE * min((t - SILENCE) / MONTEE, 1.0) ** 2.2


def fond():
    surface = pygame.Surface((LARGEUR, HAUTEUR))
    for y in range(HORIZON):
        k = y / HORIZON
        surface.fill(tuple(int(CIEL_HAUT[i] + (CIEL_BAS[i] - CIEL_HAUT[i]) * k)
                           for i in range(3)), (0, y, LARGEUR, 1))
    for y in range(HORIZON, HAUTEUR):
        k = (y - HORIZON) / (HAUTEUR - HORIZON)
        surface.fill(tuple(int(EAU_LOIN[i] + (EAU_PRES[i] - EAU_LOIN[i]) * k ** 0.6)
                           for i in range(3)), (0, y, LARGEUR, 1))
    return surface


# ----------------------------------------------------------------- le dessin

def dessiner_rides(calque, rides):
    # Les plus lointaines d'abord : les proches passent par-dessus.
    for ride in sorted(rides, key=lambda r: -r.z):
        reste = 1.0 - ride.age / VIE_RIDE
        if reste <= 0.0:
            continue
        cx, cy, echelle = projeter(ride.x, ride.z)

        for rayon, part in ((ride.age * POUSSE_RIDE, 1.0),
                            ((ride.age - 0.22) * POUSSE_RIDE, 0.45)):
            if rayon <= 0.0:
                continue
            rx = rayon * echelle
            ry = rx * H / ride.z          # l'ecrasement du a la perspective
            if rx < 1.0 or ry < 0.4:
                continue
            alpha = int(225 * reste ** 2.5 * part)
            if alpha < 4:
                continue
            pygame.draw.ellipse(
                calque, (*LUEUR, alpha),
                pygame.Rect(cx - rx, cy - ry, 2 * rx, 2 * ry),
                1 if rx < 40 else 2,
            )


def dessiner_gouttes(calque, gouttes):
    for g in gouttes:
        x, y, echelle = projeter(g.x, g.z, g.y)
        if not (-40 < x < LARGEUR + 40):
            continue
        longueur = min(58.0, max(2.5, 0.95 * echelle))
        alpha = int(min(210, 42 + echelle * 2.2))
        pygame.draw.line(calque, (*LUEUR, alpha), (x, y), (x, y - longueur),
                         1 if echelle < 55 else 2)


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
    fenetre = ouvrir("une goutte")
    toile = pygame.Surface((LARGEUR, HAUTEUR))
    horloge = pygame.time.Clock()

    decor = fond()
    calque = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)

    etat = {"t": 0.0, "reste": 0.0, "premiere": False}
    gouttes, rides = [], []

    def recommencer():
        etat.update(t=0.0, reste=0.0, premiere=False)
        gouttes.clear()
        rides.clear()

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    recommencer()

        dt = min(horloge.tick(FPS) / 1000.0, 1 / 20)
        etat["t"] += dt
        t = etat["t"]

        # LA goutte. Une seule, au milieu, bien visible.
        if not etat["premiere"] and t >= PREMIERE:
            etat["premiere"] = True
            gouttes.append(Goutte(0.0, 15.0, 22.0))

        # Puis l'averse, qui monte.
        etat["reste"] += intensite(t) * dt
        for _ in range(int(etat["reste"])):
            gouttes.append(tirer_une_goutte())
        etat["reste"] -= int(etat["reste"])

        # Les gouttes tombent ; celles qui touchent l'eau deviennent des ronds.
        encore = []
        for g in gouttes:
            g.y -= CHUTE * dt
            if g.y <= 0.0:
                rides.append(Ride(g.x, g.z))
            else:
                encore.append(g)
        gouttes = encore

        for r in rides:
            r.age += dt
        rides = [r for r in rides if r.age < VIE_RIDE]

        toile.blit(decor, (0, 0))
        calque.fill((0, 0, 0, 0))
        dessiner_rides(calque, rides)
        dessiner_gouttes(calque, gouttes)
        toile.blit(calque, (0, 0))
        pygame.transform.smoothscale(toile, fenetre.get_size(), fenetre)
        pygame.display.flip()


if __name__ == "__main__":
    sys.exit(main())
