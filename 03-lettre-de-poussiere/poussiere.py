# -*- coding: utf-8 -*-
"""
poussiere.py  --  Des mots ecrits avec de la poussiere.

Le principe, en trois temps :

    1. On ecrit une phrase, une seule fois, dans une image invisible.
    2. On note ou sont les pixels allumes : ce sont des destinations.
    3. On lache douze mille grains de poussiere, et on leur dit
       simplement "va vers ta destination". Ils s'en chargent.

Puis on leur retire la destination, un par un, jamais tous ensemble --
et la phrase s'erode, puis s'envole.

Aucun grain ne sait qu'il ecrit une lettre. Il ne connait qu'un point.

    python poussiere.py

    ESPACE : phrase suivante     ECHAP : quitter
"""

import math
import sys

import numpy as np
import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
NB_GRAINS = 12000
FPS = 60

# Chaque entree est une phrase. Un saut de ligne = une ligne a l'ecran.
# C'est ici, et nulle part ailleurs, que tu ecris ce que tu as a dire.
PHRASES = [
    "il y a des choses\nqu'on ne sait dire\nqu'en les codant",
    "chaque grain\nne connait\nqu'un seul point",
    "et pourtant,\nensemble,\nils ecrivent",
    "merci",
]

VOL = 3.2          # secondes : les grains rejoignent la phrase
REPOS = 3.0        # secondes : la phrase tient
CHUTE = 3.4        # secondes : elle s'erode et s'envole

TEINTES = [(255, 236, 220), (255, 214, 210), (240, 224, 240), (255, 246, 232)]
TRAINEE = 0.84     # 0 = net, 0.95 = longues trainees de lumiere

RAPPEL = 31.0      # force du ressort qui tire le grain vers sa lettre
FREIN = 12.0       # ce qui l'empeche de depasser sa lettre
MONTEE = -34.0     # une fois detache, le grain s'eleve
TOURNOIE = 26.0    # et il tournoie en s'elevant
EXTINCTION = 0.5   # part de CHUTE que met un grain detache a s'eteindre


# --------------------------------------------------- ecrire, puis oublier

def choisir_police(taille):
    for nom in ("georgia", "constantia", "cambria", "palatinolinotype", "segoeui"):
        chemin = pygame.font.match_font(nom)
        if chemin:
            return pygame.font.Font(chemin, taille)
    return pygame.font.Font(None, taille)


def destinations(phrase, nb):
    """Rend nb points (x, y) pris au hasard dans les lettres de la phrase."""
    lignes = phrase.split("\n")
    taille = 78 if max(len(l) for l in lignes) < 22 else 56
    police = choisir_police(taille)
    interligne = int(taille * 1.42)

    rendus = [police.render(l, True, (255, 255, 255)) for l in lignes]
    hauteur = interligne * len(rendus)
    page = pygame.Surface((LARGEUR, HAUTEUR))
    for i, img in enumerate(rendus):
        page.blit(img, (LARGEUR // 2 - img.get_width() // 2,
                        HAUTEUR // 2 - hauteur // 2 + i * interligne))

    allumes = np.argwhere(pygame.surfarray.array2d(page) != 0)   # coordonnees (x, y)
    if len(allumes) == 0:
        return np.zeros((nb, 2), np.float32)

    points = allumes[np.random.randint(0, len(allumes), nb)].astype(np.float32)
    points += np.random.uniform(-0.6, 0.6, points.shape)         # casse la grille
    return points


# ------------------------------------------------------------ les grains

class Poussiere:
    def __init__(self):
        self.pos = np.column_stack((
            np.random.uniform(-160, LARGEUR + 160, NB_GRAINS),
            np.random.uniform(-160, HAUTEUR + 160, NB_GRAINS),
        )).astype(np.float32)
        self.vit = np.zeros((NB_GRAINS, 2), np.float32)
        self.cible = self.pos.copy()
        self.eclat = np.random.uniform(0.55, 1.0, NB_GRAINS).astype(np.float32)
        self.teinte = np.array(TEINTES, np.float32)[
            np.random.randint(0, len(TEINTES), NB_GRAINS)]
        self.phase = np.random.uniform(0, math.tau, (NB_GRAINS, 2)).astype(np.float32)
        self.tirer_au_sort()

    def tirer_au_sort(self):
        # Tous les grains ne partent pas en meme temps : c'est ce retard,
        # tout petit, qui donne l'impression que la phrase s'ecrit.
        self.retard = np.random.uniform(0.0, 1.9, NB_GRAINS).astype(np.float32)
        # Et ils ne se detachent pas en meme temps non plus : c'est ce qui fait
        # que la phrase s'erode au lieu d'exploser.
        self.envol = np.random.uniform(0.0, 0.45, NB_GRAINS).astype(np.float32)
        self.force = np.random.uniform(0.5, 1.7, NB_GRAINS).astype(np.float32)

    def viser(self, points):
        self.cible = points
        self.tirer_au_sort()

    def avancer(self, dt, t, erosion):
        """erosion vaut None tant que la phrase tient, puis va de 0 a 1.

        Rend l'eclat de chaque grain a cet instant.
        """
        if erosion is None:
            parti = (t > self.retard)[:, None]
            ecart = self.cible - self.pos
            self.vit += (ecart * RAPPEL - self.vit * FREIN) * dt * parti
            self.pos += self.vit * dt
            self.pos += np.sin(t * 1.5 + self.phase) * (0.20 * parti)   # ils respirent
            return np.ones(NB_GRAINS, np.float32)

        detache = (erosion > self.envol)[:, None]

        # Ceux qui tiennent encore restent accroches a leur lettre.
        ecart = self.cible - self.pos
        self.vit += (ecart * RAPPEL - self.vit * FREIN) * dt * ~detache

        # Ceux qui sont partis s'elevent, en tournoyant.
        courant = np.empty((NB_GRAINS, 2), np.float32)
        courant[:, 0] = np.cos(self.phase[:, 0] + t * 0.6) * TOURNOIE
        courant[:, 1] = np.sin(self.phase[:, 1] + t * 0.5) * (TOURNOIE * 0.6) + MONTEE
        self.vit += courant * self.force[:, None] * dt * detache

        self.vit *= 0.62 ** dt                   # l'air freine, tout doucement
        self.pos += self.vit * dt

        eclat = 1.0 - (erosion - self.envol) / EXTINCTION
        return np.clip(eclat, 0.0, 1.0).astype(np.float32)


# ------------------------------------------------------------- le dessin

def peindre(champ, grains, eclat, dt):
    champ *= TRAINEE ** (dt * FPS)

    x = grains.pos[:, 0].astype(np.int32)
    y = grains.pos[:, 1].astype(np.int32)
    dedans = (x >= 1) & (x < LARGEUR - 1) & (y >= 1) & (y < HAUTEUR - 1)
    x, y = x[dedans], y[dedans]
    couleur = grains.teinte[dedans] * (grains.eclat[dedans] * eclat[dedans])[:, None]

    champ[x, y] += couleur                       # le coeur du grain
    halo = couleur * 0.38                        # et un soupcon autour
    champ[x + 1, y] += halo
    champ[x - 1, y] += halo
    champ[x, y + 1] += halo
    champ[x, y - 1] += halo


# ---------------------------------------------------------------- le film

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
    fenetre = ouvrir("poussiere")
    toile = pygame.Surface((LARGEUR, HAUTEUR))
    horloge = pygame.time.Clock()

    champ = np.zeros((LARGEUR, HAUTEUR, 3), np.float32)
    tampon = np.zeros((LARGEUR, HAUTEUR, 3), np.uint8)   # reutilise : rien a reallouer
    grains = Poussiere()

    etat = {"numero": 0, "t": 0.0}
    grains.viser(destinations(PHRASES[0], NB_GRAINS))

    def suivante():
        etat["numero"] = (etat["numero"] + 1) % len(PHRASES)
        grains.viser(destinations(PHRASES[etat["numero"]], NB_GRAINS))
        etat["t"] = 0.0

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    suivante()

        dt = min(horloge.tick(FPS) / 1000.0, 1 / 20)   # si l'ordi hoquette, on ne saute pas
        etat["t"] += dt
        t = etat["t"]

        erosion = None if t < VOL + REPOS else (t - VOL - REPOS) / CHUTE
        eclat = grains.avancer(dt, t, erosion)

        peindre(champ, grains, eclat, dt)
        np.clip(champ, 0, 255, out=champ)
        np.copyto(tampon, champ, casting="unsafe")
        pygame.surfarray.blit_array(toile, tampon)
        pygame.transform.smoothscale(toile, fenetre.get_size(), fenetre)
        pygame.display.flip()

        if erosion is not None and erosion > 1.0:
            suivante()


if __name__ == "__main__":
    sys.exit(main())
