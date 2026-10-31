# -*- coding: utf-8 -*-
"""
foudre.py  --  Un eclair ne sait pas ou il va. Il tatonne, et il finit par
                trouver le sol.

Personne ne dessine le zigzag. Il n'y a pas de courbe, pas de fractale ecrite a
la main, aucune forme prevue. Il y a un champ electrique, et une regle de
croissance qui tient en une ligne.

Le modele
---------
C'est le "claquage dielectrique" (Niemeyer, Pietronero et Wiesmann, 1984), le
meme modele qui sert pour les figures de Lichtenberg.

  -  Le nuage, en haut, est a potentiel 0. Le sol, en bas, est a 1.
  -  Entre les deux, l'air : le potentiel y verifie l'equation de Laplace,
     div(grad(phi)) = 0. On la resout par relaxation, en moyennant chaque case
     avec ses quatre voisines.
  -  Le canal deja forme est un conducteur : il est a 0 partout, lui aussi.
     C'est ce qui compte -- une branche qui avance **tire le potentiel avec
     elle**, et deforme tout le champ devant elle.
  -  A chaque pas, on regarde les cases libres qui touchent le canal, et on en
     allume une au hasard, avec une chance proportionnelle a

            phi ** eta          (ici eta = 3)

Voila. Le zigzag, les branches qui meurent, celles qui prennent toute la place,
le fait que ca descende sans jamais aller droit : tout ca sort de cette ligne.

L'exposant eta est le seul bouton qui compte. A 1, la decharge est grasse et
buissonnante. A 3, c'est un eclair. Plus haut, un trait presque droit.

Le retour de flamme
-------------------
Quand une branche touche le sol, on remonte les parents jusqu'au nuage : ce
chemin-la est le canal principal. C'est lui qui s'embrase -- et il s'embrase
d'un coup, en trois eclats separes de quelques centiemes de seconde, comme un
vrai eclair.

Ce qui se passe avant -- vingt secondes a tatonner dans le noir -- n'est pas une
introduction. C'est le sujet.

    python foudre.py

    ESPACE : un autre eclair     ECHAP : quitte
"""

import sys

import numpy as np
import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
FPS = 60

ZOOM = 4
GL, GH = LARGEUR // ZOOM, HAUTEUR // ZOOM     # 180 x 320
NUAGE = 6               # les lignes du haut : le nuage, conducteur
HORIZON = GH - 26       # la ligne de sol, en moyenne
RELIEF = 7              # de combien elle monte et descend

ETA = 2.5               # l'exposant. Voir le README : c'est le seul qui compte
PAR_IMAGE = 1           # cases ajoutees par image
RELAX = 8               # passes de relaxation par image
DEPART = 0.5            # ou l'eclair part, en largeur

T_NUIT = 2.0            # le noir avant que ca commence
T_APRES = 4.5           # ce qu'on laisse apres l'eclair avant de recommencer
ECLATS = [(0.00, 1.00), (0.13, 0.62), (0.28, 0.38)]   # instant, force
DECLIN = 0.22           # la duree d'un eclat, en secondes

# --- couleurs
CIEL_HAUT = (17, 19, 34)
CIEL_BAS = (6, 6, 10)
NUEE = (31, 33, 54)             # les nuages, la nuit
NUEE_VIVE = (168, 178, 214)     # les memes, eclaires par en dessous
TERRE = (3, 3, 5)
TERRE_VIVE = (56, 58, 68)
TRACEUR = (66, 80, 150)         # le canal qui cherche : a peine visible
ECLAIR = (238, 242, 255)        # le canal principal, au moment ou il part
TETE = (150, 170, 255)          # les toutes dernieres cases posees


# ---------------------------------------------------------------- le champ

class Decharge:
    """Le potentiel, le canal, et la regle qui ajoute une case.

    Le potentiel est resolu une fois au depart -- c'est un simple degrade, la
    solution exacte tant qu'il n'y a pas de canal -- puis entretenu par
    relaxation. On ne le recalcule jamais de zero : une case ajoutee ne
    derange le champ que pres d'elle, et huit passes suffisent a rattraper.
    """

    def __init__(self, graine):
        alea = np.random.RandomState(graine)
        self.alea = alea

        # le relief : une ligne d'horizon un peu accidentee
        h = alea.standard_normal(GL)
        for _ in range(14):
            h = (np.roll(h, 1) + 2.0 * h + np.roll(h, -1)) * 0.25
        h /= max(float(np.abs(h).max()), 1e-6)
        self.sol = (HORIZON - RELIEF * h).astype(np.int32)

        self.bloque = np.zeros((GL, GH), bool)      # la terre : on n'y entre pas
        for i in range(GL):
            self.bloque[i, self.sol[i]:] = True

        self.canal = np.zeros((GL, GH), bool)
        self.canal[:, :NUAGE] = True                # le nuage est un conducteur
        # Le nuage est au meme potentiel que le canal, mais il ne pousse pas :
        # sinon la decharge part aussi *le long* du nuage et on obtient un
        # peigne de petites dents sur le bord haut de l'image.
        self.pousse = np.zeros((GL, GH), bool)
        # Les cases a potentiel impose, en indices a plat : remettre le sol et
        # le canal a leur valeur apres chaque passe coute deux fois moins cher
        # avec une liste d'indices qu'avec un masque de 57 600 booleens.
        self.terre = np.flatnonzero(self.bloque.reshape(-1))
        self.fixes = []
        self.parent = np.full(GL * GH, -1, np.int32)
        self.tete = []                              # les cases posees a l'image
        self.fini = None                            # la case qui touche le sol

        # phi : 0 au nuage, 1 au sol, degrade entre les deux
        self.phi = np.zeros((GL, GH), np.float32)
        y = np.arange(GH, dtype=np.float32)
        pente = np.clip((y - NUAGE) / float(HORIZON - NUAGE), 0.0, 1.0)
        self.phi[:] = pente[None, :]
        self.phi[self.bloque] = 1.0
        self.phi[self.canal] = 0.0
        self.tampon = np.empty((GL, GH), np.float32)

        # la premiere case, sous le nuage
        self.fixes = np.zeros(0, np.int32)
        depart = int(DEPART * GL)
        self.poser(depart * GH + NUAGE, depart * GH + NUAGE - 1)

    # -- le potentiel ------------------------------------------------------

    def relaxer(self, passes):
        """Jacobi : chaque case devient la moyenne de ses quatre voisines.

        C'est la methode la plus simple qui soit, et la plus lente a converger
        globalement. Ca n'a pas d'importance ici : le champ est deja juste
        partout sauf autour de la derniere case posee, et c'est justement la
        qu'on a besoin qu'il soit juste.
        """
        p, s = self.phi, self.tampon
        for _ in range(passes):
            np.add(p[:-2, 1:-1], p[2:, 1:-1], out=s[1:-1, 1:-1])
            s[1:-1, 1:-1] += p[1:-1, :-2]
            s[1:-1, 1:-1] += p[1:-1, 2:]
            s[1:-1, 1:-1] *= 0.25
            p[1:-1, 1:-1] = s[1:-1, 1:-1]
            p[0, :] = p[1, :]                   # bords lateraux : rien ne fuit
            p[-1, :] = p[-2, :]
            p[:, :NUAGE] = 0.0
            plat = p.reshape(-1)
            plat[self.terre] = 1.0
            plat[self.fixes] = 0.0

    def residu(self):
        """De combien le champ n'est pas encore une solution de Laplace."""
        p = self.phi
        r = 0.25 * (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:])
        r = np.abs(r - p[1:-1, 1:-1])
        libre = ~(self.canal[1:-1, 1:-1] | self.bloque[1:-1, 1:-1])
        return float(r[libre].mean())

    # -- la croissance -----------------------------------------------------

    def poser(self, case, venant):
        self.parent[case] = venant
        i, j = divmod(case, GH)
        self.canal[i, j] = True
        self.pousse[i, j] = True
        self.phi[i, j] = 0.0
        self.fixes = np.append(self.fixes, np.int32(case))
        self.tete.append(case)
        if self.bloque[i, min(j + 1, GH - 1)]:
            self.fini = case

    def pousser(self):
        """Une case de plus. Toute la physique de ce fichier est ici."""
        c = self.pousse
        # les cases libres qui touchent le canal
        bord = np.zeros((GL, GH), bool)
        bord[1:, :] |= c[:-1, :]
        bord[:-1, :] |= c[1:, :]
        bord[:, 1:] |= c[:, :-1]
        bord[:, :-1] |= c[:, 1:]
        bord &= ~self.canal
        bord &= ~self.bloque
        cases = np.flatnonzero(bord.reshape(-1))
        if cases.size == 0:
            return

        # une chance proportionnelle a phi^eta
        poids = self.phi.reshape(-1)[cases]
        np.maximum(poids, 0.0, out=poids)
        poids **= np.float32(ETA)
        total = float(poids.sum())
        if total <= 0.0:
            return
        cumul = np.cumsum(poids)
        tire = self.alea.random_sample() * total
        case = int(cases[np.searchsorted(cumul, tire)])

        # De quel voisin vient-elle ? On regarde au-dessus d'abord : c'est de
        # la que vient le courant neuf fois sur dix, et ca evite des parents
        # qui remontent, donc des chemins qui font des boucles a l'affichage.
        i, j = divmod(case, GH)
        venant = -1
        for di, dj in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            a, b = i + di, j + dj
            if 0 <= a < GL and 0 <= b < GH and self.canal[a, b]:
                venant = a * GH + b
                break
        self.poser(case, venant)

    def chemin(self):
        """Du point d'impact au nuage, en remontant les parents."""
        route = []
        case = self.fini
        while case is not None and case >= 0:
            route.append(case)
            suivant = int(self.parent[case])
            case = suivant if suivant >= 0 else None
        return route

    def avancer(self):
        self.tete = []
        if self.fini is None:
            for _ in range(PAR_IMAGE):
                if self.fini is None:
                    self.pousser()
            self.relaxer(RELAX)


# ---------------------------------------------------------------- l'image

def degrade(haut, bas):
    """Le ciel : une couleur en haut, une autre en bas."""
    y = np.linspace(0.0, 1.0, HAUTEUR, dtype=np.float32)[None, :, None]
    a = np.array(haut, np.float32)[None, None, :]
    b = np.array(bas, np.float32)[None, None, :]
    return np.repeat(a + (b - a) * y, LARGEUR, 0)


def flou(source, cible, division=5):
    """Reduire puis rendre : le moyen le plus court d'obtenir un flou."""
    petit = pygame.transform.smoothscale(
        source, (LARGEUR // division, HAUTEUR // division))
    pygame.transform.smoothscale(petit, (LARGEUR, HAUTEUR), cible)


class Vue:
    """Des calques qui ne se redessinent presque jamais.

    Le canal ne fait que grandir : on ne dessine donc que les cases posees dans
    l'image -- une -- sur un calque qu'on garde. Et au moment ou ca frappe, on
    compose une bonne fois pour toutes l'image entiere de l'eclair : le ciel
    eclaire, le canal, sa lueur. Pendant la seconde que dure l'eclat, il n'y a
    plus qu'a la melanger au noir avec une opacite qui retombe.

    Sans ca, il faudrait quatre recouvrements de 921 600 pixels par image, et
    l'eclair -- le seul moment ou le programme doit absolument tenir les 60
    images par seconde -- serait le seul a ne pas y arriver.
    """

    def __init__(self, decharge):
        # .convert() : les calques prennent le format de l'ecran. Sans ca, un
        # recouvrement avec opacite peut passer par un chemin lent -- mesure a
        # 17 ms l'image sur un format qui ne tombait pas juste, contre 0,8.
        self.nuit = pygame.Surface((LARGEUR, HAUTEUR)).convert()
        self.jour = pygame.Surface((LARGEUR, HAUTEUR)).convert()
        self.trace = pygame.Surface((LARGEUR, HAUTEUR)).convert()
        self.trace.set_colorkey((0, 0, 0))
        self.plein = None
        self.paysage(decharge)

    def paysage(self, decharge):
        """Le ciel et la terre, en deux versions : de nuit, et eclaires."""
        alea = decharge.alea
        # les nuages : du bruit lisse, en haut seulement
        b = alea.standard_normal((GL, GH)).astype(np.float32)
        for _ in range(9):
            b = (np.roll(b, 1, 0) + 2 * b + np.roll(b, -1, 0)) * 0.25
            b = (np.roll(b, 1, 1) + 2 * b + np.roll(b, -1, 1)) * 0.25
        b /= max(float(np.abs(b).max()), 1e-6)
        fondu = np.clip(1.0 - np.arange(GH) / float(GH // 3), 0.0, 1.0) ** 1.4
        b = np.clip(b, 0.0, 1.0) * fondu[None, :]
        # agrandi par pygame, pas par numpy : sinon on voit les carres de 4 px
        petit = pygame.Surface((GL, GH))
        pygame.surfarray.blit_array(
            petit, (b[:, :, None] * 255.0).astype(np.uint8).repeat(3, 2))
        nuages = pygame.surfarray.array3d(
            pygame.transform.smoothscale(petit, (LARGEUR, HAUTEUR)))
        nuages = nuages[:, :, :1].astype(np.float32) / 255.0

        for cible, ciel, nuee, terre in (
                (self.nuit, (CIEL_HAUT, CIEL_BAS), NUEE, TERRE),
                (self.jour, ((80, 86, 116), (16, 17, 27)), NUEE_VIVE, TERRE_VIVE)):
            img = degrade(*ciel)
            img += nuages * np.array(nuee, np.float32)
            for x in range(LARGEUR):
                img[x, decharge.sol[x // ZOOM] * ZOOM:] = terre
            np.clip(img, 0, 255, out=img)
            pygame.surfarray.blit_array(cible, img.astype(np.uint8))

    def tracer(self, decharge):
        """Les segments nouveaux de l'image, et rien d'autre."""
        for case in decharge.tete:
            p = int(decharge.parent[case])
            if p < 0:
                continue
            i, j = divmod(case, GH)
            a, b = divmod(p, GH)
            pygame.draw.line(self.trace, TRACEUR,
                             (a * ZOOM + 2, b * ZOOM + 2),
                             (i * ZOOM + 2, j * ZOOM + 2), 2)

    def embraser(self, decharge):
        """L'image de l'eclair, composee une fois : le ciel eclaire, le canal
        principal du sol au nuage, les branches, et la lueur de tout ca."""
        eclair = pygame.Surface((LARGEUR, HAUTEUR))
        route = decharge.chemin()
        pts = [(i * ZOOM + 2, j * ZOOM + 2)
               for i, j in (divmod(c, GH) for c in route)]
        # les branches aussi s'allument : on les compte deux fois
        eclair.blit(self.trace, (0, 0), special_flags=pygame.BLEND_ADD)
        eclair.blit(self.trace, (0, 0), special_flags=pygame.BLEND_ADD)
        if len(pts) >= 2:
            pygame.draw.lines(eclair, ECLAIR, False, pts, 3)

        lueur = pygame.Surface((LARGEUR, HAUTEUR))
        flou(eclair, lueur)
        lueur.fill((160, 160, 160), special_flags=pygame.BLEND_MULT)

        self.plein = self.jour.copy()
        self.plein.blit(lueur, (0, 0), special_flags=pygame.BLEND_ADD)
        self.plein.blit(eclair, (0, 0), special_flags=pygame.BLEND_ADD)
        self.plein = self.plein.convert()

    def dessiner(self, decharge, eclat, ecran):
        ecran.blit(self.nuit, (0, 0))
        if self.plein is not None and eclat > 0.004:
            # 254 et pas 255. A 255, pygame considere le calque comme opaque
            # et prend un autre chemin de recouvrement : 20,4 ms au lieu de
            # 2,3. C'est-a-dire, tres exactement, l'image de l'eclair.
            self.plein.set_alpha(min(254, int(255 * min(1.0, eclat ** 0.75))))
            ecran.blit(self.plein, (0, 0))
        self.trace.set_alpha(70)
        ecran.blit(self.trace, (0, 0), special_flags=pygame.BLEND_ADD)


# ---------------------------------------------------------------- la fenetre

def ouvrir(titre):
    """Une fenetre 9:16 qui tient sur l'ecran, comme partout dans ce dossier."""
    pygame.init()
    pygame.display.set_caption(titre)
    haut = HAUTEUR
    if "--plein" not in sys.argv:
        haut = max(420, min(HAUTEUR, int(pygame.display.Info().current_h * 0.88)))
    return pygame.display.set_mode((max(2, round(haut * LARGEUR / HAUTEUR)), haut))


def force(depuis):
    """Les trois eclats successifs, chacun qui retombe en exponentielle."""
    f = 0.0
    for retard, amplitude in ECLATS:
        d = depuis - retard
        if d >= 0.0:
            f += amplitude * np.exp(-d / DECLIN)
    return f


def main():
    fenetre = ouvrir("de la foudre")
    large, haut = fenetre.get_size()
    horloge = pygame.time.Clock()
    plein = (large, haut) == (LARGEUR, HAUTEUR)
    image = fenetre if plein else pygame.Surface((LARGEUR, HAUTEUR))

    def naitre():
        d = Decharge(np.random.randint(1, 10_000_000))
        return d, Vue(d), 0.0, None

    decharge, vue, t, touche = naitre()

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    decharge, vue, t, touche = naitre()

        t += min(horloge.tick(FPS) / 1000.0, 1 / 20)

        if t >= T_NUIT and touche is None:
            decharge.avancer()
            vue.tracer(decharge)
            if decharge.fini is not None:
                vue.embraser(decharge)
                touche = t

        eclat = 0.0 if touche is None else force(t - touche)
        vue.dessiner(decharge, eclat, image)
        if not plein:
            pygame.transform.smoothscale(image, (large, haut), fenetre)
        pygame.display.flip()

        if touche is not None and t - touche > T_APRES:
            decharge, vue, t, touche = naitre()


if __name__ == "__main__":
    sys.exit(main())
