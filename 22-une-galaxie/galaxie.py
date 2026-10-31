# -*- coding: utf-8 -*-
"""
galaxie.py  --  Cinquante mille etoiles sur cinquante mille ellipses, et les
                 bras apparaissent.

Personne ne dessine de spirale ici. Il n'y a pas de courbe, pas de fonction en
r = exp(theta), aucune forme prevue. Il y a cinquante mille etoiles, chacune sur
son ellipse, et une seule idee -- celle de Bertil Lindblad, 1927 :

    les ellipses ne sont pas toutes orientees pareil.
    Leur inclinaison tourne doucement avec le rayon.

C'est tout. Deux ellipses voisines se croisent quelque part ; sur toute la
galaxie, les endroits ou elles se croisent forment deux bras. Les bras ne sont
pas des objets : ce sont des **embouteillages**. Les etoiles y entrent, s'y
serrent, et en ressortent -- comme les voitures dans un bouchon qui remonte
l'autoroute alors qu'aucune voiture ne recule.

    inclinaison(a) = TORSION . a          (a = demi-grand axe)

Au debut du film, TORSION vaut zero : toutes les ellipses sont alignees, et on
ne voit qu'un disque allonge. On la fait monter, et les bras se forment tout
seuls.

Le probleme de l'enroulement
----------------------------
Si chaque ellipse tournait a son propre rythme -- ce qui serait le plus naturel
--, la torsion augmenterait sans fin et les bras s'enrouleraient jusqu'a
disparaitre en quelques tours. Les vraies galaxies ont fait cent tours et ont
toujours deux bras. C'est pour ca qu'on arrete la torsion : elle devient une
figure qui tourne d'un bloc, a sa vitesse a elle, pendant que les etoiles la
traversent.

    python galaxie.py

    ESPACE : une autre galaxie     ECHAP : quitte
"""

import sys

import numpy as np
import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
FPS = 60

# La galaxie est ronde et l'image est haute : on ne calcule qu'un carre, et on
# le pose au milieu. Les deux bandes noires du haut et du bas sont gratuites --
# et ca fait 44 % de pixels en moins a traiter, a chaque image.
COTE = 360                      # le carre de calcul ; l'image fait 720 x 1280

NB = 110_000                    # les etoiles
BULBE = 0.08                    # la part d'entre elles qui sont au centre

RAYON = 152.0                   # le rayon du disque, en pixels du carre
ECHELLE = 0.45                  # la decroissance du disque
E_MAX = 0.40                    # l'aplatissement maximal des ellipses
E_RAYON = 0.30                  # le rayon ou l'aplatissement est deja atteint
DISPERSION = 0.034              # de combien une etoile s'ecarte de son ellipse

TORSION = 0.048                 # l'inclinaison gagnee par pixel de rayon
T_TORSION = 13.0                # le temps qu'elle met a s'installer
VITESSE = 26.0                  # la vitesse de rotation, a la peripherie
FIGURE = 0.085                  # la vitesse de la figure elle-meme (radians/s)

T_NUIT = 1.5

# --- couleurs : de l'etoile bleue (0) a l'etoile rouge (1)
TEINTES = [
    (0.00, (150, 190, 255)), (0.30, (225, 236, 255)), (0.55, (255, 244, 222)),
    (0.78, (255, 208, 150)), (1.00, (255, 158, 104)),
]
NEBULEUSE = (255, 120, 150)     # les nuages ou naissent les etoiles
PART_NEBULEUSE = 0.012
ECLAT = 0.40                    # la force du tone-mapping
HALO = 0.40                     # la lueur autour du disque
FOND = (5, 5, 9)


def palette(table, n=256):
    seuils = [s for s, _ in table]
    d = np.empty((n, 3), np.float32)
    x = np.linspace(0.0, 1.0, n)
    for c in range(3):
        d[:, c] = np.interp(x, seuils, [t[1][c] for t in table])
    return d


# ---------------------------------------------------------------- le disque

class Galaxie:
    """Cinquante mille ellipses. Rien d'autre n'est stocke.

    Une etoile, ici, c'est quatre nombres : son demi-grand axe, sa phase sur
    l'ellipse, sa vitesse angulaire et sa couleur. Sa position n'est jamais
    rangee nulle part -- elle se recalcule a chaque image, en dix lignes.
    """

    def __init__(self, graine):
        alea = np.random.RandomState(graine)
        self.alea = alea

        # Le disque : une exponentielle, comme les vrais. Le bulbe : le meme
        # tirage, mais ecrase vers le centre.
        u = alea.random_sample(NB)
        a = -RAYON * ECHELLE * np.log(1.0 - u * 0.986)
        bulbe = alea.random_sample(NB) < BULBE
        a[bulbe] *= alea.random_sample(int(bulbe.sum())) ** 1.7 * 0.55
        np.clip(a, 1.0, RAYON * 1.32, out=a)
        self.a = a.astype(np.float32)

        # L'aplatissement : nul au centre -- le bulbe est rond -- et maximal
        # des qu'on est dans le disque. C'est ce qui donne leur place aux bras.
        e = E_MAX * (1.0 - np.exp(-self.a / (RAYON * E_RAYON)))
        self.b = (self.a * (1.0 - e)).astype(np.float32)

        # Une etoile n'est pas exactement sur son ellipse : elle oscille autour.
        # Sans ce desordre, les ellipses se voient une par une -- des cerceaux
        # emboites au lieu d'un disque.
        self.dx = (alea.normal(0, 1, NB) * self.a * DISPERSION).astype(np.float32)
        self.dy = (alea.normal(0, 1, NB) * self.a * DISPERSION).astype(np.float32)

        self.phase = alea.uniform(0, 2 * np.pi, NB).astype(np.float32)
        # courbe de rotation plate : la vitesse est la meme partout, donc la
        # vitesse *angulaire* va comme 1/a. C'est ce qui fait tourner le centre
        # beaucoup plus vite que le bord.
        self.omega = (VITESSE / np.maximum(self.a, 6.0)).astype(np.float32)

        # la couleur : rouge au centre, bleue au bord, et du desordre
        t = np.clip(1.0 - self.a / (RAYON * 0.9), 0.0, 1.0) ** 0.8
        t += alea.normal(0.0, 0.17, NB)
        self.teinte = np.clip(t, 0.0, 1.0).astype(np.float32)
        self.eclat = (0.35 + alea.random_sample(NB) ** 3 * 2.2)
        # les toutes dernieres etoiles s'eteignent doucement, pour que le
        # disque n'ait pas un bord net
        self.eclat *= np.clip((RAYON * 1.34 - self.a) / (RAYON * 0.22), 0.0, 1.0)
        self.eclat = self.eclat.astype(np.float32)
        # une etoile sur quatre-vingts est une nebuleuse : plus grosse, rose
        neb = alea.random_sample(NB) < PART_NEBULEUSE
        self.nebuleuse = neb & (self.a > RAYON * 0.25)
        self.eclat[self.nebuleuse] *= 2.6
        # l'eclat deja multiplie par la teinte : c'est le second comptage, et
        # il ne change jamais, autant le faire une fois pour toutes
        self.chaleur = self.eclat * self.teinte

        self.t = 0.0
        self.x = np.empty(NB, np.float32)
        self.y = np.empty(NB, np.float32)
        self.avancer(0.0)

    def avancer(self, dt):
        self.t += dt
        # la torsion s'installe, puis s'arrete : voir le README
        u = min(1.0, self.t / T_TORSION)
        torsion = TORSION * (u * u * (3.0 - 2.0 * u))

        theta = self.phase + self.omega * np.float32(self.t)
        xe = self.a * np.cos(theta) + self.dx
        ye = self.b * np.sin(theta) + self.dy

        psi = self.a * np.float32(torsion) + np.float32(FIGURE * self.t)
        c, s = np.cos(psi), np.sin(psi)
        np.subtract(xe * c, ye * s, out=self.x)
        np.add(xe * s, ye * c, out=self.y)
        return torsion

    def bras(self):
        """La force des bras, mesuree comme le font les astronomes : l'amplitude
        du mode a deux branches.

        On prend les etoiles d'une couronne, on regarde ou elles sont en angle,
        et on demande : est-ce qu'elles se groupent en deux paquets opposes ?
        C'est la moyenne de exp(2.i.phi). Zero = reparties partout ; un = toutes
        dans deux rayons.
        """
        r = np.hypot(self.x, self.y)
        phi = np.arctan2(self.y, self.x)
        z = np.exp(2j * phi)
        # couronne par couronne : un bras s'enroule, donc si on melange les
        # rayons les paquets ne tombent plus au meme angle et tout s'annule
        total = 0.0
        bornes = np.linspace(RAYON * 0.35, RAYON * 1.0, 9)
        for i in range(8):
            pris = (r >= bornes[i]) & (r < bornes[i + 1])
            if pris.sum() > 200:
                total += abs(np.mean(z[pris]))
        return total / 8.0


# ---------------------------------------------------------------- l'image

class Vue:
    """Deux comptages par image : la lumiere, et la couleur qu'elle porte.

    Une etoile depose son eclat dans un tableau, et son eclat *multiplie par sa
    teinte* dans un second. Le rapport des deux donne la teinte moyenne du
    pixel, ponderee par la lumiere -- ce qui est exactement ce que fait un
    capteur. Deux comptages suffisent pour une image en couleur, la ou trois
    seraient necessaires en rouge-vert-bleu.

    Et la teinte et la luminosite ne sont pas combinees a la main : elles sont
    reduites a 16 et 256 niveaux, mises bout a bout en un seul indice, et la
    couleur finale sort d'une table de 4 096 entrees. Une seule lecture de
    table remplace une exponentielle, une multiplication a trois canaux et une
    conversion -- 9,5 ms l'image contre 3,4.
    """

    TEINTES_Q = 16              # les niveaux de teinte de la table
    GAIN = 26.0                 # la lumiere qui correspond au dernier niveau

    def __init__(self):
        self.table = self.fabriquer()
        self.pixels = np.empty((COTE, COTE, 3), np.uint8)
        self.carre = pygame.Surface((COTE, COTE))
        self.floue = pygame.Surface((COTE // 5, COTE // 5))
        self.lueur = pygame.Surface((COTE, COTE))
        self.agrandi = None

    def fabriquer(self):
        """La table teinte x lumiere -> couleur, avec le tone-mapping dedans."""
        couleurs = palette(TEINTES, self.TEINTES_Q)
        lum = np.arange(256, dtype=np.float32) / self.GAIN
        ton = 1.0 - np.exp(-ECLAT * lum)
        t = np.multiply.outer(couleurs, ton)            # (teintes, 3, 256)
        return np.clip(t.transpose(0, 2, 1).reshape(-1, 3), 0, 255).astype(np.uint8)

    def dessiner(self, g, ecran):
        ix = np.clip(g.x + COTE * 0.5, 0, COTE - 1).astype(np.int32)
        iy = np.clip(g.y + COTE * 0.5, 0, COTE - 1).astype(np.int32)
        plat = ix * COTE + iy
        lumiere = np.bincount(plat, weights=g.eclat, minlength=COTE * COTE)
        chaud = np.bincount(plat, weights=g.chaleur, minlength=COTE * COTE)

        teinte = chaud / np.maximum(lumiere, 1e-6)
        idx = (teinte * (self.TEINTES_Q - 0.01)).astype(np.int32)
        idx *= 256
        idx += np.clip(lumiere * self.GAIN, 0, 255).astype(np.int32)
        np.take(self.table, idx.reshape(COTE, COTE), axis=0, out=self.pixels)

        pygame.surfarray.blit_array(self.carre, self.pixels)
        pygame.transform.smoothscale(self.carre, self.floue.get_size(), self.floue)
        pygame.transform.smoothscale(self.floue, (COTE, COTE), self.lueur)
        self.lueur.fill((int(255 * HALO),) * 3, special_flags=pygame.BLEND_MULT)
        self.carre.blit(self.lueur, (0, 0), special_flags=pygame.BLEND_ADD)

        large, haut = ecran.get_size()
        if self.agrandi is None or self.agrandi.get_width() != large:
            self.agrandi = pygame.Surface((large, large))
            ecran.fill(FOND)
        pygame.transform.smoothscale(self.carre, (large, large), self.agrandi)
        ecran.blit(self.agrandi, (0, (haut - large) // 2))


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
    fenetre = ouvrir("une galaxie")
    horloge = pygame.time.Clock()
    vue = Vue()
    galaxie = Galaxie(np.random.randint(1, 10_000_000))
    t = 0.0

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    galaxie = Galaxie(np.random.randint(1, 10_000_000))
                    t = 0.0

        dt = min(horloge.tick(FPS) / 1000.0, 1 / 20)
        t += dt
        if t >= T_NUIT:
            galaxie.avancer(dt)
        vue.dessiner(galaxie, fenetre)
        pygame.display.flip()


if __name__ == "__main__":
    sys.exit(main())
