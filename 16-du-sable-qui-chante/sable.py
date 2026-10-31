# -*- coding: utf-8 -*-
"""
sable.py  --  Quatre-vingt mille grains, une plaque, et une frequence qui monte.

Une plaque carree, du sable dessus, un archet -- ou un haut-parleur -- en
dessous. La plaque se met a vibrer. Le grain ne tient nulle part, sauf la ou
la plaque ne bouge pas. Il finit donc par dessiner, tout seul, les endroits
immobiles.

Ces endroits ont une equation. Pour une plaque carree libre, la forme qui
vibre a la frequence choisie est une somme de deux ondes croisees :

    w(x, y) = cos(n.pi.x).cos(m.pi.y)  +/-  cos(m.pi.x).cos(n.pi.y)

Les lignes ou w = 0 sont les lignes nodales : la plaque y est immobile. Elles
ne sont dessinees nulle part dans ce programme. Aucun trait n'est trace. Ce
sont quatre-vingt mille grains qui les trouvent.

Chaque grain, a chaque image, ne fait qu'une chose :

  -  il regarde de combien la plaque bouge sous lui (|w|) ;
  -  plus ca bouge, plus il a de chances d'etre ejecte. S'il l'est, il retombe
     un peu au hasard, et un peu plus bas dans la pente -- vers le calme ;
  -  la ou la plaque ne bouge pas, il ne repart jamais. Il est arrive.

Deux lignes de physique. Le reste -- les croix, les grilles, les anneaux, les
fleurs -- n'est jamais demande. Change la frequence, et la figure entiere se
refait ailleurs en une seconde et demie.

Le nombre affiche en haut est la frequence. Elle monte tout au long : chaque
palier est un mode de la plaque, et chaque mode a son dessin.

    python sable.py

    ESPACE : on redisperse le sable     ECHAP : quitte
"""

import bisect
import sys

import numpy as np
import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
FPS = 60

COTE = 660              # le cote de la plaque, en pixels. C'est aussi la grille
X0 = (LARGEUR - COTE) // 2
Y0 = 430                # la plaque est basse : la frequence occupe le haut

NB = 80_000             # les grains

# Les modes, dans l'ordre ou on les joue. (n, m, signe) : le signe choisit
# laquelle des deux ondes croisees on soustrait, et ca change tout le dessin.
# Ils sont ranges par n^2 + m^2 croissant -- c'est-a-dire par frequence.
MODES = [
    (1, 2, -1), (1, 3, +1), (2, 3, +1), (1, 4, +1), (2, 4, +1),
    (3, 4, +1), (1, 5, +1), (2, 5, -1), (3, 5, +1), (1, 6, +1),
    (2, 6, +1), (3, 6, +1), (4, 6, +1),
]
F0 = 24.0               # la frequence d'un mode vaut F0 x (n^2 + m^2)

T_SILENCE = 2.0         # le sable, immobile, avant que ca commence
T_PREMIER = 5.0         # le premier palier : le sable part de partout, il lui faut le temps
T_MODE = 3.4            # les suivants : ~1,5 s pour se refaire, ~2 s pour respirer
T_ROULE = 0.50          # le temps que met le nombre a monter jusqu'au palier suivant

# l'instant ou commence chaque palier
DEBUTS = [T_SILENCE]
for _i in range(len(MODES)):
    DEBUTS.append(DEBUTS[-1] + (T_PREMIER if _i == 0 else T_MODE))

SEUIL = 0.10            # au-dela, le grain risque de decoller. Voir le README
PENTE = 1.00            # ce qui descend vers le calme -- c'est lui qui fait les lignes
BRUIT = 8.00            # ce qui part au hasard -- c'est lui qui donne son grain au trait

FOND = (9, 9, 11)               # autour de la plaque
PLAQUE = (23, 22, 25)           # la plaque au repos
ONDE = (11, 12, 18)             # ce qu'on ajoute la ou elle vibre : a peine bleu
LUEUR = 1.00                    # la force de ce bleu. 0 = plaque parfaitement plate
SABLE = (236, 223, 192)         # la couleur du grain
ECLAT = 0.42                    # l'opacite d'un grain seul dans son pixel
ENCRE = (150, 146, 156)


# ---------------------------------------------------------------- la plaque

class Plaque:
    """La forme qui vibre, et tout ce qu'on en deduit une fois pour toutes.

    Les grains lisent |w| et sa pente des milliers de fois par seconde. Les
    recalculer par grain couterait quatre cosinus a chaque fois ; on les
    calcule une seule fois par mode, sur la grille des pixels, et les grains
    n'ont plus qu'a lire la case sous eux.

    Les trois nombres qu'un grain lit -- l'amplitude et les deux pentes -- sont
    ranges cote a cote dans un seul tableau `champ[ix, iy, :]`. Les chercher
    dans trois tableaux separes coute trois fois plus cher : ce n'est pas le
    calcul qui compte a ce nombre de grains, c'est le nombre d'allers-retours
    en memoire.

    Tout est range en x d'abord -- `a[ix, iy]` -- et pas en lignes comme
    d'habitude. C'est l'ordre qu'attend pygame : ca evite une transposee de
    1,3 million de nombres a chaque image.
    """

    def __init__(self):
        self.u = ((np.arange(COTE, dtype=np.float32) + 0.5) / COTE) * np.pi
        # a plat : un grain donne son pixel en un seul indice, pas deux
        self.champ = np.zeros((COTE * COTE, 3), np.float32)
        self.grille = self.champ.reshape(COTE, COTE, 3)
        self.fond = np.empty((COTE, COTE, 3), np.uint8)
        self.accorder(*MODES[0])

    def accorder(self, n, m, signe):
        """Prendre la forme du mode (n, m). C'est le seul calcul lourd, et il
        n'arrive qu'une fois par palier -- douze fois dans toute la video."""
        a, b = np.cos(n * self.u), np.cos(m * self.u)
        w = np.outer(a, b) + signe * np.outer(b, a)
        np.abs(w, out=w)
        w /= max(float(w.max()), 1e-6)
        amp = w.astype(np.float32)

        # La pente de |w| pointe vers les ventres ; le grain la descend. Elle
        # a un angle vif sur la ligne nodale -- c'est exactement ce qu'on veut :
        # de chaque cote, elle renvoie vers la ligne.
        gx, gy = np.gradient(amp)
        norme = np.sqrt(gx * gx + gy * gy) + np.float32(1e-5)
        self.grille[:, :, 0] = amp
        self.grille[:, :, 1] = gx / norme
        self.grille[:, :, 2] = gy / norme

        fond = np.multiply.outer(amp, np.array(ONDE, np.float32) * np.float32(LUEUR))
        fond += np.array(PLAQUE, np.float32)
        np.copyto(self.fond, fond, casting="unsafe")
        # un lisere sur le bord : on doit sentir que c'est un objet pose la
        for c in (0, COTE - 1):
            self.fond[c, :] = self.fond[:, c] = (46, 45, 49)


# ---------------------------------------------------------------- le sable

class Sable:
    """Les grains. Position seulement : un grain n'a pas de vitesse ici.

    C'est volontaire. Sur une plaque reelle, le grain est ejecte, vole, et
    retombe ailleurs -- il n'y a pas de glissement, il y a des sauts. On
    modelise donc le saut, pas la trajectoire. Et un saut, ca ne se negocie
    pas : ou le grain decolle, ou il ne decolle pas.

    Deux details, et je m'y suis repris a deux fois sur chacun :

    -  la longueur du saut est fixe. Proportionnelle a l'excitation -- ce
       qui semble plus fin -- le grain ralentit en approchant du calme et
       s'arrete *au bord* de la zone tranquille, des deux cotes : chaque ligne
       sort en double, avec un vide au milieu.
    -  le decollage est tire au sort, avec une chance qui monte avec
       l'amplitude. Avec un seuil net, le grain s'arrete la ou il franchit le
       seuil, et la ligne sort creuse : du sable sur ses deux bords, rien
       dedans. Avec un seuil au hasard, un grain mal place finit toujours par
       repartir, et ne s'arrete vraiment qu'au fond du calme.
    """

    ALEA = 1 << 20          # la reserve de hasard : 1 048 576 nombres

    def __init__(self, alea):
        self.pos = alea.uniform(1.0, COTE - 2.0, (NB, 2)).astype(np.float32)
        self.d = np.empty((NB, 2), np.float32)
        self.alea = alea
        # Il faut 240 000 nombres au hasard par image : un par grain pour le
        # decollage, deux pour la direction. Les tirer coute 2,4 ms a chaque
        # image -- 6 ms si on les veut gaussiens -- pour du bruit. On en tire
        # un million une fois pour toutes, et on pioche dedans une tranche
        # differente a chaque image : 0,00 ms.
        self.reserve = alea.random_sample(self.ALEA).astype(np.float32)

    def hasard(self, n):
        i = self.alea.randint(0, self.ALEA - n)
        return self.reserve[i:i + n]

    def cases(self):
        """Le pixel sous chaque grain, en indice a plat."""
        ix = self.pos[:, 0].astype(np.int32)
        iy = self.pos[:, 1].astype(np.int32)
        ix *= COTE
        ix += iy
        return ix

    def secouer(self, plaque, gain, dt):
        """Une image de vibration. Deux lignes de physique, le reste est du
        rangement."""
        if gain <= 0.0:
            return 0.0
        champ = plaque.champ[self.cases()]        # amplitude, pente x, pente y

        # Le grain decolle si la plaque bouge assez sous lui -- et "assez" est
        # tire au sort a chaque image, entre zero et deux fois le seuil.
        saute = champ[:, 0] > self.hasard(NB) * np.float32(2.0 * SEUIL / gain)
        pas = saute.astype(np.float32)
        pas *= np.float32(dt * FPS)

        d = self.d
        np.multiply(champ[:, 1:], np.float32(-PENTE), out=d)
        d += (self.hasard(NB * 2).reshape(NB, 2) - np.float32(0.5)) * np.float32(BRUIT)
        d *= pas[:, None]
        self.pos += d

        # Le bord : la plaque a un rebord, le grain rebondit dessus. Sans lui
        # le sable tombe par terre -- ce qui est vrai, mais il n'en resterait
        # plus assez pour les douze figures.
        np.abs(self.pos, out=self.pos)
        np.subtract(np.float32(COTE - 1.001), self.pos, out=self.pos)
        np.abs(self.pos, out=self.pos)
        np.subtract(np.float32(COTE - 1.001), self.pos, out=self.pos)
        return 1.0 - float(saute.mean())


# ---------------------------------------------------------------- l'image

class Vue:
    """Densite de grains -> teinte. Il n'y a rien d'autre a dessiner.

    Le sable finit par ne couvrir que 3 a 6 % de la plaque -- 12 000 a 25 000
    pixels sur 435 600. On recopie donc la plaque telle quelle, d'un bloc
    (0,06 ms pour 1,3 Mo), et on ne peint que les pixels qui ont vraiment du
    sable dessus.

    Faire passer les 435 600 pixels par la table des teintes coute 7,0 ms a lui
    seul ; n'y faire passer que les occupes en coute 1,4. Sur l'image entiere,
    12,4 ms contre 5,1.
    """

    def __init__(self):
        self.plaque_img = np.empty((COTE, COTE, 3), np.uint8)
        self.pixels = self.plaque_img.reshape(-1, 3)
        # ce qu'on voit selon le nombre de grains tombes dans le pixel. Une
        # table de 48 entrees : au-dela c'est blanc, et ca arrive vite.
        t = 1.0 - np.exp(-np.arange(48, dtype=np.float32) * ECLAT)
        self.table = np.multiply.outer(t, np.array(SABLE, np.float32)).astype(np.uint8)

    def dessiner(self, sable, plaque):
        compte = np.bincount(sable.cases(), minlength=COTE * COTE)
        occupes = np.flatnonzero(compte)
        np.copyto(self.plaque_img, plaque.fond)
        self.pixels[occupes] = self.table[np.minimum(compte[occupes], 47)]
        return occupes.size


# ---------------------------------------------------------------- la fenetre

def ouvrir(titre):
    """Une fenetre 9:16 qui tient sur l'ecran, comme partout dans ce dossier."""
    pygame.init()
    pygame.display.set_caption(titre)
    haut = HAUTEUR
    if "--plein" not in sys.argv:
        haut = max(420, min(HAUTEUR, int(pygame.display.Info().current_h * 0.88)))
    return pygame.display.set_mode((max(2, round(haut * LARGEUR / HAUTEUR)), haut))


def frequence(i):
    n, m, _ = MODES[i]
    return F0 * (n * n + m * m)


def main():
    fenetre = ouvrir("du sable qui chante")
    large, haut = fenetre.get_size()
    horloge = pygame.time.Clock()
    ech = large / LARGEUR

    image = pygame.Surface((LARGEUR, HAUTEUR))
    image.fill(FOND)
    dessus = image.subsurface((X0, Y0, COTE, COTE))
    vue = Vue()
    plaque = Plaque()
    sable = Sable(np.random.RandomState(np.random.randint(1, 10_000_000)))

    chemin = pygame.font.match_font("consolas") or pygame.font.match_font("segoeui")
    police = pygame.font.Font(chemin, max(22, round(104 * ech)))
    petite = pygame.font.Font(chemin, max(9, round(26 * ech)))
    hz = petite.render("Hz", True, ENCRE)

    t = 0.0
    mode = -1

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    sable = Sable(np.random.RandomState(
                        np.random.randint(1, 10_000_000)))
                    t = 0.0
                    mode = -1

        dt = min(horloge.tick(FPS) / 1000.0, 1 / 20)
        t += dt

        # ou en est-on dans la montee ?
        if t < T_SILENCE:
            gain, f = 0.0, 0.0
        else:
            k = min(bisect.bisect_right(DEBUTS, t) - 1, len(MODES) - 1)
            if k != mode:
                plaque.accorder(*MODES[k])
                mode = k
            gain = 1.0
            # le nombre monte vers le palier pendant qu'on y arrive
            u = min(1.0, (t - DEBUTS[k]) / T_ROULE)
            u = u * u * (3.0 - 2.0 * u)
            avant = frequence(k - 1) if k else 0.0
            f = avant + (frequence(k) - avant) * u

        sable.secouer(plaque, gain, dt)
        vue.dessiner(sable, plaque)

        pygame.surfarray.blit_array(dessus, vue.plaque_img)
        pygame.transform.smoothscale(image, (large, haut), fenetre)

        if f > 0.0:
            txt = police.render("%d" % round(f), True, (226, 218, 200))
            x = round(large * 0.5 - (txt.get_width() + hz.get_width() * 1.6) * 0.5)
            y = round(250 * ech)
            fenetre.blit(txt, (x, y))
            fenetre.blit(hz, (x + txt.get_width() + round(hz.get_width() * 0.6),
                              y + txt.get_height() - hz.get_height() * 2))
        pygame.display.flip()


if __name__ == "__main__":
    sys.exit(main())
