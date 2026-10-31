# -*- coding: utf-8 -*-
"""
voir.py  --  La fenetre. Tout le calcul est dans infini.c.

Le C ne sait calculer que 4 a 100 images par seconde selon la profondeur.
Beaucoup trop peu pour que la descente soit fluide.

L'astuce est de ne pas lui demander de suivre. Chaque image recue est
estampillee de l'instant auquel elle correspond ; en attendant la suivante,
cette fenetre continue de zoomer *dedans*, en recadrant son centre. Comme
deux images successives ne different que d'un tout petit facteur d'echelle,
personne ne voit la difference -- et le zoom, lui, ne s'arrete jamais.

    gcc infini.c -o infini -lm -O3 -march=native -fopenmp
    python voir.py

    ECHAP : quitter
"""

import os
import struct
import subprocess
import sys
import threading

import pygame

# Ces trois valeurs doivent rester identiques a celles de infini.c.
LARGEUR, HAUTEUR = 360, 640
DEBUT = 1.5
VITESSE = 0.40

FORME = (720, 1280)          # le 9:16 vise, quelle que soit la taille reelle
OCTETS = LARGEUR * HAUTEUR * 3
ENTETE = struct.calcsize("d")


def ouvrir(titre):
    """Une fenetre 9:16 qui tient sur l'ecran.

    On vise toujours du 720 x 1280. Si l'ecran est plus petit -- un portable
    de 14 pouces annonce souvent 720 pixels de haut -- la fenetre l'est
    aussi, mais garde exactement la meme forme. Ce qu'on capture reste donc
    du 9:16. Lancer avec --plein force la taille d'origine.
    """
    pygame.init()
    pygame.display.set_caption(titre)
    haut = FORME[1]
    if "--plein" not in sys.argv:
        haut = max(420, min(FORME[1], int(pygame.display.Info().current_h * 0.88)))
    return pygame.display.set_mode((max(2, round(haut * FORME[0] / FORME[1])), haut))


def trouver_le_binaire():
    ici = os.path.dirname(os.path.abspath(__file__))
    for nom in ("infini.exe", "infini"):
        chemin = os.path.join(ici, nom)
        if os.path.exists(chemin):
            return chemin
    sys.exit("Compile d'abord :\n"
             "    gcc infini.c -o infini -lm -O3 -march=native -fopenmp")


class Source:
    """Lit les images du programme C dans un fil a part, pour ne jamais
    bloquer l'affichage."""

    def __init__(self, chemin):
        self.proc = subprocess.Popen([chemin], stdout=subprocess.PIPE, bufsize=0)
        self.verrou = threading.Lock()
        self.image = None
        self.instant = 0.0
        self.compte = 0
        self.fil = threading.Thread(target=self._boucle, daemon=True)
        self.fil.start()

    def _lire(self, combien):
        morceaux = bytearray()
        while len(morceaux) < combien:
            bout = self.proc.stdout.read(combien - len(morceaux))
            if not bout:
                return None
            morceaux += bout
        return bytes(morceaux)

    def _boucle(self):
        while True:
            entete = self._lire(ENTETE)
            if entete is None:
                return
            corps = self._lire(OCTETS)
            if corps is None:
                return
            with self.verrou:
                self.instant = struct.unpack("d", entete)[0]
                self.image = corps
                self.compte += 1

    def derniere(self):
        with self.verrou:
            return self.image, self.instant, self.compte

    def arreter(self):
        self.proc.terminate()


def main():
    fenetre = ouvrir("l'infini")
    horloge = pygame.time.Clock()

    source = Source(trouver_le_binaire())
    brute = pygame.Surface((LARGEUR, HAUTEUR))
    police = pygame.font.Font(pygame.font.match_font("consolas"), 22)

    mon_temps = 0.0
    vu = -1

    try:
        while True:
            for evt in pygame.event.get():
                if evt.type == pygame.QUIT:
                    return
                if evt.type == pygame.KEYDOWN and evt.key == pygame.K_ESCAPE:
                    return

            donnees, instant, compte = source.derniere()
            if donnees is None:
                fenetre.fill((0, 0, 0))
                pygame.display.flip()
                horloge.tick(30)
                continue

            if compte != vu:
                vu = compte
                # Le .convert() n'est pas cosmetique : sans lui la surface reste
                # en 24 bits alors que l'ecran est en 32, et smoothscale tasse
                # alors l'image sur les trois quarts de la largeur.
                brute = pygame.image.frombuffer(
                    donnees, (LARGEUR, HAUTEUR), "RGB").convert()
                if instant < mon_temps - 1.0:        # le C est reparti du haut
                    mon_temps = instant
                mon_temps = max(mon_temps, instant)

            # Entre deux images, on continue la descente en recadrant celle-ci.
            facteur = pow(2.718281828459045, VITESSE * (mon_temps - instant))
            facteur = max(1.0, min(facteur, 6.0))
            large = LARGEUR / facteur
            haute = HAUTEUR / facteur
            cadre = pygame.Rect(int((LARGEUR - large) / 2), int((HAUTEUR - haute) / 2),
                                max(2, int(large)), max(2, int(haute)))
            pygame.transform.smoothscale(brute.subsurface(cadre),
                                         fenetre.get_size(), fenetre)

            grossissement = DEBUT / (DEBUT * pow(2.718281828459045, -VITESSE * mon_temps))
            texte = police.render("x %.0e" % grossissement, True, (190, 190, 200))
            fenetre.blit(texte, (24, fenetre.get_height() - 48))

            pygame.display.flip()
            mon_temps += horloge.tick(60) / 1000.0
    finally:
        source.arreter()


if __name__ == "__main__":
    sys.exit(main())
