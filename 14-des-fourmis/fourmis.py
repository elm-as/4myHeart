# -*- coding: utf-8 -*-
"""
fourmis.py  --  Des fourmis cherchent a manger, et les routes se dessinent.

Aucune fourmi ne sait ou est la nourriture. Aucune ne sait ou sont les autres.
Il n'y a pas de chef, pas de plan, pas de carte. Chacune ne fait que trois
choses, et toujours les memes :

    1. elle renifle devant elle -- trois points, gauche, centre, droite
    2. elle tourne vers le plus odorant, et avance
    3. elle laisse derriere elle l'odeur de la ou elle vient

C'est tout. La troisieme ligne est la seule qui compte vraiment, parce qu'elle
transforme le sol en memoire : une fourmi qui rentre chargee laisse l'odeur
*nourriture*, et la suivante n'a plus qu'a la suivre. Plus elles sont
nombreuses a passer, plus ca sent, plus elles passent.

Le sol, lui, oublie. L'odeur s'evapore et se repand un peu. Une piste qui ne
sert plus disparait en une dizaine de secondes -- et c'est *l'oubli* qui rend
les routes nettes : sans lui, tout le sol finirait par sentir pareil, et plus
personne ne saurait ou aller.

Il y a donc deux odeurs, jamais melangees :

    bleu   l'odeur du nid        -- deposee par celles qui cherchent encore
    vert   l'odeur de la table   -- deposee par celles qui rentrent chargees

Au debut l'ecran est bleu et brouille : tout le monde cherche. Puis un filament
vert apparait, un seul, entre le nid et le premier tas. Puis il epaissit. Puis
les autres tas sont trouves. A la fin il n'y a plus que quelques routes, nettes,
et les tas s'eteignent un par un a mesure qu'ils sont vides.

    python fourmis.py

    ESPACE : une autre colonie     ECHAP : quitte
"""

import sys

import numpy as np
import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
FPS = 60

# Tout -- le sol, les fourmis, l'image -- vit en demi-resolution. C'est quatre
# fois moins de cases a faire evaporer a chaque image, et l'agrandissement final
# fait exactement le flou qu'on veut sur une trace d'odeur.
L, H = LARGEUR // 2, HAUTEUR // 2

NB = 1200               # les fourmis
VITESSE = 58.0          # en cases par seconde
PORTEE = 9.0            # a quelle distance elles reniflent
ECART = 0.62            # l'angle entre le capteur central et les deux autres
VIRAGE = 7.0            # a quelle vitesse elles peuvent tourner (rad/s)
HASARD = 4.5            # ce qu'il reste d'indecision (rad/s)
COMPAS = 5.0            # le sens du nid, connu de celles qui rentrent (rad/s)

DEPOT = 46.0            # d'odeur laissee par seconde
SOUVENIR = 7.0          # en secondes : au-dela, une fourmi ne sent plus rien
EVAPORATION = 0.11      # ce qui s'efface par seconde
DIFFUSION = 0.34        # ce qui se repand sur les quatre voisines, par seconde
PLAFOND = 22.0          # au-dela, une case ne sent pas plus fort

NID = (0.50, 0.44)      # sa place, en fractions de l'ecran
RAYON_NID = 15.0
NB_TAS = 5
LOIN = (0.30, 0.44)     # la distance des tas au nid, en fractions de la hauteur
RAYON_TAS = 27.0
REPAS = 580             # combien de bouchees dans un tas

# Les couleurs, en energie : c'est le tone-mapping qui en fera des pixels.
ODEUR_NID = (0.26, 0.46, 1.00)
ODEUR_TABLE = (0.62, 1.00, 0.30)
FOURMI = (1.00, 0.94, 0.82)
CHARGEE = (1.00, 0.78, 0.24)
ECLAT = 0.60            # la force du tone-mapping
ENCRE = (150, 146, 156)


# ------------------------------------------------------------- le sol

class Sol:
    """Deux grilles d'odeur, et ce qu'il faut pour les faire vivre.

    Evaporer et diffuser, c'est six passes sur 230 000 cases, deux fois par
    image. Chacune ecrit dans un tampon reserve une fois pour toutes : la meme
    chose ecrite en `a = a * (1 - part) + voisins * k` reserverait huit
    tableaux d'un mega-octet par image, et ne tiendrait pas les 60 i/s.
    """

    def __init__(self):
        # Les deux odeurs dans un seul tableau : une fourmi ne cherche pas la
        # meme que sa voisine, et `piste[quelle, y, x]` lit les 1 200 d'un coup.
        # Deux tableaux separes obligeraient a couper la colonie en deux.
        self.piste = np.zeros((2, H, L), np.float32)
        self.bord = np.zeros((H + 2, L + 2), np.float32)
        self.tampon = np.empty((H, L), np.float32)

    def vieillir(self, dt):
        garde = np.float32(max(0.0, 1.0 - EVAPORATION * dt))
        part = np.float32(min(1.0, DIFFUSION * dt))
        quart = np.float32(part * 0.25)
        reste = np.float32(1.0 - part)
        for a in self.piste:
            v = self.tampon
            self.bord[1:-1, 1:-1] = a
            # La somme des quatre voisines, accumulee en place.
            np.add(self.bord[:-2, 1:-1], self.bord[2:, 1:-1], out=v)
            np.add(v, self.bord[1:-1, :-2], out=v)
            np.add(v, self.bord[1:-1, 2:], out=v)
            np.multiply(v, quart, out=v)
            np.multiply(a, reste * garde, out=a)
            np.add(a, v, out=a)

    def renifler(self, x, y, quelle):
        """Ce que chaque fourmi sent en (x, y), dans l'odeur qu'elle cherche."""
        xi = np.clip(x, 0, L - 1).astype(np.intp)
        yi = np.clip(y, 0, H - 1).astype(np.intp)
        return self.piste[quelle, yi, xi]


# ------------------------------------------------------------- la colonie

class Colonie:
    """Les fourmis, les tas, et le nid. Rien d'autre n'est simule."""

    def __init__(self, graine):
        alea = np.random.RandomState(graine)
        self.alea = alea
        self.sol = Sol()

        self.nid = np.array([NID[0] * L, NID[1] * H], np.float32)
        self.pos = np.repeat(self.nid[None, :], NB, 0).astype(np.float32)
        self.ang = alea.uniform(0.0, 2.0 * np.pi, NB).astype(np.float32)
        self.charge = np.zeros(NB, bool)
        # Ce qu'il reste a deposer : plein en quittant une source, puis ca
        # s'epuise. C'est ce seul nombre qui fait gagner le chemin le plus court.
        self.force = np.ones(NB, np.float32)

        # Les tas, en couronne autour du nid. Un tas juste au-dessus du nid et
        # un autre juste en dessous donneraient deux routes superposees a
        # l'ecran : on decale donc la couronne d'un demi-pas.
        pas = 2.0 * np.pi / NB_TAS
        angles = np.arange(NB_TAS) * pas + pas * 0.5
        loin = alea.uniform(LOIN[0], LOIN[1], NB_TAS) * H
        self.tas = np.stack([self.nid[0] + np.cos(angles) * loin,
                             self.nid[1] + np.sin(angles) * loin], 1).astype(np.float32)
        self.tas[:, 0] = np.clip(self.tas[:, 0], RAYON_TAS + 6, L - RAYON_TAS - 6)
        self.tas[:, 1] = np.clip(self.tas[:, 1], RAYON_TAS + 6, H - RAYON_TAS - 6)
        self.reste = np.full(NB_TAS, float(REPAS), np.float32)

        self.recolte = 0
        self.temps = 0.0

    # -- les trois lignes -------------------------------------------------

    def avancer(self, dt):
        """Renifler, tourner, avancer, deposer. Dans cet ordre, et c'est tout."""
        self.temps += dt
        cherche = ~self.charge

        # 1. Renifler. On cherche l'odeur de ce qu'on n'a pas : celle qui
        #    cherche suit la piste de la table, celle qui rentre suit celle du
        #    nid. Les deux odeurs ne se melangent donc jamais.
        quelle = np.where(cherche, 1, 0)
        gauche = self._capteur(-ECART, quelle)
        centre = self._capteur(0.0, quelle)
        droite = self._capteur(+ECART, quelle)

        # 2. Tourner vers la plus forte. Si c'est devant, ne rien changer.
        tout_droit = centre >= np.maximum(gauche, droite)
        vers = np.where(gauche > droite, -1.0, 1.0).astype(np.float32)
        vers[tout_droit] = 0.0
        self.ang += vers * np.float32(VIRAGE * dt)
        self.ang += self.alea.uniform(-HASARD, HASARD, NB).astype(np.float32) * np.float32(dt)

        # Celles qui rentrent savent en gros ou est le nid. Une vraie fourmi
        # aussi : elle compte ses pas depuis la sortie, et sait rentrer meme
        # sans piste. Ici c'est indispensable, parce que l'odeur du nid ne
        # survit pas loin du nid -- une chercheuse qui erre depuis longtemps ne
        # depose presque plus rien (voir SOUVENIR). Sans compas, une chargee
        # qui a perdu la piste tourne pour toujours : mesure sur 54 s, 759
        # fourmis sur 1 200 rentraient les bras charges sans jamais arriver, et
        # la recolte se figeait a 841.
        #
        # Il doit donc peser plus lourd que l'indecision (HASARD), sinon il ne
        # sert a rien. Ce qui s'organise tout seul a l'ecran, c'est l'aller :
        # trouver un tas qu'aucune fourmi ne connait. Le retour, lui, est guide.
        if self.charge.any():
            d = self.nid - self.pos[self.charge]
            vise = np.arctan2(d[:, 1], d[:, 0])
            ecart = (vise - self.ang[self.charge] + np.pi) % (2.0 * np.pi) - np.pi
            pas_max = np.float32(COMPAS * dt)
            self.ang[self.charge] += np.clip(ecart, -pas_max, pas_max)

        # 3. Avancer, et rebondir sur les bords.
        pas = np.float32(VITESSE * dt)
        self.pos[:, 0] += np.cos(self.ang) * pas
        self.pos[:, 1] += np.sin(self.ang) * pas
        dehors_x = (self.pos[:, 0] < 1) | (self.pos[:, 0] > L - 2)
        dehors_y = (self.pos[:, 1] < 1) | (self.pos[:, 1] > H - 2)
        self.ang[dehors_x] = np.pi - self.ang[dehors_x]
        self.ang[dehors_y] = -self.ang[dehors_y]
        np.clip(self.pos[:, 0], 1, L - 2, out=self.pos[:, 0])
        np.clip(self.pos[:, 1], 1, H - 2, out=self.pos[:, 1])

        # Une fourmi qui marche depuis longtemps laisse une trace de plus en
        # plus faible. C'est tout le mecanisme : deux chemins menent au meme
        # tas, celui qui est court est parcouru plus vite, donc marque plus
        # fort, donc suivi plus souvent, donc marque encore plus fort. Sans
        # cette ligne, un detour de trente secondes marque autant qu'une ligne
        # droite -- et on obtient de belles boucles qui ne menent nulle part.
        self.force *= np.float32(np.exp(-dt / SOUVENIR))

        self._deposer(dt)
        self._manger()

    def _capteur(self, biais, quelle):
        a = self.ang + np.float32(biais)
        return self.sol.renifler(self.pos[:, 0] + np.cos(a) * PORTEE,
                                 self.pos[:, 1] + np.sin(a) * PORTEE, quelle)

    def _deposer(self, dt):
        """Chacune laisse l'odeur de la ou elle *vient*, pas de la ou elle va.

        Comme pour la lumiere du 13, on depose une quantite par *seconde* et
        non par image : sinon la meme colonie trace des pistes deux fois plus
        fortes sur une machine qui tient 60 i/s que sur une qui en tient 30.
        """
        x = self.pos[:, 0].astype(np.intp)
        y = self.pos[:, 1].astype(np.intp)
        plat = y * L + x
        quantite = self.force * np.float32(DEPOT * dt)
        for quelle, qui in ((0, ~self.charge), (1, self.charge)):
            if qui.any():
                np.add.at(self.sol.piste[quelle].reshape(-1), plat[qui], quantite[qui])
        np.clip(self.sol.piste, 0.0, PLAFOND, out=self.sol.piste)

    def _manger(self):
        """Toucher un tas : on charge et on fait demi-tour. Toucher le nid : on pose."""
        for i in range(NB_TAS):
            if self.reste[i] <= 0.0:
                continue
            d = self.pos - self.tas[i]
            touche = (d[:, 0] ** 2 + d[:, 1] ** 2 < RAYON_TAS ** 2) & ~self.charge
            n = int(touche.sum())
            if n:
                n = min(n, int(self.reste[i]))
                ou = np.flatnonzero(touche)[:n]
                self.charge[ou] = True
                self.ang[ou] += np.pi
                self.force[ou] = 1.0
                self.reste[i] -= n

        d = self.pos - self.nid
        rentre = (d[:, 0] ** 2 + d[:, 1] ** 2 < RAYON_NID ** 2) & self.charge
        n = int(rentre.sum())
        if n:
            self.charge[rentre] = False
            self.ang[rentre] += np.pi
            self.force[rentre] = 1.0
            self.recolte += n

    def fini(self):
        return not self.reste.any() and not self.charge.any()


# --------------------------------------------------------------- l'image

class Vue:
    """Du sol et des fourmis a des pixels. Trois plans, jamais de (H, L, 3).

    Un tableau (H, L, 3) oblige a ecrire en travers de la memoire a chaque
    couleur ajoutee. Trois plans (H, L) separes restent contigus, et la seule
    transposition du programme est celle du blit, tout a la fin.
    """

    def __init__(self):
        self.plan = np.empty((3, H, L), np.float32)
        self.scratch = np.empty((H, L), np.float32)
        self.points = np.zeros((H, L), np.float32)
        self.charges = np.zeros((H, L), np.float32)
        self.disques = {}

    def disque(self, rayon):
        """Les cases d'un disque, calculees une fois par rayon entier."""
        r = int(rayon)
        if r not in self.disques:
            d = np.arange(-r, r + 1)
            dy, dx = np.meshgrid(d, d, indexing="ij")
            ou = dx * dx + dy * dy <= r * r
            self.disques[r] = (dy[ou], dx[ou])
        return self.disques[r]

    def tache(self, grille, cx, cy, rayon, force):
        dy, dx = self.disque(rayon)
        y = np.clip(int(cy) + dy, 0, H - 1)
        x = np.clip(int(cx) + dx, 0, L - 1)
        np.add.at(grille, (y, x), np.float32(force))

    def rendre(self, c, sortie):
        self.points.fill(0.0)
        self.charges.fill(0.0)
        x = c.pos[:, 0].astype(np.intp)
        y = c.pos[:, 1].astype(np.intp)
        np.add.at(self.points, (y[~c.charge], x[~c.charge]), np.float32(1.0))
        np.add.at(self.charges, (y[c.charge], x[c.charge]), np.float32(1.0))

        # Le nid respire, les tas s'eteignent a mesure qu'on les mange.
        souffle = 0.62 + 0.38 * np.sin(c.temps * 2.2) ** 2
        self.tache(self.points, c.nid[0], c.nid[1], RAYON_NID, 0.55 * souffle)
        for i in range(NB_TAS):
            part = float(c.reste[i]) / REPAS
            if part > 0.0:
                self.tache(self.charges, c.tas[i, 0], c.tas[i, 1],
                           max(3.0, RAYON_TAS * (0.35 + 0.65 * part)), 0.30 * part + 0.06)

        nid, table = c.sol.piste
        s = self.scratch
        for k in range(3):
            p = self.plan[k]
            # L'odeur de la table est montee plus fort que celle du nid, et
            # c'est du rendu, pas de la simulation : a tout instant il y a dix
            # fois plus de chercheuses que de chargees, donc dix fois plus de
            # bleu depose. A poids egal le vert -- la seule odeur qui mene
            # quelque part -- ne se voit pas.
            np.multiply(nid, np.float32(ODEUR_NID[k] * 0.13), out=p)
            np.multiply(table, np.float32(ODEUR_TABLE[k] * 0.42), out=s)
            np.add(p, s, out=p)
            np.multiply(self.points, np.float32(FOURMI[k] * 1.9), out=s)
            np.add(p, s, out=p)
            np.multiply(self.charges, np.float32(CHARGEE[k] * 2.6), out=s)
            np.add(p, s, out=p)

        # 1 - exp(-x) : ca monte vite dans le noir, ca sature en douceur.
        np.multiply(self.plan, np.float32(-ECLAT), out=self.plan)
        np.exp(self.plan, out=self.plan)
        np.subtract(np.float32(1.0), self.plan, out=self.plan)
        np.multiply(self.plan, np.float32(255.0), out=self.plan)
        np.copyto(sortie, self.plan.transpose(2, 1, 0), casting="unsafe")


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
    fenetre = ouvrir("des fourmis")
    large, haut = fenetre.get_size()
    horloge = pygame.time.Clock()

    petite = pygame.Surface((L, H))
    pixels = np.empty((L, H, 3), np.uint8)
    vue = Vue()
    chemin = pygame.font.match_font("consolas") or pygame.font.match_font("segoeui")
    police = pygame.font.Font(chemin, max(11, round(26 * large / LARGEUR)))
    legende = police.render("%d fourmis" % NB, True, ENCRE)

    colonie = Colonie(np.random.randint(1, 10_000_000))

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    colonie = Colonie(np.random.randint(1, 10_000_000))

        dt = min(horloge.tick(FPS) / 1000.0, 1 / 20)
        colonie.sol.vieillir(dt)
        colonie.avancer(dt)
        vue.rendre(colonie, pixels)

        pygame.surfarray.blit_array(petite, pixels)
        pygame.transform.smoothscale(petite, (large, haut), fenetre)
        fenetre.blit(legende, (large // 2 - legende.get_width() // 2,
                               haut - round(66 * haut / HAUTEUR)))
        pygame.display.flip()


if __name__ == "__main__":
    sys.exit(main())
