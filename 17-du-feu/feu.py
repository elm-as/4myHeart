# -*- coding: utf-8 -*-
"""
feu.py  --  Trois braises, un vent qui ne peut pas se comprimer, et ca prend.

Il n'y a pas d'images de flammes dans ce programme, pas de textures, pas de
degrades peints a la main. Il y a un champ de chaleur sur une grille de
180 x 320, et trois regles :

  1.  ce qui est chaud monte        (la poussee d'Archimede)
  2.  ce qui monte se melange       (la turbulence)
  3.  ce qui se melange refroidit   (et finit par disparaitre)

La flamme est ce qui reste quand on laisse tourner ces trois regles.

Le vent : incompressible, et gratuit
------------------------------------
Un fluide qui n'est ni comprime ni dilate verifie div(v) = 0. C'est la
condition qui coute cher dans les vraies simulations : on resout une equation
de Poisson a chaque image pour projeter le champ de vitesse.

Ici on ne la resout pas. On ecrit d'abord une fonction de courant psi(x, y, t),
et on prend la vitesse comme :

    u = +d(psi)/dy        v = -d(psi)/dx

Fait comme ca, div(v) = d2(psi)/dxdy - d2(psi)/dydx = 0, exactement, a la
precision de la machine. Pas d'iteration, pas de resolution, pas d'erreur.
Et comme psi est une somme de sinus, les derivees sont des sinus aussi : tout
le champ de vent tient en six produits exterieurs par image.

Le transport
------------
Chaque case regarde d'ou vient l'air qu'elle recoit -- on remonte le courant
d'un pas de temps -- et prend la chaleur qu'il y avait la-bas. C'est la methode
semi-lagrangienne : elle ne peut pas exploser, meme avec un gros pas de temps.

Le feu qui se propage
---------------------
Le sol n'est pas allume partout d'un coup. Chaque braise pousse un front qui
avance a vitesse constante, mais dans un combustible irregulier : le front
traine la ou ca resiste, court la ou ca brule bien. Il faut 25 secondes pour
que les trois fronts se rejoignent et prennent tout le sol.

    python feu.py

    ESPACE : on rallume     ECHAP : quitte
"""

import sys

import numpy as np
import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
FPS = 60

ZOOM = 4                        # la grille fait 180 x 320, l'image 720 x 1280
GL, GH = LARGEUR // ZOOM, HAUTEUR // ZOOM
SOL = GH - 18                   # la ligne de braises

PAS = 1 / 60.0                  # le pas de calcul

# --- la chaleur
POUSSEE = 95.0          # de combien la chaleur tire vers le haut (cases/s)
TIRAGE = 8.0            # le courant d'air general, meme sans flamme
REFROID = 0.86          # ce que la chaleur perd par seconde, en proportion
PERTE = 0.035           # et ce qu'elle perd en valeur absolue : ca eteint les fumees

# Le vent, terme par terme : (amplitude, longueur d'onde en x, en y, derive).
# Les longueurs d'onde sont en cases -- des tourbillons de 140 cases pour le
# premier, de 11 pour le dernier.
TOURBILLONS = [
    (530.0, 138.0, 139.0, 0.42),
    (190.0, 49.0, 70.0, -0.78),
    (60.0, 20.0, 36.0, 1.55),
    (14.0, 11.0, 21.0, -2.60),
]
VENT_FROID = 0.25       # la part de turbulence qui agite l'air froid

# --- le feu qui prend
BRAISES = [(0.34, 2.6), (0.66, 6.0), (0.12, 10.5)]   # position en x, instant
VITESSE = 4.0           # la vitesse du front, en cases par seconde
FLOU = 5.0              # la largeur du front
RESISTE = 0.55          # l'irregularite du combustible
SOURCE = 0.86           # la chaleur injectee par une case allumee
RESPIRE = 0.30          # de combien le foyer bat, d'un endroit a l'autre

# --- les etincelles
ETINCELLES = 900
VIE = 2.6               # leur duree de vie, en secondes
MONTEE = 26.0           # ce qui les tire vers le haut, en plus du vent

# --- les couleurs (temperature -> couleur, du noir au blanc)
FLAMME = [
    (0.00, (0, 0, 0)), (0.10, (34, 5, 2)), (0.22, (98, 16, 5)),
    (0.38, (182, 48, 8)), (0.56, (234, 104, 17)), (0.74, (248, 158, 40)),
    (0.90, (253, 200, 92)), (1.00, (255, 232, 158)),
]
BRAISE = (150, 40, 12)          # les braises pas encore allumees
NUIT = (7, 6, 8)                # le fond
HALO = 0.55                     # la force de la lueur autour du feu


# ------------------------------------------------------------- la palette

def palette(table, n=256):
    seuils = [s for s, _ in table]
    d = np.empty((n, 3), np.float32)
    x = np.linspace(0.0, 1.0, n)
    for c in range(3):
        d[:, c] = np.interp(x, seuils, [t[1][c] for t in table])
    return d


# ---------------------------------------------------------------- le foyer

class Foyer:
    """Le champ de chaleur, le vent qui le transporte, et le sol qui l'alimente."""

    def __init__(self, graine):
        alea = np.random.RandomState(graine)
        self.alea = alea
        self.t = 0.0

        self.T = np.zeros((GL, GH), np.float32)
        self.x = np.arange(GL, dtype=np.float32)
        self.y = np.arange(GH, dtype=np.float32)

        # Le combustible n'est pas le meme partout. On tire une resistance au
        # hasard, lissee, et on en fait une distance cumulee : le front met
        # plus longtemps a traverser une case qui resiste.
        bruit = alea.standard_normal(GL).astype(np.float32)
        for _ in range(6):                      # lissage : moyenne des voisins
            bruit = (np.roll(bruit, 1) + 2.0 * bruit + np.roll(bruit, -1)) * 0.25
        bruit /= max(float(np.abs(bruit).max()), 1e-6)
        self.route = np.cumsum(1.0 + RESISTE * bruit).astype(np.float32)

        # les trois braises elles-memes : elles rougeoient avant d'allumer
        self.braises = np.zeros(GL, np.float32)
        for px, _ in BRAISES:
            d = (self.x - px * (GL - 1)) / 2.6
            np.maximum(self.braises, np.exp(-d * d), out=self.braises)

        self.phases = alea.uniform(0, 2 * np.pi, (len(TOURBILLONS), 2))
        self.u = np.zeros((GL, GH), np.float32)
        self.v = np.zeros((GL, GH), np.float32)
        self.allume = np.zeros(GL, np.float32)

        # les tampons du transport, reserves une fois pour toutes
        self.bx = np.empty((GL, GH), np.float32)
        self.by = np.empty((GL, GH), np.float32)
        self.fx = np.empty((GL, GH), np.float32)
        self.fy = np.empty((GL, GH), np.float32)

    # -- le vent -----------------------------------------------------------

    def vent(self, dt):
        """Le champ de vitesse, a divergence nulle par construction.

        psi = somme de A.sin(kx.x + p).sin(ky.y + q), donc :
            u = +dpsi/dy = somme  A.ky.sin(kx.x + p).cos(ky.y + q)
            v = -dpsi/dx = somme -A.kx.cos(kx.x + p).sin(ky.y + q)

        Chaque terme est un produit d'une fonction de x par une fonction de y :
        un produit exterieur, et rien de plus. Six au total.
        """
        self.u.fill(0.0)
        self.v.fill(0.0)
        for i, (a, lx, ly, derive) in enumerate(TOURBILLONS):
            self.phases[i, 0] += derive * dt
            self.phases[i, 1] -= derive * 0.63 * dt
            kx = 2.0 * np.pi / lx
            ky = 2.0 * np.pi / ly
            sx = np.sin(kx * self.x + self.phases[i, 0])
            cx = np.cos(kx * self.x + self.phases[i, 0])
            sy = np.sin(ky * self.y + self.phases[i, 1])
            cy = np.cos(ky * self.y + self.phases[i, 1])
            # Les deux amplitudes ci-dessous sont le meme a, l'une multipliee
            # par ky et l'autre par kx. C'est la condition pour que ca vienne
            # bien d'une fonction de courant -- et donc que ca ne se comprime
            # pas. Deux echelles differentes, et la divergence revient.
            self.u += np.multiply.outer(sx, cy) * np.float32(a * ky)
            self.v -= np.multiply.outer(cx, sy) * np.float32(a * kx)

        # L'air froid ne tourbillonne presque pas : sans ca, le fond de l'image
        # respire alors qu'il ne s'y passe rien.
        agite = self.T * np.float32(1.0 - VENT_FROID) + np.float32(VENT_FROID)
        self.u *= agite
        self.v *= agite

        # Ce qui est chaud monte. C'est la seule ligne de physique du fichier.
        self.v -= self.T * np.float32(POUSSEE) * self.souffle()
        self.v -= np.float32(TIRAGE)

    def battement(self):
        """Une braise ne brille pas d'un eclat fixe : elle respire."""
        return 0.72 + 0.28 * np.sin(self.t * 1.9) * np.sin(self.t * 0.7 + 1.0)

    def souffle(self):
        """Un grand feu tire plus fort qu'un petit : il aspire moins d'air froid
        sur ses cotes. C'est un coefficient, pas une equation -- mais sans lui
        la flamme garde la meme hauteur du debut a la fin."""
        return np.float32(0.55 + 0.45 * float(self.allume.mean()))

    # -- le transport ------------------------------------------------------

    def transporter(self, dt):
        """Semi-lagrangien : chaque case va chercher d'ou vient son air.

        On remonte le courant d'un pas de temps, on tombe entre quatre cases,
        on prend leur moyenne ponderee. Rien ne peut exploser : la valeur
        obtenue est toujours entre les quatre valeurs de depart.
        """
        np.multiply(self.u, np.float32(-dt), out=self.bx)
        self.bx += self.x[:, None]
        np.multiply(self.v, np.float32(-dt), out=self.by)
        self.by += self.y[None, :]
        np.clip(self.bx, 0.0, GL - 1.001, out=self.bx)
        np.clip(self.by, 0.0, GH - 1.001, out=self.by)

        i = self.bx.astype(np.int32)
        j = self.by.astype(np.int32)
        np.subtract(self.bx, i, out=self.fx)
        np.subtract(self.by, j, out=self.fy)

        plat = self.T.reshape(-1)
        base = i * GH + j
        a = plat[base]
        b = plat[base + GH]
        c = plat[base + 1]
        d = plat[base + GH + 1]
        haut = a + (b - a) * self.fx
        bas = c + (d - c) * self.fx
        np.add(haut, (bas - haut) * self.fy, out=self.T)

    # -- le sol ------------------------------------------------------------

    def allumage(self):
        """Les fronts de feu, partis de chaque braise, dans un sol irregulier."""
        self.allume.fill(0.0)
        for px, t0 in BRAISES:
            if self.t < t0:
                continue
            depart = self.route[int(px * (GL - 1))]
            avance = VITESSE * (self.t - t0) - np.abs(self.route - depart)
            np.maximum(self.allume, np.clip(avance / FLOU, 0.0, 1.0),
                       out=self.allume)

    def avancer(self, dt):
        self.t += dt
        self.allumage()
        self.vent(dt)
        self.transporter(dt)

        # refroidissement : une part, et un peu en valeur absolue
        self.T *= np.float32(max(0.0, 1.0 - REFROID * dt))
        self.T -= np.float32(PERTE * dt)
        np.maximum(self.T, 0.0, out=self.T)

        # Le sol reinjecte de la chaleur la ou ca brule. Deux irregularites :
        # une lente, qui se deplace -- le foyer ne brule pas pareil partout, et
        # ce n'est pas toujours au meme endroit ; une rapide, par case, qui
        # donne son grain a la base de la flamme.
        souffle = (np.sin(self.x * 0.052 + self.t * 0.55) +
                   0.7 * np.sin(self.x * 0.021 - self.t * 0.31))
        chaud = self.allume * np.float32(SOURCE) * (1.0 + RESPIRE * souffle)
        chaud = chaud * (0.78 + 0.44 * self.alea.random_sample(GL)).astype(np.float32)
        # une braise chauffe l'air au-dessus d'elle bien avant de prendre
        np.maximum(chaud, self.braises * np.float32(0.11 * self.battement()),
                   out=chaud)
        np.maximum(self.T[:, SOL - 2:SOL + 1], chaud[:, None],
                   out=self.T[:, SOL - 2:SOL + 1])


# ------------------------------------------------------------ les etincelles

class Etincelles:
    """Des braises arrachees au foyer. Elles ne chauffent rien : elles se voient.

    Sans elles la flamme est un degrade qui ondule, et ca se voit que c'est un
    degrade. Une etincelle est un point net qui a une trajectoire : c'est elle
    qui donne l'echelle et la vitesse du reste.
    """

    def __init__(self, alea):
        self.alea = alea
        self.pos = np.zeros((ETINCELLES, 2), np.float32)
        self.vit = np.zeros((ETINCELLES, 2), np.float32)
        self.vie = np.zeros(ETINCELLES, np.float32)

    def avancer(self, foyer, dt):
        vivantes = self.vie > 0.0
        n = int(vivantes.sum())

        # on en rallume autant qu'il en meurt, proportionnellement au feu
        naissent = int(ETINCELLES * float(foyer.allume.mean()) * 0.55) - n
        if naissent > 0:
            libres = np.flatnonzero(~vivantes)[:naissent]
            if libres.size:
                p = foyer.allume.astype(np.float64)
                p /= p.sum()
                xs = self.alea.choice(GL, libres.size, p=p)
                self.pos[libres, 0] = xs + self.alea.random_sample(libres.size)
                self.pos[libres, 1] = SOL - self.alea.random_sample(libres.size) * 3.0
                self.vit[libres] = 0.0
                self.vie[libres] = VIE * (0.45 + 0.55 * self.alea.random_sample(libres.size))
                vivantes[libres] = True

        if not vivantes.any():
            return
        i = np.clip(self.pos[vivantes, 0], 0, GL - 1).astype(np.int32)
        j = np.clip(self.pos[vivantes, 1], 0, GH - 1).astype(np.int32)
        cible = np.stack([foyer.u[i, j], foyer.v[i, j] - MONTEE], 1)

        # l'etincelle ne suit pas le vent : elle s'y ajuste. C'est ce retard
        # qui lui donne sa trajectoire propre, au lieu de coller au courant.
        v = self.vit[vivantes]
        v += (cible - v) * np.float32(min(1.0, 4.0 * dt))
        self.vit[vivantes] = v
        self.pos[vivantes] += v * np.float32(dt)
        self.vie[vivantes] -= dt
        self.vie[self.pos[:, 1] < 0.0] = 0.0
        np.maximum(self.vie, 0.0, out=self.vie)


# ---------------------------------------------------------------- l'image

class Vue:
    """La grille 180 x 320 devient l'image, plus un halo, plus les etincelles.

    Deux choses ici ne sont pas de la mise en forme, ce sont des economies :

    -  le halo se fabrique sur la petite image, pas sur la grande. C'est la
       meme chose a l'oeil -- il est flou de toute facon -- et ca evite un
       agrandissement et une addition sur 921 600 pixels.
    -  la grille est agrandie **directement a la taille de la fenetre**, une
       seule fois, et les etincelles sont posees dessus. Passer par une image
       720 x 1280 intermediaire, puis la reduire, coute deux fois le prix pour
       exactement la meme image.
    """

    def __init__(self):
        self.feu = palette(FLAMME)
        self.petite = pygame.Surface((GL, GH))
        self.floue = pygame.Surface((GL // 3, GH // 3))
        self.lueur = pygame.Surface((GL, GH))
        self.pixels = np.empty((GL, GH, 3), np.uint8)

    def dessiner(self, foyer, etincelles, ecran):
        # la chaleur -> la palette
        idx = np.clip(foyer.T * 255.0, 0, 255).astype(np.uint8)
        np.copyto(self.pixels, self.feu[idx], casting="unsafe")

        # Le sol : noir la ou il n'y a rien, rouge sombre sur les braises,
        # vif la ou ca brule. Avant l'allumage, ce sont les trois seules choses
        # visibles de toute l'image.
        braise = np.maximum(foyer.allume,
                            foyer.braises * np.float32(0.62 * foyer.battement()))
        lit = self.pixels[:, SOL:SOL + 2]
        np.maximum(lit, (np.multiply.outer(braise, np.array(BRAISE, np.float32))
                         ).astype(np.uint8)[:, None, :], out=lit)
        pygame.surfarray.blit_array(self.petite, self.pixels)

        # le halo : la meme image, reduite trois fois puis rendue -- donc floue
        # -- attenuee, et rajoutee par-dessus
        pygame.transform.smoothscale(self.petite, self.floue.get_size(), self.floue)
        pygame.transform.smoothscale(self.floue, (GL, GH), self.lueur)
        self.lueur.fill((int(255 * HALO),) * 3, special_flags=pygame.BLEND_MULT)
        self.petite.blit(self.lueur, (0, 0), special_flags=pygame.BLEND_ADD)

        large, haut = ecran.get_size()
        pygame.transform.smoothscale(self.petite, (large, haut), ecran)

        # les etincelles, par-dessus, a la resolution de l'ecran
        vivantes = etincelles.vie > 0.0
        if not vivantes.any():
            return
        ech = large / float(GL)
        gros = 2 if ech >= 2.5 else 1
        p = etincelles.pos[vivantes] * ech
        age = np.clip(etincelles.vie[vivantes] / VIE, 0.0, 1.0)
        couleur = self.feu[np.clip(120 + age * 135, 0, 255).astype(np.uint8)]
        dedans = ((p[:, 0] >= 0) & (p[:, 0] < large - gros) &
                  (p[:, 1] >= 0) & (p[:, 1] < haut - gros))
        p = p[dedans].astype(np.int32)
        couleur = couleur[dedans].astype(np.uint8)
        # tab[ix, iy] est une copie, pas une vue : il faut reaffecter. Avec
        # out=tab[ix, iy], numpy ecrit dans un tableau temporaire et
        # l'etincelle n'apparait jamais -- cherchee pendant vingt minutes.
        tab = pygame.surfarray.pixels3d(ecran)
        for dx in range(gros):
            for dy in range(gros):
                ix, iy = p[:, 0] + dx, p[:, 1] + dy
                tab[ix, iy] = np.maximum(tab[ix, iy], couleur)
        del tab


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
    fenetre = ouvrir("du feu")
    horloge = pygame.time.Clock()
    vue = Vue()

    graine = np.random.randint(1, 10_000_000)
    foyer = Foyer(graine)
    etincelles = Etincelles(foyer.alea)
    reste = 0.0

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    foyer = Foyer(np.random.randint(1, 10_000_000))
                    etincelles = Etincelles(foyer.alea)
                    reste = 0.0

        ecoule = min(horloge.tick(FPS) / 1000.0, 1 / 20)
        reste += ecoule
        while reste >= PAS:
            foyer.avancer(PAS)
            etincelles.avancer(foyer, PAS)
            reste -= PAS

        vue.dessiner(foyer, etincelles, fenetre)
        pygame.display.flip()


if __name__ == "__main__":
    sys.exit(main())
