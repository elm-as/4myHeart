# -*- coding: utf-8 -*-
"""
eau.py  --  Mille quatre cents points qui n'ont qu'une consigne : ne pas se
             serrer. Et ca fait une vague.

Il n'y a pas de surface dans ce programme. Pas de hauteur d'eau, pas de courbe,
pas de maillage. Il y a des points, et une seule contrainte :

    la densite autour de chaque point doit valoir rho0.

Rien d'autre. La vague, l'ecume, l'eclaboussure qui monte le long du mur, la
flaque qui finit par s'aplatir : tout ca est ce que fait un tas de points qui
refusent d'etre serres, dans un champ de pesanteur.

La methode
----------
C'est la methode PBF -- Position Based Fluids, Macklin et Muller, 2013. Elle ne
calcule pas de forces de pression. Elle deplace les points :

  1.  la gravite pousse tout le monde : p = x + dt.v
  2.  on mesure la densite autour de chaque point, avec un noyau lisse
  3.  on calcule de combien il faudrait bouger pour que cette densite revienne
      a rho0 -- c'est un multiplicateur de Lagrange, lambda
  4.  on bouge. Puis on recommence trois fois.
  5.  la vitesse, a la fin, est simplement (p - x) / dt

L'interet, par rapport a la methode classique (SPH a pression explicite) : la
correction est une **position**, pas une force. On ne peut donc pas exploser --
au pire le fluide est un peu compressible. C'est ce qui permet de faire un pas
de temps d'une image entiere au lieu d'un millieme de seconde.

Le terme anti-grumeaux -- celui qui n'a rien fait
-------------------------------------------------
La methode prescrit une pression artificielle, negative, contre l'instabilite
de traction : sans elle, les points sont censes se coller par paquets de trois
ou quatre et la surface devient granuleuse. Elle est la, TENSION.

Mesuree, elle ne change rien ici : avec ou sans, la distance au plus proche
voisin reste a 3,85 unites pour 4,00 au repos. La raison est que le rayon du
noyau vaut 1,67 fois l'espacement -- chaque point voit huit voisins, assez pour
que la densite soit bien estimee. Les grumeaux apparaissent quand le noyau est
plus serre. On la garde parce qu'elle protege les autres reglages, pas parce
qu'elle sert a celui-la.

    python eau.py

    ESPACE : on remonte le barrage     ECHAP : quitte
"""

import sys

import numpy as np
import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
FPS = 60

ZOOM = 4                        # on calcule en 180 x 320, on dessine en 720 x 1280
BX, BY = LARGEUR / ZOOM, HAUTEUR / ZOOM     # le bassin, en unites
MUR = 2.0                       # l'epaisseur des bords

ESPACE = 4.00                   # la distance entre deux points au repos
H = 6.67                        # le rayon du noyau : 1,67 fois l'espacement
COLONNES, LIGNES = 22, 64       # la colonne du depart : 1 408 points

G = 80.0                        # la pesanteur, en unites par seconde carree
PAS = 1 / 60.0
ITERATIONS = 4                  # les passes de correction de densite
RELACHE = 0.040                 # epsilon : ce qui empeche lambda d'exploser
DETENTE = 1.00                  # la part de la correction qu'on applique
VMAX = 195.0                    # la vitesse maximale, en unites par seconde
SERRE = False                   # ne corriger que la compression, jamais l'inverse
VISCO = 0.055                   # XSPH : de combien un point suit ses voisins

# le terme anti-grumeaux
TENSION = 0.0008
DQ = 0.28                       # la distance de reference, en fraction de H
PUISSANCE = 4

CASES = 5                       # points gardes par case de la grille de voisinage
VOISINS = 16                    # voisins gardes par point apres le tri

T_BARRAGE = 2.2                 # le temps que le bloc reste sage

# --- couleurs
BASSIN = (13, 17, 26)
PROFOND = (12, 42, 92)          # l'eau epaisse
CLAIRE = (64, 150, 210)         # l'eau fine
ECUME = (226, 242, 250)         # les gouttes isolees, les cretes
SEUIL = 0.30                    # la densite a partir de laquelle on voit de l'eau


# ---------------------------------------------------------------- les noyaux

POLY6 = 4.0 / (np.pi * H ** 8)
SPIKY = 30.0 / (np.pi * H ** 5)


def poids(r2):
    """Poly6 : lisse, nul au bord, et ne demande jamais de racine carree."""
    q = np.maximum(H * H - r2, 0.0)
    return q * q * q * POLY6


def gradient(r):
    """Spiky : son gradient ne s'annule pas quand deux points se touchent.

    C'est la raison d'etre de ce noyau-la. Avec Poly6, deux points colles ne
    se repoussent plus -- la derivee est nulle en zero -- et le fluide fait des
    grumeaux qu'il ne peut plus defaire.
    """
    return np.maximum(H - r, 0.0) ** 2 * SPIKY


# ---------------------------------------------------------------- le fluide

class Eau:
    """Les points, leurs voisins, et les trois passes de correction."""

    def __init__(self, graine):
        alea = np.random.RandomState(graine)

        x = MUR + 1.0 + np.arange(COLONNES) * ESPACE
        y = BY - MUR - 1.0 - np.arange(LIGNES) * ESPACE
        p = np.stack(np.meshgrid(x, y, indexing='ij'), -1).reshape(-1, 2)
        # un cheveu de desordre : une grille parfaite est un equilibre instable,
        # elle se defait d'un coup au lieu de couler
        p += alea.uniform(-0.02, 0.02, p.shape)
        self.x = p.astype(np.float32)
        self.v = np.zeros_like(self.x)
        self.p = self.x.copy()
        self.n = len(self.x)

        # la grille de voisinage : une case fait un rayon de noyau
        self.nx = int(BX / H) + 3
        self.ny = int(BY / H) + 3
        self.grille = np.full((self.nx, self.ny, CASES), -1, np.int32)
        self.candidats = np.zeros((self.n, 9 * CASES), np.int32)
        self.voisins = np.zeros((self.n, VOISINS), np.int32)

        # rho0 : la densite d'un empilement regulier au repos. On la mesure au
        # lieu de la choisir -- elle depend du noyau, de H et de l'espacement,
        # et se tromper dessus fait un fluide qui gonfle ou qui s'ecrase.
        k = int(H / ESPACE) + 1
        d = np.arange(-k, k + 1) * ESPACE
        rx, ry = np.meshgrid(d, d, indexing='ij')
        self.rho0 = float(poids(rx * rx + ry * ry).sum())
        self.wdq = float(poids(np.array([(DQ * H) ** 2]))[0])
        self.barrage = True
        self.t = 0.0

    # -- les voisins -------------------------------------------------------

    def chercher(self):
        """Range les points dans une grille, puis lit les neuf cases autour.

        Chaque case ne garde que CASES points. C'est un mensonge -- il peut y
        en avoir plus -- mais au repos une case en contient 2,8 en moyenne, et
        les rares fois ou ca deborde, le point oublie est repris a l'image
        suivante. En echange, tout est un tableau rectangulaire, donc tout est
        vectorise.
        """
        c = np.clip((self.p / H).astype(np.int32) + 1, 1, [self.nx - 2, self.ny - 2])
        plat = c[:, 0] * self.ny + c[:, 1]
        ordre = np.argsort(plat, kind='stable')
        tri = plat[ordre]
        # le rang de chaque point dans sa case, sans boucle : on compte combien
        # de points de la meme case sont deja passes
        depart = np.searchsorted(tri, tri)
        rang = np.arange(self.n) - depart
        garde = rang < CASES
        self.grille.fill(-1)
        self.grille.reshape(-1, CASES)[tri[garde], rang[garde]] = ordre[garde]

        k = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                self.candidats[:, k:k + CASES] = \
                    self.grille[c[:, 0] + dx, c[:, 1] + dy]
                k += CASES
        self.serrer()

    def serrer(self):
        """Des 45 places candidates, on ne garde que les vrais voisins.

        Les neuf cases autour d'un point offrent 45 places, dont huit seulement
        sont a portee du noyau : les trente-sept autres sont vides ou trop
        loin, et on les trainerait dans tous les calculs. Les compacter une
        fois par image coute 1,5 ms et fait tomber le reste de 12 a 4.
        """
        cand = self.candidats
        valide = cand >= 0
        idx = np.where(valide, cand, 0)
        dx = self.p[idx, 0] - self.p[:, 0:1]
        dy = self.p[idx, 1] - self.p[:, 1:2]
        proche = valide & (dx * dx + dy * dy < H * H)
        rang = np.cumsum(proche, axis=1) - 1
        garde = proche & (rang < VOISINS)
        self.voisins.fill(-1)
        i, j = np.nonzero(garde)
        self.voisins[i, rang[i, j]] = cand[i, j]

    # -- une image ---------------------------------------------------------

    def avancer(self, dt):
        self.t += dt
        if self.barrage and self.t >= T_BARRAGE:
            self.barrage = False

        self.v[:, 1] += np.float32(G * dt)
        if self.barrage:
            self.v[:] = 0.0
        # Un point ne doit jamais franchir plus d'un demi-rayon de noyau en un
        # pas : au-dela, deux points se traversent sans s'etre vus.
        vite = np.hypot(self.v[:, 0], self.v[:, 1])
        trop = vite > VMAX
        if trop.any():
            self.v[trop] *= (VMAX / vite[trop])[:, None]
        np.add(self.x, self.v * np.float32(dt), out=self.p)
        self.bords(self.p)
        self.chercher()

        vois = self.voisins
        valide = vois >= 0
        idx = np.where(valide, vois, 0)

        for _ in range(ITERATIONS):
            dx = self.p[idx, 0] - self.p[:, 0:1]
            dy = self.p[idx, 1] - self.p[:, 1:2]
            r2 = dx * dx + dy * dy

            # Les deux noyaux s'annulent au-dela de H : inutile de tester la
            # distance, il suffit d'ecarter les places vides.
            w = poids(r2) * valide
            rho = w.sum(1)

            # de combien la densite est-elle fausse, et dans quel sens
            contrainte = rho / self.rho0 - 1.0
            if SERRE:
                np.maximum(contrainte, 0.0, out=contrainte)

            r = np.sqrt(r2) + 1e-6
            g = gradient(r) * valide / (r * self.rho0)
            gx, gy = g * dx, g * dy
            somme = gx.sum(1) ** 2 + gy.sum(1) ** 2
            carres = (gx * gx + gy * gy).sum(1)
            lam = -contrainte / (somme + carres + RELACHE)

            # la pression anti-grumeaux : nulle a bonne distance, negative des
            # que deux points se rapprochent trop
            corr = -TENSION * (w / self.wdq) ** PUISSANCE

            poussee = (lam[:, None] + lam[idx] + corr) * np.float32(DETENTE)
            self.p[:, 0] += (poussee * gx).sum(1)
            self.p[:, 1] += (poussee * gy).sum(1)
            self.bords(self.p)

        np.subtract(self.p, self.x, out=self.v)
        self.v /= np.float32(dt)

        # XSPH : chaque point prend un peu de la vitesse moyenne de ses
        # voisins. Sans ca l'eau est nerveuse -- chaque point garde sa vitesse
        # propre et la surface grouille.
        #
        # On reutilise le noyau de la derniere passe de correction au lieu de
        # le recalculer : les points ont bouge d'un centieme de rayon depuis,
        # et ce calcul-la coutait 2 ms sur 12.
        total = w.sum(1) + 1e-6
        self.v[:, 0] += VISCO * ((self.v[idx, 0] - self.v[:, 0:1]) * w).sum(1) / total
        self.v[:, 1] += VISCO * ((self.v[idx, 1] - self.v[:, 1:2]) * w).sum(1) / total

        np.copyto(self.x, self.p)

    def bords(self, p):
        """Le bassin. Un point qui sort est simplement remis dedans.

        On ne touche pas a sa vitesse : elle est recalculee a la fin comme
        (p - x) / dt, donc un point plaque contre un mur perd de lui-meme sa
        vitesse perpendiculaire. Le mur est parfaitement mou -- ce qui est a
        peu pres ce que fait de l'eau contre du beton.
        """
        np.clip(p[:, 0], MUR, BX - MUR, out=p[:, 0])
        np.clip(p[:, 1], MUR, BY - MUR, out=p[:, 1])

    def compression(self):
        """L'ecart de densite, en pour-cent. C'est le juge de la methode."""
        vois = self.voisins
        valide = vois >= 0
        idx = np.where(valide, vois, 0)
        dx = self.p[idx, 0] - self.p[:, 0:1]
        dy = self.p[idx, 1] - self.p[:, 1:2]
        rho = (poids(dx * dx + dy * dy) * valide).sum(1)
        return float(np.abs(rho / self.rho0 - 1.0).mean() * 100.0)


# ---------------------------------------------------------------- l'image

class Vue:
    """Les points deviennent une densite, la densite devient de l'eau.

    On ne dessine jamais les points. Chacun depose un petit tas sur une grille
    de 180 x 320, et c'est cette grille qu'on colore : epais au fond, clair sur
    les bords, blanc la ou il n'y a presque rien -- c'est-a-dire l'ecume et les
    gouttes. Le fluide n'a pas de surface dans le calcul ; il en a une a
    l'image, et c'est la meme chose qu'une ligne de niveau.
    """

    L, HH = int(BX), int(BY)
    ETALE = 2.10                # la largeur de la tache d'un point, en cases
    PORTEE = 4                  # elle est coupee a quatre cases : 81 depots

    def __init__(self, n):
        self.pixels = np.empty((self.L, self.HH, 3), np.uint8)
        self.petite = pygame.Surface((self.L, self.HH))
        self.couleurs = self.palette()
        # La tache d'un point : une gaussienne coupee a trois cases. Elle doit
        # etre plus large que l'espacement des points (2,4 cases), sinon on
        # voit les points un par un au lieu de voir de l'eau.
        d = np.arange(-self.PORTEE, self.PORTEE + 1)
        dx, dy = np.meshgrid(d, d, indexing='ij')
        w = np.exp(-(dx * dx + dy * dy) / (2.0 * self.ETALE ** 2))
        w *= ESPACE * ESPACE / w.sum()     # un fluide au repos donne 1,0 par case
        self.decale = (dx * self.HH + dy).ravel().astype(np.int32)
        # Les 49 depots se font en un seul comptage : 49 bincount separes
        # coutent 20 ms, un seul en coute 0,6 -- c'est le tableau de 57 600
        # cases qu'il faut remettre a zero a chaque fois, pas le comptage.
        self.mise = np.repeat(w.ravel().astype(np.float64), n)

    def palette(self):
        d = np.zeros((256, 3), np.float32)
        x = np.linspace(0.0, 1.6, 256)
        for c in range(3):
            d[:, c] = np.interp(x, [0.0, SEUIL * 0.55, SEUIL, SEUIL + 0.22,
                                    0.68, 1.6],
                                [BASSIN[c], BASSIN[c], ECUME[c], CLAIRE[c],
                                 PROFOND[c], PROFOND[c]])
        return d.astype(np.uint8)

    def dessiner(self, eau, ecran):
        ix = np.clip(eau.x[:, 0], self.PORTEE, self.L - 1 - self.PORTEE
                     ).astype(np.int32)
        iy = np.clip(eau.x[:, 1], self.PORTEE, self.HH - 1 - self.PORTEE
                     ).astype(np.int32)
        base = ix * self.HH + iy
        dens = np.bincount(
            np.clip((base[None, :] + self.decale[:, None]).ravel(),
                    0, self.L * self.HH - 1),
            weights=self.mise, minlength=self.L * self.HH)

        idx = np.clip(dens * (255.0 / 1.6), 0, 255).astype(np.uint8)
        np.take(self.couleurs, idx.reshape(self.L, self.HH), axis=0,
                out=self.pixels)
        pygame.surfarray.blit_array(self.petite, self.pixels)
        pygame.transform.smoothscale(self.petite, ecran.get_size(), ecran)


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
    fenetre = ouvrir("de l'eau")
    horloge = pygame.time.Clock()
    eau = Eau(np.random.randint(1, 10_000_000))
    vue = Vue(eau.n)

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    eau = Eau(np.random.randint(1, 10_000_000))

        horloge.tick(FPS)
        eau.avancer(PAS)
        vue.dessiner(eau, fenetre)
        pygame.display.flip()


if __name__ == "__main__":
    sys.exit(main())
