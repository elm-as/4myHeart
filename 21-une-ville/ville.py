# -*- coding: utf-8 -*-
"""
ville.py  --  Un rectangle. On le coupe en deux, puis encore, et a la fin les
               lumieres s'allument.

Il n'y a pas de plan dans ce programme, pas de carte, pas de modele de ville. Il
y a un rectangle -- le cadre de l'image -- et une regle qu'on applique
cinquante fois :

    prends une parcelle, coupe-la en deux par une droite,
    et laisse une rue dans la coupure.

C'est tout. La largeur de la rue depend seulement de la profondeur de la
coupure : large pour les premieres, etroite pour les dernieres. Ce qui en sort
-- des avenues qui traversent, des rues qui les relient, des ruelles qui ne
menent nulle part -- n'a jamais ete decrit.

Deux choses valent le coup d'oeil dans la construction :

  -  Ce qui empeche les ilots d'etre des lanieres, ce n'est pas la direction de
     la coupe -- c'est **l'endroit**. On coupe toujours pres du milieu (entre
     34 et 66 % de la largeur). Autoriser 8 a 92 % fait passer la proportion de
     lanieres de 2 % a 23 %. Choisir la direction en travers du plus long cote,
     au contraire, ne change presque rien : 1,9 % contre 3,5 %. Je croyais
     l'inverse avant de mesurer.
  -  Toutes les parcelles restent **convexes**. C'est automatique : couper un
     convexe par une droite donne deux convexes. Et un convexe, on sait le
     retrecir sans rien calculer -- on repousse chacun de ses cotes vers
     l'interieur. C'est ce qui donne les trottoirs, et les cours interieures.

Puis on decoupe chaque ilot en immeubles, chaque immeuble en fenetres, et on
allume.

La nuit tombe en trois temps
----------------------------
Les rues se dessinent, les immeubles sortent, puis les fenetres s'allument --
une a une, de plus en plus vite, puis de moins en moins. C'est une courbe en
cloche, et c'est la seule chose de ce fichier qui soit une mise en scene.

    python ville.py

    ESPACE : une autre ville     ECHAP : quitte
"""

import sys

import numpy as np
import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
FPS = 60

MARGE = 14                      # le bord de la ville
PROFOND = 7                     # le nombre de coupures successives
RUES = [20, 13, 9, 7, 5, 4, 3]  # la largeur de la rue, par profondeur
AIRE_MIN = 2600                 # au-dessous, on ne coupe plus : c'est un ilot
BIAIS = 0.20                    # la chance qu'une coupure parte de travers
PENCHE = 0.13                   # le desordre de l'angle, en radians

TROTTOIR = 2.6                  # entre la rue et le premier mur
LOTS = 2100                     # l'aire visee d'un immeuble
COUR = 1.7                      # l'espace entre deux immeubles

FENETRE = 7.0                   # la distance entre deux fenetres
BORD_MUR = 3.0                  # la marge entre une fenetre et le bord du toit
VIDE = 0.12                     # la part d'immeubles qui restent eteints
OCCUPE = (0.22, 0.92)           # la part de fenetres allumees, immeuble par immeuble

# --- le deroule, en secondes
T_NUIT = 1.5
T_RUES = 6.5                    # les rues se dessinent
T_MURS = 7.5                    # les immeubles sortent
T_LUMIERE = 19.0                # les fenetres s'allument
T_FIN = 5.0

# --- couleurs
NUIT = (9, 10, 13)
ASPHALTE = (30, 31, 37)         # les rues
IMMEUBLE = (20, 21, 26)         # les toits
CRETE = (37, 38, 46)            # le bord des toits, cote lumiere
CHAUDE = (255, 186, 96)         # la plupart des fenetres
FROIDE = (150, 196, 255)        # une sur six : un ecran, un neon
LAMPE = (255, 150, 60)          # les lampadaires
PART_FROIDE = 0.17


# ------------------------------------------------------- geometrie convexe

def aire(poly):
    x, y = poly[:, 0], poly[:, 1]
    return 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


def couper(poly, n, d):
    """Garde la part de la parcelle du cote ou n.p <= d. (Sutherland-Hodgman)

    Un polygone convexe coupe par une droite donne un polygone convexe : c'est
    ce qui permet de tout faire avec cette seule fonction -- les rues, les
    trottoirs, les cours, les lots.
    """
    s = poly @ n - d
    dedans = s <= 0.0
    if dedans.all():
        return poly
    if not dedans.any():
        return None
    sortie = []
    for i in range(len(poly)):
        j = (i + 1) % len(poly)
        if dedans[i]:
            sortie.append(poly[i])
        if dedans[i] != dedans[j]:
            t = s[i] / (s[i] - s[j])
            sortie.append(poly[i] + t * (poly[j] - poly[i]))
    return np.array(sortie, np.float32) if len(sortie) >= 3 else None


def retrecir(poly, marge):
    """Repousse chaque cote vers l'interieur. Ne marche que sur un convexe --
    et tout est convexe ici."""
    out = poly
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        e = b - a
        n = np.array([e[1], -e[0]], np.float32)
        longueur = float(np.hypot(n[0], n[1]))
        if longueur < 1e-6:
            continue
        n /= longueur
        out = couper(out, n, float(n @ a) - marge)
        if out is None or len(out) < 3:
            return None
    return out


def corde(poly, n, d):
    """Les deux points ou la droite n.p = d traverse la parcelle : c'est le
    trait de la rue qu'on vient d'ouvrir."""
    s = poly @ n - d
    pts = []
    for i in range(len(poly)):
        j = (i + 1) % len(poly)
        if (s[i] <= 0) != (s[j] <= 0):
            t = s[i] / (s[i] - s[j])
            pts.append(poly[i] + t * (poly[j] - poly[i]))
    return pts[:2]


# ---------------------------------------------------------------- la ville

class Ville:
    """Le plan : les rues, les immeubles, les fenetres. Tout est calcule au
    demarrage ; l'animation ne fait que devoiler dans l'ordre."""

    def __init__(self, graine):
        self.alea = np.random.RandomState(graine)
        self.rues = []          # (a, b, largeur, profondeur)
        self.ilots = []
        depart = np.array([[MARGE, MARGE], [LARGEUR - MARGE, MARGE],
                           [LARGEUR - MARGE, HAUTEUR - MARGE],
                           [MARGE, HAUTEUR - MARGE]], np.float32)
        self.diviser(depart, 0)
        self.rues.sort(key=lambda r: r[3])

        self.immeubles = []
        for ilot in self.ilots:
            self.batir(ilot)
        # du centre vers les bords : les immeubles sortent en tache d'huile
        centre = np.array([LARGEUR * 0.5, HAUTEUR * 0.47])
        self.immeubles.sort(
            key=lambda b: float(np.hypot(*(b[0].mean(0) - centre))))

        self.fenetres = []
        for poly, _ in self.immeubles:
            # Chaque immeuble a son taux d'occupation, et un sur huit reste
            # noir. C'est ce qui evite le quadrillage parfait : une ville ou
            # toutes les fenetres sont allumees ne ressemble a rien.
            if self.alea.random_sample() < VIDE:
                continue
            self.percer(poly, self.alea.uniform(*OCCUPE))
        self.alea.shuffle(self.fenetres)

        self.lampes = []
        for a, b, large, prof in self.rues:
            if prof <= 1:
                self.eclairer(a, b, large)

    # -- les rues ----------------------------------------------------------

    def diviser(self, poly, prof):
        if prof >= PROFOND or aire(poly) < AIRE_MIN:
            self.ilots.append(poly)
            return
        # en travers du plus long cote : c'est ce qui fait des pates de
        # maisons plutot que des lanieres
        mini, maxi = poly.min(0), poly.max(0)
        taille = maxi - mini
        angle = 0.0 if taille[0] >= taille[1] else np.pi / 2
        if self.alea.random_sample() < BIAIS:
            angle = self.alea.uniform(0, np.pi)
        angle += self.alea.uniform(-PENCHE, PENCHE)
        n = np.array([np.cos(angle), np.sin(angle)], np.float32)

        # on coupe pres du milieu, mais pas au milieu
        proj = poly @ n
        bas, haut = float(proj.min()), float(proj.max())
        d = bas + (haut - bas) * self.alea.uniform(0.34, 0.66)

        large = RUES[min(prof, len(RUES) - 1)]
        pts = corde(poly, n, d)
        if len(pts) == 2:
            self.rues.append((pts[0], pts[1], large, prof))

        for part in (couper(poly, n, d - large * 0.5),
                     couper(poly, -n, -(d + large * 0.5))):
            if part is not None and len(part) >= 3 and aire(part) > 40:
                self.diviser(part, prof + 1)

    # -- les immeubles -----------------------------------------------------

    def batir(self, ilot):
        """Un ilot devient un ou plusieurs immeubles : on le retrecit du
        trottoir, puis on le recoupe tant qu'il est trop grand."""
        terrain = retrecir(ilot, TROTTOIR)
        if terrain is None:
            return
        a_traiter, lots = [terrain], []
        while a_traiter:
            p = a_traiter.pop()
            if aire(p) <= LOTS:
                lots.append(p)
                continue
            mini, maxi = p.min(0), p.max(0)
            t = maxi - mini
            angle = 0.0 if t[0] >= t[1] else np.pi / 2
            angle += self.alea.uniform(-0.10, 0.10)
            n = np.array([np.cos(angle), np.sin(angle)], np.float32)
            proj = p @ n
            bas, haut = float(proj.min()), float(proj.max())
            d = bas + (haut - bas) * self.alea.uniform(0.38, 0.62)
            morceaux = [q for q in (couper(p, n, d - COUR),
                                    couper(p, -n, -(d + COUR)))
                        if q is not None and len(q) >= 3 and aire(q) > 300]
            # si la coupe n'a pas donne deux morceaux valables, on garde le lot
            # entier : c'est un grand immeuble, et ca arrive en vrai aussi
            a_traiter.extend(morceaux) if len(morceaux) == 2 else lots.append(p)

        for lot in lots:
            if aire(lot) > 260:
                # la hauteur ne se voit pas d'en haut : elle sert seulement a
                # eclairer le bord du toit, et a decider du nombre de fenetres
                self.immeubles.append((lot, self.alea.uniform(0.25, 1.0)))

    def percer(self, poly, occupe):
        """Les fenetres : une grille reguliere, puis on jette celles qui
        tombent hors des murs."""
        mini, maxi = poly.min(0), poly.max(0)
        if (maxi - mini).min() < 2 * BORD_MUR + 2:
            return
        xs = np.arange(mini[0] + BORD_MUR, maxi[0] - BORD_MUR, FENETRE)
        ys = np.arange(mini[1] + BORD_MUR, maxi[1] - BORD_MUR, FENETRE)
        if not len(xs) or not len(ys):
            return
        grille = np.stack(np.meshgrid(xs, ys, indexing='ij'), -1).reshape(-1, 2)
        grille += self.alea.uniform(-0.8, 0.8, grille.shape)
        interieur = retrecir(poly, BORD_MUR)
        if interieur is None:
            return
        tirage = self.alea.random_sample(len(grille))
        for p, t in zip(grille, tirage):
            if t < occupe and self.dedans(interieur, p):
                self.fenetres.append((p, self.alea.random_sample() < PART_FROIDE))

    @staticmethod
    def dedans(poly, p):
        """Toutes les parcelles tournent dans le meme sens -- elles descendent
        toutes du meme rectangle -- donc un seul signe suffit."""
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            e, q = b - a, p - a
            if e[0] * q[1] - e[1] * q[0] < 0.0:
                return False
        return True

    def eclairer(self, a, b, large):
        """Des lampadaires le long des avenues, tous les quarante pixels."""
        d = b - a
        longueur = float(np.hypot(d[0], d[1]))
        if longueur < 60:
            return
        u = d / longueur
        cote = np.array([-u[1], u[0]], np.float32) * (large * 0.5 + 1.5)
        for s in np.arange(30, longueur - 20, 42.0):
            for signe in (1, -1):
                self.lampes.append(a + u * s + cote * signe)


# ---------------------------------------------------------------- l'image

def halo(rayon, couleur, force=1.0):
    """Un petit disque flou, pre-calcule une fois : c'est la lueur d'une
    lumiere. On le pose en addition, donc deux lueurs qui se croisent
    s'additionnent, comme de la vraie lumiere."""
    d = np.arange(-rayon, rayon + 1, dtype=np.float32)
    x, y = np.meshgrid(d, d, indexing='ij')
    g = np.exp(-(x * x + y * y) / (2.0 * (rayon / 2.4) ** 2)) * force
    img = np.multiply.outer(g, np.array(couleur, np.float32))
    s = pygame.Surface((2 * rayon + 1, 2 * rayon + 1))
    pygame.surfarray.blit_array(s, np.clip(img, 0, 255).astype(np.uint8))
    return s


class Vue:
    """Trois calques qui ne font que grandir, et qu'on ne redessine jamais."""

    def __init__(self):
        self.plan = pygame.Surface((LARGEUR, HAUTEUR)).convert()
        self.plan.fill(NUIT)
        self.lumiere = pygame.Surface((LARGEUR, HAUTEUR)).convert()
        self.lumiere.fill((0, 0, 0))
        self.cadre = pygame.Surface((LARGEUR, HAUTEUR)).convert()
        self.halos = {
            'chaude': halo(6, CHAUDE, 0.30),
            'froide': halo(6, FROIDE, 0.26),
            'lampe': halo(11, LAMPE, 0.34),
        }

    def rue(self, a, b, large):
        pygame.draw.line(self.plan, ASPHALTE,
                         (float(a[0]), float(a[1])), (float(b[0]), float(b[1])),
                         max(1, int(round(large))))

    def immeuble(self, poly, hauteur):
        pts = [(float(p[0]), float(p[1])) for p in poly]
        pygame.draw.polygon(self.plan, IMMEUBLE, pts)
        # le liseré clair sur deux cotes : de loin, ca suffit a faire du relief
        couleur = tuple(int(IMMEUBLE[i] + (CRETE[i] - IMMEUBLE[i]) * hauteur)
                        for i in range(3))
        pygame.draw.lines(self.plan, couleur, True, pts, 1)

    def allumer(self, p, froide):
        h = self.halos['froide' if froide else 'chaude']
        r = h.get_width() // 2
        self.lumiere.blit(h, (int(p[0]) - r, int(p[1]) - r),
                          special_flags=pygame.BLEND_ADD)
        self.lumiere.set_at((int(p[0]), int(p[1])),
                            FROIDE if froide else CHAUDE)

    def lampe(self, p):
        h = self.halos['lampe']
        r = h.get_width() // 2
        self.lumiere.blit(h, (int(p[0]) - r, int(p[1]) - r),
                          special_flags=pygame.BLEND_ADD)

    def dessiner(self, ecran):
        cible = ecran if ecran.get_size() == (LARGEUR, HAUTEUR) else self.cadre
        cible.blit(self.plan, (0, 0))
        cible.blit(self.lumiere, (0, 0), special_flags=pygame.BLEND_ADD)
        if cible is not ecran:
            pygame.transform.smoothscale(cible, ecran.get_size(), ecran)


# ---------------------------------------------------------------- la fenetre

def ouvrir(titre):
    """Une fenetre 9:16 qui tient sur l'ecran, comme partout dans ce dossier."""
    pygame.init()
    pygame.display.set_caption(titre)
    haut = HAUTEUR
    if "--plein" not in sys.argv:
        haut = max(420, min(HAUTEUR, int(pygame.display.Info().current_h * 0.88)))
    return pygame.display.set_mode((max(2, round(haut * LARGEUR / HAUTEUR)), haut))


def cloche(u):
    """La courbe d'allumage : lente, puis vite, puis lente. C'est une ville qui
    rentre du travail."""
    return u * u * (3.0 - 2.0 * u)


def main():
    fenetre = ouvrir("une ville")
    horloge = pygame.time.Clock()

    def naitre():
        v = Ville(np.random.randint(1, 10_000_000))
        return v, Vue(), 0.0, [0, 0, 0, 0]

    ville, vue, t, fait = naitre()

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    ville, vue, t, fait = naitre()

        t += min(horloge.tick(FPS) / 1000.0, 1 / 20)

        # 1. les rues, des avenues aux ruelles
        u = np.clip((t - T_NUIT) / T_RUES, 0.0, 1.0)
        cible = int(cloche(u) * len(ville.rues))
        while fait[0] < cible:
            a, b, large, _ = ville.rues[fait[0]]
            vue.rue(a, b, large)
            fait[0] += 1

        # 2. les immeubles, du centre vers les bords
        u = np.clip((t - T_NUIT - T_RUES * 0.75) / T_MURS, 0.0, 1.0)
        cible = int(cloche(u) * len(ville.immeubles))
        while fait[1] < cible:
            poly, hauteur = ville.immeubles[fait[1]]
            vue.immeuble(poly, hauteur)
            fait[1] += 1

        # 3. les lampadaires, puis les fenetres
        debut = T_NUIT + T_RUES * 0.75 + T_MURS * 0.7
        u = np.clip((t - debut) / (T_LUMIERE * 0.35), 0.0, 1.0)
        cible = int(cloche(u) * len(ville.lampes))
        while fait[2] < cible:
            vue.lampe(ville.lampes[fait[2]])
            fait[2] += 1

        u = np.clip((t - debut) / T_LUMIERE, 0.0, 1.0)
        cible = int(cloche(u) * len(ville.fenetres))
        while fait[3] < cible:
            p, froide = ville.fenetres[fait[3]]
            vue.allumer(p, froide)
            fait[3] += 1

        vue.dessiner(fenetre)
        pygame.display.flip()

        if t > debut + T_LUMIERE + T_FIN:
            ville, vue, t, fait = naitre()


if __name__ == "__main__":
    sys.exit(main())
