# -*- coding: utf-8 -*-
"""
banc.py  --  Cinq cents poissons, et personne aux commandes.

Il n'y a pas de chef dans ce programme. Pas de trajectoire ecrite, pas de
forme prevue. Chaque poisson ne connait que ses voisins immediats, et ne
suit que trois regles :

    1. ne pas coller ses voisins
    2. aller dans le meme sens qu'eux
    3. ne pas trop s'en eloigner

Le banc n'est ecrit nulle part. Il apparait.

La video montre les trois regles s'allumer une par une : d'abord le
desordre, puis une nuee reguliere, puis des courants, puis -- d'un coup --
un animal. Regarder la troisieme regle s'allumer est tout l'interet.

    python banc.py

    ESPACE : recommencer     P : lacher le predateur     ECHAP : quitter
"""

import math
import sys

import numpy as np
import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
FPS = 60
NB = 500

# Jusqu'ou chaque poisson regarde. Ces trois rayons comptent autant que les
# trois forces : si personne ne voit assez loin, il ne se forme jamais UN banc,
# seulement un essaim qui remplit l'aquarium.
R_SEPARATION = 30.0
R_ALIGNEMENT = 95.0
R_COHESION = 185.0

# L'equilibre entre ces trois nombres est tout le sujet. Trop de cohesion et
# le banc s'effondre en boules compactes ; trop de separation et il se disperse.
P_SEPARATION = 1500.0
P_ALIGNEMENT = 5.0
P_COHESION = 0.90
P_FUITE = 900.0
ACCEL_MAX = 1400.0      # un plafond, pour que rien ne parte jamais en vrille

VITESSE_MIN, VITESSE_MAX = 70.0, 165.0
MARGE = 90.0            # a quelle distance du bord on se fait repousser
P_BORD = 260.0

R_PREDATEUR = 150.0
PREDATEUR_A = 34.0      # a quelle seconde il arrive, si on ne fait rien

# Quand chaque regle s'allume, et ce qu'on ecrit a l'ecran.
ETAPES = [
    (0.0, "aucune regle"),
    (7.0, "1.  ne pas coller ses voisins"),
    (14.0, "2.  aller dans le meme sens qu'eux"),
    (21.0, "3.  ne pas trop s'en eloigner"),
]

EAU_HAUT = (14, 40, 58)
EAU_BAS = (5, 13, 24)
POISSON = (196, 232, 238)
PREDATEUR = (212, 92, 78)
TEXTE = (150, 178, 188)


# ------------------------------------------------------------------ le banc

class Banc:
    def __init__(self):
        self.pos = np.column_stack((
            np.random.uniform(60, LARGEUR - 60, NB),
            np.random.uniform(60, HAUTEUR - 60, NB),
        )).astype(np.float32)
        angle = np.random.uniform(0, math.tau, NB)
        vite = np.random.uniform(VITESSE_MIN, VITESSE_MAX, NB)
        self.vit = np.column_stack((np.cos(angle) * vite,
                                    np.sin(angle) * vite)).astype(np.float32)

    def avancer(self, dt, regles, predateur):
        """`regles` vaut 0, 1, 2 ou 3 : le nombre de regles allumees."""
        pos, vit = self.pos, self.vit
        accel = np.zeros_like(vit)

        if regles > 0:
            # Le carre des distances entre tous les couples, sans jamais
            # construire le tableau des differences : |a-b|^2 = |a|^2 + |b|^2 - 2a.b
            carres = (pos * pos).sum(1)
            dist2 = carres[:, None] + carres[None, :] - 2.0 * (pos @ pos.T)
            np.fill_diagonal(dist2, 1e9)

            # 1. Se separer. La poussee est d'autant plus forte qu'on est pres.
            poids = np.where(dist2 < R_SEPARATION ** 2, 1.0 / np.maximum(dist2, 9.0), 0.0)
            accel += P_SEPARATION * (pos * poids.sum(1)[:, None] - poids @ pos)

            if regles > 1:
                # 2. S'aligner sur la vitesse moyenne des voisins.
                proches = (dist2 < R_ALIGNEMENT ** 2).astype(np.float32)
                combien = np.maximum(proches.sum(1), 1.0)[:, None]
                accel += P_ALIGNEMENT * ((proches @ vit) / combien - vit)

            if regles > 2:
                # 3. Revenir vers le centre de ses voisins.
                autour = (dist2 < R_COHESION ** 2).astype(np.float32)
                combien = np.maximum(autour.sum(1), 1.0)[:, None]
                accel += P_COHESION * ((autour @ pos) / combien - pos)

        # Fuir le predateur -- la seule regle qui ne vienne pas du banc.
        if predateur is not None:
            ecart = pos - predateur
            loin = np.linalg.norm(ecart, axis=1)
            menace = loin < R_PREDATEUR
            if menace.any():
                force = (1.0 - loin[menace] / R_PREDATEUR) / np.maximum(loin[menace], 8.0)
                accel[menace] += P_FUITE * ecart[menace] * force[:, None]

        # Les bords repoussent, doucement, avant qu'on les touche.
        accel[:, 0] += P_BORD * np.clip(1.0 - pos[:, 0] / MARGE, 0, 1)
        accel[:, 0] -= P_BORD * np.clip(1.0 - (LARGEUR - pos[:, 0]) / MARGE, 0, 1)
        accel[:, 1] += P_BORD * np.clip(1.0 - pos[:, 1] / MARGE, 0, 1)
        accel[:, 1] -= P_BORD * np.clip(1.0 - (HAUTEUR - pos[:, 1]) / MARGE, 0, 1)

        pousse = np.linalg.norm(accel, axis=1)[:, None]
        accel *= np.minimum(pousse, ACCEL_MAX) / np.maximum(pousse, 1e-6)

        vit += accel * dt
        vite = np.linalg.norm(vit, axis=1)[:, None]
        vit *= np.clip(vite, VITESSE_MIN, VITESSE_MAX) / np.maximum(vite, 1e-6)
        self.pos += vit * dt
        np.clip(self.pos[:, 0], 2, LARGEUR - 2, out=self.pos[:, 0])
        np.clip(self.pos[:, 1], 2, HAUTEUR - 2, out=self.pos[:, 1])


# ---------------------------------------------------------------- le dessin

def eau():
    surface = pygame.Surface((LARGEUR, HAUTEUR))
    for y in range(HAUTEUR):
        k = (y / HAUTEUR) ** 0.75
        surface.fill(tuple(int(EAU_HAUT[i] + (EAU_BAS[i] - EAU_HAUT[i]) * k)
                           for i in range(3)), (0, y, LARGEUR, 1))
    return surface


def dessiner_poissons(toile, banc):
    """Chaque poisson est un triangle tourne dans le sens ou il nage."""
    vite = np.linalg.norm(banc.vit, axis=1)[:, None]
    avant = banc.vit / np.maximum(vite, 1e-6)
    cote = np.column_stack((-avant[:, 1], avant[:, 0]))

    museau = banc.pos + avant * 9.0
    gauche = banc.pos - avant * 5.0 + cote * 3.8
    droite = banc.pos - avant * 5.0 - cote * 3.8

    # Un seul passage en listes Python : pygame n'accepte pas les nombres numpy.
    for triangle in np.stack((museau, gauche, droite), axis=1).tolist():
        pygame.draw.polygon(toile, POISSON, triangle)


def dessiner_predateur(toile, ou, temps):
    pulsation = 1.0 + 0.06 * math.sin(temps * 5.0)
    halo = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
    pygame.draw.circle(halo, (*PREDATEUR, 26), ou.astype(int), int(R_PREDATEUR))
    toile.blit(halo, (0, 0))
    pygame.draw.circle(toile, PREDATEUR, ou.astype(int), int(15 * pulsation))


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
    fenetre = ouvrir("un banc de poissons")
    toile = pygame.Surface((LARGEUR, HAUTEUR))
    horloge = pygame.time.Clock()

    fond = eau()
    chemin = pygame.font.match_font("consolas") or pygame.font.match_font("segoeui")
    police = pygame.font.Font(chemin, 25)

    banc = Banc()
    etat = {"t": 0.0, "predateur": None}

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    banc = Banc()
                    etat.update(t=0.0, predateur=None)
                if evt.key == pygame.K_p:
                    etat["predateur"] = np.array([LARGEUR / 2, HAUTEUR + 60], np.float32)

        dt = min(horloge.tick(FPS) / 1000.0, 1 / 20)
        etat["t"] += dt
        t = etat["t"]

        regles = sum(1 for seuil, _ in ETAPES[1:] if t >= seuil)

        if etat["predateur"] is None and t >= PREDATEUR_A:
            etat["predateur"] = np.array([LARGEUR / 2, HAUTEUR + 60], np.float32)
        if etat["predateur"] is not None:
            # Il vise le centre du banc, sans jamais tout a fait le rattraper.
            vers = banc.pos.mean(0) - etat["predateur"]
            loin = np.linalg.norm(vers)
            if loin > 1.0:
                etat["predateur"] += vers / loin * 118.0 * dt

        banc.avancer(dt, regles, etat["predateur"])

        toile.blit(fond, (0, 0))
        dessiner_poissons(toile, banc)
        if etat["predateur"] is not None:
            dessiner_predateur(toile, etat["predateur"], t)

        for i, (seuil, libelle) in enumerate(ETAPES[1:]):
            if t >= seuil:
                vif = min((t - seuil) / 0.8, 1.0)
                img = police.render(libelle, True,
                                    tuple(int(c * vif) for c in TEXTE))
                toile.blit(img, (44, HAUTEUR - 150 + i * 36))

        pygame.transform.smoothscale(toile, fenetre.get_size(), fenetre)
        pygame.display.flip()


if __name__ == "__main__":
    sys.exit(main())
