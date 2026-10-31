# -*- coding: utf-8 -*-
"""
monde.py  --  Un monde entier, a partir d'un seul nombre.

Il n'y a pas de carte dans ce programme. Il y a une graine -- un entier --
et six grilles de nombres au hasard, de plus en plus fines, qu'on additionne :

    relief = grille(3) + grille(6)/2 + grille(12)/4 + ... + grille(96)/32

La premiere donne les continents. La derniere, les cailloux. Les quatre du
milieu donnent tout le reste. C'est tout le terrain.

Ensuite, trois lectures du meme relief, et rien d'autre :
  -  sa hauteur donne la couleur : ocean, sable, herbe, foret, roche, neige
  -  sa pente donne l'ombre, et donc le relief qu'on croit voir
  -  sa descente donne les rivieres : on part d'un sommet et on suit toujours
     le voisin le plus bas. L'eau ne fait jamais autre chose.

Change la graine, et c'est une autre planete. Le programme, lui, est le meme.

    python monde.py

    ESPACE : un autre monde     ECHAP : quitter
"""

import math
import sys

import numpy as np
import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
FPS = 60

OCTAVES = 6
CELLULES = 3            # combien de cases pour la premiere grille, en largeur

MER = 0.38              # au-dessous, c'est de l'eau -- et c'est une part exacte
NB_RIVIERES = 130
GROSSIER = 4            # les rivieres se calculent sur une grille 4 fois plus petite
LISSAGE_RIVIERES = 4    # ... et lissee, sinon elles tombent dans le premier trou

# Le film
T_OCTAVES = 6.0         # les six grilles s'ajoutent
T_COULEUR = 3.0         # puis la couleur vient
T_RELIEF = 2.5          # puis l'ombre, et le relief apparait
T_RIVIERES = 5.0        # puis l'eau descend

# La couleur, selon l'altitude seule. Comme le relief est remis a plat par les
# rangs, chaque intervalle ci-dessous est exactement sa part de la carte :
# 26 % d'ocean profond, 12 % de haut-fond, 3,5 % de sable, et ainsi de suite.
TERRAIN = [
    (0.00, (10, 26, 54)), (0.26, (24, 58, 100)), (MER - 0.001, (52, 108, 146)),
    (MER, (208, 192, 148)), (MER + 0.035, (190, 174, 126)),
    (MER + 0.06, (96, 128, 78)), (0.63, (56, 94, 60)), (0.72, (78, 88, 64)),
    (0.82, (118, 112, 104)), (0.93, (186, 184, 180)), (1.00, (248, 250, 254)),
]
RIVIERE = (118, 176, 208)
ENCRE = (168, 174, 186)


# ------------------------------------------------------------------ le bruit

def grille(alea, cases_x, cases_y):
    """Des valeurs au hasard aux coins d'une grille, lissees entre les coins.

    C'est tout ce qu'est un "bruit" : du hasard, mais du hasard continu.
    Le lissage t*t*(3-2t) sert a ce que les pentes se raccordent, sinon on
    verrait la grille en losanges.
    """
    coins = alea.random((cases_y + 1, cases_x + 1)).astype(np.float32)

    fy = np.linspace(0, cases_y, HAUTEUR, endpoint=False, dtype=np.float32)
    fx = np.linspace(0, cases_x, LARGEUR, endpoint=False, dtype=np.float32)
    y0, x0 = fy.astype(np.int32), fx.astype(np.int32)
    ty, tx = fy - y0, fx - x0
    ty = (ty * ty * (3 - 2 * ty))[:, None]
    tx = (tx * tx * (3 - 2 * tx))[None, :]

    hg = coins[y0][:, x0]
    hd = coins[y0][:, x0 + 1]
    bg = coins[y0 + 1][:, x0]
    bd = coins[y0 + 1][:, x0 + 1]
    haut = hg + (hd - hg) * tx
    bas = bg + (bd - bg) * tx
    return haut + (bas - haut) * ty


def mettre_a_plat(a):
    """Remplace chaque altitude par son rang, ramene entre 0 et 1.

    Sans ca, chaque graine donne un monde different *en proportions* : l'une
    presque toute noyee, l'autre presque toute en neige. Avec ca, il y a
    toujours exactement 38 % d'eau et 7 % de neige -- et c'est la forme des
    continents, elle, qui change.
    """
    plat = np.empty(a.size, np.float32)
    plat[a.ravel().argsort()] = np.linspace(0, 1, a.size, dtype=np.float32)
    return plat.reshape(a.shape)


def relief(graine):
    """Les six grilles, additionnees. Rend aussi les etapes, pour le film."""
    alea = np.random.RandomState(graine)
    cumul = np.zeros((HAUTEUR, LARGEUR), np.float32)
    etapes = []
    cases = CELLULES
    force = 1.0
    for _ in range(OCTAVES):
        cumul = cumul + grille(alea, cases, max(1, round(cases * HAUTEUR / LARGEUR))) * force
        etapes.append(mettre_a_plat(cumul))
        cases *= 2
        force *= 0.5
    return etapes


def flouter(a, fois):
    for _ in range(fois):
        p = np.pad(a, 1, mode="edge")
        a = (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:] + 4.0 * a) / 8.0
    return a


# ----------------------------------------------------------------- la carte

def colorier(haut):
    couleur = np.empty((HAUTEUR, LARGEUR, 3), np.float32)
    seuils = [s for s, _ in TERRAIN]
    for c in range(3):
        couleur[:, :, c] = np.interp(haut, seuils, [t[1][c] for t in TERRAIN])
    return couleur


def pentes(haut):
    """La pente du terrain, dans les deux sens. C'est elle qui fera l'ombre."""
    dx = np.zeros_like(haut)
    dy = np.zeros_like(haut)
    dx[:, 1:-1] = (haut[:, 2:] - haut[:, :-2]) * 0.5
    dy[1:-1, :] = (haut[2:, :] - haut[:-2, :]) * 0.5
    return dx * 300.0, dy * 300.0


# -------------------------------------------------------------- les rivieres

def rivieres(haut):
    """On part d'un sommet et on va toujours vers le voisin le plus bas.

    L'eau ne fait jamais rien d'autre. Le dessin en arbre des rivieres n'est
    pas dessine : c'est ce que donne cette regle, repetee.

    Le terrain est d'abord lisse, sinon chaque riviere tombe au bout de trois
    pas dans la premiere cuvette venue et il n'en reste que des griffures.
    """
    petit = flouter(haut[::GROSSIER, ::GROSSIER], LISSAGE_RIVIERES)
    ph, pl = petit.shape
    alea = np.random.RandomState(1)

    hauts = np.argwhere(petit > MER + 0.22)
    if len(hauts) == 0:
        return []
    combien = min(NB_RIVIERES, len(hauts))
    depart = hauts[alea.choice(len(hauts), combien, replace=False)]

    voisins = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    cours = []
    for y, x in depart:
        chemin = [(int(x), int(y))]
        for _ in range(600):
            bas, ou = petit[y, x], None
            for dy, dx in voisins:
                ny, nx = y + dy, x + dx
                if 0 <= ny < ph and 0 <= nx < pl and petit[ny, nx] < bas:
                    bas, ou = petit[ny, nx], (nx, ny)
            if ou is None:               # une cuvette : la riviere s'arrete la
                break
            x, y = ou
            chemin.append((int(x), int(y)))
            if petit[y, x] < MER:        # arrivee a la mer
                break
        if len(chemin) > 12:
            cours.append([(px * GROSSIER, py * GROSSIER) for px, py in chemin])
    return cours


def tracer(calque, cours, part):
    """Dessine la part demandee de chaque riviere, de la source vers la mer."""
    calque.fill((0, 0, 0, 0))
    for chemin in cours:
        combien = int(len(chemin) * part)
        if combien < 2:
            continue
        bout = chemin[:combien]
        for i in range(1, len(bout)):
            epais = 1 + int(4.0 * i / len(chemin))
            pygame.draw.line(calque, (*RIVIERE, 235), bout[i - 1], bout[i], epais)


# ---------------------------------------------------------------- la fenetre

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


def en_surface(colonnes):
    """Un tableau (colonnes, lignes, 3) devient une image pygame."""
    s = pygame.Surface((LARGEUR, HAUTEUR))
    pygame.surfarray.blit_array(s, np.clip(colonnes, 0, 255).astype(np.uint8))
    return s


class Monde:
    """Tout ce qui ne change jamais est calcule une fois, ici.

    Les tableaux sont ranges en (colonnes, lignes) et non l'inverse : c'est
    l'ordre qu'attend pygame, et cela evite de transposer 2,7 millions de
    nombres a chaque image.
    """

    def __init__(self, graine):
        self.graine = graine
        etapes = relief(graine)
        self.haut = etapes[-1]
        self.gris = [en_surface(np.repeat(np.transpose(e)[:, :, None] * 255.0, 3, 2))
                     for e in etapes]

        self.couleur = np.ascontiguousarray(np.transpose(colorier(self.haut), (1, 0, 2)))
        self.plat = en_surface(self.couleur)

        # Les pentes sont mises a zero sur la mer, et la constante 1.9 y devient
        # 2.6, ce qui donne exactement 2.6/2.6 = 1 : la mer reste plate sans
        # qu'on ait a la retrancher image par image.
        dx, dy = pentes(self.haut)
        terre = np.ascontiguousarray((self.haut >= MER).T).astype(np.float32)
        self.dx = np.ascontiguousarray(dx.T * terre)
        self.dy = np.ascontiguousarray(dy.T * terre)
        self.base = np.where(terre > 0, np.float32(1.9), np.float32(2.6))
        self.cours = rivieres(self.haut)

        self.ombre = np.empty_like(self.dx)
        self.appoint = np.empty_like(self.dx)
        self.tampon = np.empty((LARGEUR, HAUTEUR, 3), np.float32)
        self.image = np.empty((LARGEUR, HAUTEUR, 3), np.uint8)
        self.rendu = pygame.Surface((LARGEUR, HAUTEUR))
        self.dernier = None

    def eclairer(self, angle):
        """L'image du monde sous ce soleil-la. Recalculee seulement si besoin.

        Chaque ligne ecrit dans un tampon deja reserve : a 921 600 pixels, une
        seule expression comme `dx * lx + dy * ly + 1.9` construirait quatre
        tableaux intermediaires de 3,7 Mo, et c'est cela qui coute, pas le
        calcul. Tel quel : 30 ms au lieu de 44, pour la meme image au niveau
        pres.
        """
        cle = round(angle, 2)
        if cle == self.dernier:
            return self.rendu
        self.dernier = cle

        lx, ly = np.float32(math.cos(angle)), np.float32(math.sin(angle))
        np.multiply(self.dx, lx, out=self.ombre)
        np.multiply(self.dy, ly, out=self.appoint)
        np.add(self.ombre, self.appoint, out=self.ombre)
        np.add(self.ombre, self.base, out=self.ombre)
        np.multiply(self.ombre, np.float32(1.0 / 2.6), out=self.ombre)
        np.clip(self.ombre, 0.34, 1.6, out=self.ombre)

        np.multiply(self.couleur, self.ombre[:, :, None], out=self.tampon)
        np.clip(self.tampon, 0, 255, out=self.tampon)
        np.copyto(self.image, self.tampon, casting="unsafe")
        pygame.surfarray.blit_array(self.rendu, self.image)
        return self.rendu


# ------------------------------------------------------------------ le film

def main():
    fenetre = ouvrir("un monde")
    horloge = pygame.time.Clock()

    toile = pygame.Surface((LARGEUR, HAUTEUR))
    calque = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
    chemin = pygame.font.match_font("consolas") or pygame.font.match_font("segoeui")
    police = pygame.font.Font(chemin, 26)

    etat = {"t": 0.0, "monde": Monde(np.random.randint(1, 10_000_000)), "part": -1.0}

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    etat.update(t=0.0, part=-1.0,
                                monde=Monde(np.random.randint(1, 10_000_000)))

        etat["t"] += min(horloge.tick(FPS) / 1000.0, 1 / 20)
        t = etat["t"]
        m = etat["monde"]

        if t < T_OCTAVES:
            # Les six grilles, l'une apres l'autre, en fondu.
            avance = t / T_OCTAVES * OCTAVES
            k = min(int(avance), OCTAVES - 1)
            toile.blit(m.gris[k], (0, 0))
            if k + 1 < OCTAVES:
                suivante = m.gris[k + 1]
                suivante.set_alpha(int(255 * (avance - k)))
                toile.blit(suivante, (0, 0))
                suivante.set_alpha(255)
        else:
            apres = t - T_OCTAVES
            vers_couleur = min(apres / T_COULEUR, 1.0)
            releve = min(max(apres - T_COULEUR, 0.0) / T_RELIEF, 1.0)

            if releve <= 0.0:
                toile.blit(m.gris[-1], (0, 0))
                m.plat.set_alpha(int(255 * vers_couleur))
                toile.blit(m.plat, (0, 0))
                m.plat.set_alpha(255)
            else:
                # Le soleil tourne lentement, une fois tout en place.
                angle = 2.35 + max(0.0, apres - T_COULEUR - T_RELIEF) * 0.09
                soleil = m.eclairer(angle)
                if releve < 1.0:
                    # L'ombre qui monte est un fondu entre la carte plate et la
                    # carte eclairee -- c'est exactement ce que dit le calcul,
                    # puisque couleur*(1 + (ombre-1)*f) = melange(plat, eclaire, f).
                    # Autant le laisser faire a la carte graphique : deux
                    # blits, moins de 3 ms au lieu de 30, et les 2,5 s les plus
                    # belles du film passent de 24 a 60 images par seconde.
                    toile.blit(m.plat, (0, 0))
                    soleil.set_alpha(int(255 * releve))
                    toile.blit(soleil, (0, 0))
                    soleil.set_alpha(255)
                else:
                    toile.blit(soleil, (0, 0))

            coule = min(max(apres - T_COULEUR - T_RELIEF, 0.0) / T_RIVIERES, 1.0)
            if coule > 0.0:
                if abs(coule - etat["part"]) > 0.004:
                    tracer(calque, m.cours, coule)
                    etat["part"] = coule
                toile.blit(calque, (0, 0))

        img = police.render("graine  %d" % m.graine, True, ENCRE)
        toile.blit(img, (LARGEUR // 2 - img.get_width() // 2, HAUTEUR - 66))

        pygame.transform.smoothscale(toile, fenetre.get_size(), fenetre)
        pygame.display.flip()


if __name__ == "__main__":
    sys.exit(main())
