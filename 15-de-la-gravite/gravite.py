# -*- coding: utf-8 -*-
"""
gravite.py  --  Six cents points, une seule loi, et un systeme apparait.

Il n'y a pas de soleil dans ce programme. Pas de centre, pas d'orbites
prevues, pas une seule ellipse dessinee. Il y a un nuage de points qui ne
savent rien faire d'autre que s'attirer :

                    m
    a  =  G . --------------
              (r^2 + e^2)^1.5

Chaque point attire chaque autre point. Six cents points, donc 360 000
attractions a calculer -- vingt et un millions par seconde. C'est le seul
calcul du programme, et il occupe la moitie du temps de chaque image.

Le reste vient tout seul, et c'est ca qui vaut le coup d'oeil :

  -  le nuage tombe sur lui-meme. Il n'a pas de raison de faire autrement.
  -  en tombant il tourne plus vite -- le moment angulaire se conserve, comme
     la patineuse qui ramene les bras. Personne n'a programme cette
     acceleration : elle est une consequence.
  -  ce qui tombe droit finit au centre et y reste. Ce qui tournait assez vite
     rate le centre, remonte, redescend : ca orbite.
  -  au bout d'une minute il reste un coeur dense et un disque autour. On
     appelle ca un systeme.

La couleur ne dit qu'une chose : la vitesse. Bleu sombre pour les lents des
bords, blanc pour les rapides du centre. C'est la troisieme loi de Kepler,
affichee sans l'avoir ecrite nulle part.

    python gravite.py

    ESPACE : un autre nuage     ECHAP : quitte
"""

import sys

import numpy as np
import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
FPS = 60

# On dessine dans une image deux fois plus petite, puis on l'agrandit : quatre
# fois moins de pixels, et le flou de l'agrandissement fait les halos.
L, H = LARGEUR // 2, HAUTEUR // 2

NB = 600                # les corps. Le cout va comme le carre : voir le README
G = 240.0               # la constante de gravitation, dans nos unites a nous
MASSE = 1.0
ADOUCI = 5.0            # e : sans lui, deux corps qui se croisent partent a l'infini

RAYON = 145.0           # le nuage de depart
EPAISSEUR = 1.00        # son aplatissement. En 2D on le voit de face : rond
ROTATION = 0.80         # la part de la vitesse qu'il faudrait pour tenir en l'air
DESORDRE = 0.16         # ce qu'on ajoute de vitesse au hasard

PAS = 1 / 60.0          # le pas de calcul. Plus fin ne change rien : voir README
T_NUAGE = 2.5           # le temps qu'on laisse au nuage avant d'allumer

TRAINEE = 0.970         # ce qui reste de l'image precedente : c'est l'orbite
ZOOM = 1.20             # le cadrage : le nuage de depart tient juste dans la largeur
ECLAT = 0.90            # la force du tone-mapping
VITE = 55.0             # la vitesse a partir de laquelle un corps est blanc

# Du plus lent au plus rapide. C'est la seule table du programme.
FROID = [
    (0.00, (26, 38, 92)), (0.22, (54, 96, 180)), (0.45, (120, 176, 235)),
    (0.70, (226, 226, 240)), (1.00, (255, 246, 214)),
]
ENCRE = (150, 146, 156)
CANAUX = np.arange(3)


# ------------------------------------------------------------ la geometrie

def palette(table, n=256):
    seuils = [s for s, _ in table]
    d = np.empty((n, 3), np.float32)
    x = np.linspace(0.0, 1.0, n)
    for c in range(3):
        d[:, c] = np.interp(x, seuils, [t[1][c] for t in table])
    return d


def nuage(alea, n):
    """Un nuage plein, sans entassement au centre.

    Tirer un rayon au hasard entre 0 et R entasse les points au milieu : il y a
    beaucoup plus de place dans la couronne exterieure que dans le disque du
    centre. On tire donc la racine, et la densite devient egale partout.
    """
    r = RAYON * np.sqrt(alea.random(n))
    a = alea.uniform(0.0, 2.0 * np.pi, n)
    p = np.stack([r * np.cos(a), r * np.sin(a) * EPAISSEUR], 1)
    return p.astype(np.float32)


# --------------------------------------------------------------- le systeme

class Systeme:
    """Six cents corps, et les tampons ou se calcule leur attraction.

    Les six matrices (600 x 600) sont reservees une fois pour toutes. Ecrit
    naturellement -- `r2 = dx*dx + dy*dy + e2` -- numpy en reserverait six
    nouvelles a chaque appel, soit 8,6 Mo par image : 15 ms au lieu de 7,6.
    """

    def __init__(self, graine):
        alea = np.random.RandomState(graine)
        self.pos = nuage(alea, NB)
        self.masse = np.full(NB, MASSE, np.float32)

        # Le nuage tourne, mais pas assez pour se tenir : il va tomber *en*
        # tournant. C'est tout ce qu'il faut pour obtenir un disque plutot
        # qu'un tas.
        r = np.hypot(self.pos[:, 0], self.pos[:, 1]) + 1.0
        tenir = np.sqrt(G * MASSE * NB * r / (r * r + RAYON * RAYON) ** 1.5 * r)
        self.vit = np.stack([-self.pos[:, 1] / r, self.pos[:, 0] / r], 1) * \
            (tenir * ROTATION)[:, None]
        self.vit += alea.standard_normal((NB, 2)).astype(np.float32) * \
            (tenir.mean() * DESORDRE)
        self.vit = self.vit.astype(np.float32)

        # Le desordre qu'on vient d'ajouter ne tombe jamais juste : il reste
        # une vitesse d'ensemble, et comme rien d'exterieur ne s'y oppose, tout
        # le nuage s'en va en ligne droite. Mesure sans ces deux lignes : le
        # centre avait glisse de 33 pixels au bout de 45 s, et le systeme
        # quittait le cadre par le bord. On enleve donc la moyenne -- ce qui
        # revient a regarder depuis le nuage, et non depuis la fenetre.
        self.vit -= self.vit.mean(0)
        self.pos -= self.pos.mean(0)

        n = NB
        self.dx = np.empty((n, n), np.float32)
        self.dy = np.empty((n, n), np.float32)
        self.r2 = np.empty((n, n), np.float32)
        self.tmp = np.empty((n, n), np.float32)
        self.acc = np.zeros((n, 2), np.float32)
        self.e2 = np.float32(ADOUCI * ADOUCI)
        self.temps = 0.0
        self._forces()

    def _forces(self):
        """L'attraction de tous sur tous. C'est tout le programme."""
        x = self.pos[:, 0]
        y = self.pos[:, 1]
        dx, dy, r2, tmp = self.dx, self.dy, self.r2, self.tmp
        np.subtract(x[None, :], x[:, None], out=dx)
        np.subtract(y[None, :], y[:, None], out=dy)
        np.multiply(dx, dx, out=r2)
        np.multiply(dy, dy, out=tmp)
        np.add(r2, tmp, out=r2)
        np.add(r2, self.e2, out=r2)
        np.sqrt(r2, out=tmp)                      # tmp = r
        np.multiply(r2, tmp, out=r2)              # r2  = r^3
        np.divide(self.masse[None, :], r2, out=r2)
        np.fill_diagonal(r2, 0.0)                 # un corps ne s'attire pas
        np.multiply(dx, r2, out=dx)
        np.multiply(dy, r2, out=dy)
        self.acc[:, 0] = dx.sum(1)
        self.acc[:, 1] = dy.sum(1)
        self.acc *= np.float32(G)

    def avancer(self, dt):
        """Saute-mouton : un demi-coup de pied, un pas, un demi-coup de pied.

        Ce qui compte ici n'est pas le choix d'une methode savante, c'est
        l'ordre de deux lignes. Bouger la position avec l'*ancienne* vitesse --

            x += v*dt ; v += a*dt        (Euler explicite)

        -- fabrique de l'energie a chaque pas : +54 % au bout de 40 secondes,
        mesure. Le nuage ne tombe pas, il gonfle. Mettre a jour la vitesse
        d'abord suffit deja a tout sauver (-0,02 %), et la mettre a jour a
        cheval sur le pas, comme ici, tient a -0,003 %.

        C'est pour ca que le programme peut se permettre un pas aussi gros
        qu'une image : ce n'est pas la finesse du pas qui tient le systeme,
        c'est sa symetrie.
        """
        d = np.float32(dt * 0.5)
        self.vit += self.acc * d
        self.pos += self.vit * np.float32(dt)
        self._forces()
        self.vit += self.acc * d
        self.temps += dt

    def energie(self):
        """Cinetique + potentielle. Doit rester constante : c'est le juge."""
        c = 0.5 * float((self.masse * (self.vit ** 2).sum(1)).sum())
        x, y = self.pos[:, 0], self.pos[:, 1]
        dx = x[None, :] - x[:, None]
        dy = y[None, :] - y[:, None]
        r = np.sqrt(dx * dx + dy * dy + self.e2)
        p = -G * MASSE * MASSE * np.triu(1.0 / r, 1).sum()
        return c + float(p)


# --------------------------------------------------------------- l'image

class Vue:
    """Les corps, leur trainee, et le tone-mapping. Rien d'autre n'est dessine."""

    def __init__(self):
        self.toile = np.zeros((H * L, 3), np.float32)
        self.plat = self.toile.reshape(-1)
        self.tampon = np.empty((H, L, 3), np.float32)
        self.feu = palette(FROID)

    def dessiner(self, s, dt, zoom, eclat=1.0):
        self.toile *= np.float32(TRAINEE)
        x = (L * 0.5 + s.pos[:, 0] * zoom).astype(np.int32)
        y = (H * 0.46 + s.pos[:, 1] * zoom).astype(np.int32)
        vu = (x >= 0) & (x < L) & (y >= 0) & (y < H)
        if not vu.any():
            return
        v = np.hypot(s.vit[vu, 0], s.vit[vu, 1]) * np.float32(1.0 / VITE)
        teinte = self.feu[np.clip(v * 255.0, 0, 255).astype(np.int32)]
        # L'energie deposee est proportionnelle a dt : un corps brille par
        # seconde, pas par image. Sinon la trainee change avec le nombre
        # d'images par seconde, et l'orbite n'a plus la meme epaisseur.
        force = np.float32(dt * FPS * eclat / 255.0)
        plat = (y[vu] * L + x[vu]).astype(np.intp)
        idx = (plat[:, None] * 3 + CANAUX).ravel()
        np.add.at(self.plat, idx, (teinte * force).ravel())

    def image(self, sortie):
        t = self.tampon
        np.multiply(self.toile.reshape(H, L, 3), np.float32(-ECLAT), out=t)
        np.exp(t, out=t)
        np.subtract(np.float32(1.0), t, out=t)
        np.multiply(t, np.float32(255.0), out=t)
        np.copyto(sortie, t.transpose(1, 0, 2), casting="unsafe")


# --------------------------------------------------------------- la fenetre

def ouvrir(titre):
    """Une fenetre 9:16 qui tient sur l'ecran, comme partout dans ce dossier."""
    pygame.init()
    pygame.display.set_caption(titre)
    haut = HAUTEUR
    if "--plein" not in sys.argv:
        haut = max(420, min(HAUTEUR, int(pygame.display.Info().current_h * 0.88)))
    return pygame.display.set_mode((max(2, round(haut * LARGEUR / HAUTEUR)), haut))


def main():
    fenetre = ouvrir("de la gravite")
    large, haut = fenetre.get_size()
    horloge = pygame.time.Clock()

    petite = pygame.Surface((L, H))
    pixels = np.empty((L, H, 3), np.uint8)
    vue = Vue()
    chemin = pygame.font.match_font("consolas") or pygame.font.match_font("segoeui")
    police = pygame.font.Font(chemin, max(11, round(26 * large / LARGEUR)))
    legende = police.render("%d corps" % NB, True, ENCRE)

    s = Systeme(np.random.randint(1, 10_000_000))
    t = 0.0
    reste = 0.0

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    s = Systeme(np.random.randint(1, 10_000_000))
                    vue.toile.fill(0.0)
                    t = reste = 0.0

        ecoule = min(horloge.tick(FPS) / 1000.0, 1 / 20)
        t += ecoule

        if t >= T_NUAGE:
            # Le calcul avance par pas fixes, quoi qu'il arrive a l'affichage :
            # une image en retard ne doit pas changer la physique.
            reste += ecoule
            while reste >= PAS:
                s.avancer(PAS)
                reste -= PAS
            vue.dessiner(s, ecoule, ZOOM)
        else:
            vue.dessiner(s, ecoule, ZOOM, eclat=0.55)

        vue.image(pixels)
        pygame.surfarray.blit_array(petite, pixels)
        pygame.transform.smoothscale(petite, (large, haut), fenetre)
        fenetre.blit(legende, (large // 2 - legende.get_width() // 2,
                               haut - round(66 * haut / HAUTEUR)))
        pygame.display.flip()


if __name__ == "__main__":
    sys.exit(main())
