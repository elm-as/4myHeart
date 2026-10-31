# -*- coding: utf-8 -*-
"""
explosion.py  --  Une explosion, et il n'y a rien d'autre dedans que des maths.

Un point. Puis cinq mille eclats, et pas une image, pas une texture, pas un
dessin. Chaque eclat n'obeit qu'a trois lignes, toujours les memes :

    vitesse *= frottement       (l'air freine)
    vitesse += pesanteur        (tout retombe)
    position += vitesse

Le reste est de la geometrie.

La direction de depart est le seul endroit ou il faut reflechir. On ne peut pas
tirer deux angles au hasard : on obtiendrait beaucoup plus d'eclats aux poles
qu'a l'equateur, et l'explosion aurait la forme d'un sablier. Le bon tirage est
celui d'Archimede -- tirer la *hauteur* au hasard, pas la latitude -- et il
tient en trois lignes (voir `directions`).

De la, tout le reste vient tout seul :

  -  les eclats partent presque tous a la meme vitesse, donc ils sont sur une
     sphere, donc on les voit s'accumuler sur le bord : c'est l'anneau.
     Personne ne l'a dessine, c'est de la projection.
  -  ils refroidissent, donc ils passent du blanc au jaune, puis au rouge, puis
     a la braise. C'est une seule courbe de couleur, lue a l'age de l'eclat.
  -  la pesanteur finit par gagner, donc la sphere devient une pluie.

Le debut est filme au ralenti -- huit fois plus lent -- puis le temps reprend sa
vitesse. C'est une multiplication, et c'est le seul effet du programme.

    python explosion.py

    ESPACE : recommencer     ECHAP : quitter
"""

import sys

import numpy as np
import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
FPS = 60

# On accumule les eclats dans une image deux fois plus petite, puis on
# l'agrandit. C'est quatre fois moins de pixels a traiter, et le flou que ca
# donne est exactement celui qu'on veut pour du feu.
DEMI_L, DEMI_H = LARGEUR // 2, HAUTEUR // 2

NB = 50000              # les eclats
VITESSE = 260.0         # leur vitesse de depart, en pixels par seconde
DISPERSION = 0.16       # ... a laquelle on laisse un peu de jeu
COEUR = 0.08            # la part qui part moins vite, et qui remplit le centre
FROTTEMENT = 0.75       # l'air. Plus c'est haut, plus vite ca s'arrete
PESANTEUR = 26.0        # ce qui fait retomber -- faible, pour que ca flotte
PROFONDEUR = 900.0      # la distance de l'oeil : c'est elle qui donne la 3D

VIEILLIR = 0.035        # refroidissement, par seconde de film (1 = eteint)
TRAINEE = 0.92          # ce qui reste de l'image precedente -- les filaments
ECLAT = 0.85            # la force du tone-mapping : au-dela, tout est blanc
HALO = 0.30             # combien de halo on rajoute autour des eclats

# Le film
T_POINT = 2.5           # un point seul, qui respire
T_RALENTI = 3.5         # la detonation, au ralenti
T_REPRISE = 2.5         # le temps redevient normal -- puis on laisse respirer
RALENTI = 0.125         # huit fois plus lent

# La couleur d'un eclat selon son age : blanc, jaune, orange, rouge, braise.
# C'est la seule table du programme, et elle fait tout le travail.
FEU = [
    (0.00, (255, 252, 238)), (0.06, (255, 236, 168)), (0.16, (255, 186, 74)),
    (0.34, (248, 116, 30)), (0.58, (206, 52, 18)), (0.80, (104, 20, 12)),
    (1.00, (16, 5, 4)),
]
ENCRE = (150, 146, 156)
CANAUX = np.arange(3)   # sert a glisser la couleur dans l'indice du bincount


# ------------------------------------------------------------ la geometrie

def directions(alea, n):
    """n directions tirees au hasard, sans favoriser les poles.

    Le piege : tirer la latitude au hasard entasse les points aux poles, parce
    qu'un anneau de latitude est d'autant plus court qu'on monte. Archimede a
    montre que la sphere et le cylindre qui l'enveloppe ont la meme aire par
    tranche de hauteur -- il suffit donc de tirer *la hauteur* uniformement, et
    le rayon de la tranche suit.

    Trois lignes, et la sphere est parfaitement reguliere.
    """
    z = alea.uniform(-1.0, 1.0, n).astype(np.float32)
    phi = alea.uniform(0.0, 2.0 * np.pi, n).astype(np.float32)
    r = np.sqrt(1.0 - z * z).astype(np.float32)
    return np.stack([r * np.cos(phi), r * np.sin(phi), z], 1)


def palette(table, n=256):
    """La table de couleurs devenue un degrade de n teintes."""
    seuils = [s for s, _ in table]
    d = np.empty((n, 3), np.float32)
    x = np.linspace(0.0, 1.0, n)
    for c in range(3):
        d[:, c] = np.interp(x, seuils, [t[1][c] for t in table])
    return d


def flou(a, fois=2):
    """Un flou de boite, repete. Chaque passe ne lit que quatre voisins."""
    for _ in range(fois):
        p = np.pad(a, ((1, 1), (1, 1)), mode="constant")
        a = (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:] + 2.0 * a) / 6.0
    return a


# ------------------------------------------------------------- les eclats

class Explosion:
    """Cinq mille eclats, et l'image ou on les accumule."""

    def __init__(self, graine):
        alea = np.random.RandomState(graine)
        self.graine = graine

        # Presque tous a la meme vitesse : c'est ce qui fait la sphere, donc
        # l'anneau. Sauf une petite part, plus lente, qui remplit le centre.
        v = VITESSE * (1.0 + DISPERSION * alea.standard_normal(NB))
        lents = alea.random(NB) < COEUR
        v[lents] *= alea.uniform(0.12, 0.45, int(lents.sum()))

        self.pos = np.zeros((NB, 3), np.float32)
        self.vit = (directions(alea, NB) * v[:, None]).astype(np.float32)

        # Chaque eclat vieillit a son propre rythme : sans cela ils changent
        # tous de couleur exactement ensemble, et ca se voit.
        self.rythme = alea.uniform(0.50, 2.20, NB).astype(np.float32)
        self.age = np.zeros(NB, np.float32)
        self.brille = alea.uniform(0.55, 1.0, NB).astype(np.float32)

        self.feu = palette(FEU)
        self.toile = np.zeros((DEMI_H * DEMI_L, 3), np.float32)
        self.suite = self.toile.reshape(-1)          # la meme, vue a plat
        self.tampon = np.empty((DEMI_H, DEMI_L, 3), np.float32)
        self.temps = 0.0

    def avancer(self, dt, dt_film):
        """Les trois lignes. C'est toute la physique du programme.

        Deux temps entrent ici, et c'est voulu. `dt` est le temps de la scene,
        celui que le ralenti divise par huit : il commande le mouvement, donc
        les eclats avancent au ralenti. `dt_film` est le temps du spectateur :
        il commande le refroidissement, parce qu'un eclat pali *sous nos yeux*,
        pas dans le referentiel de la simulation.

        Faire vieillir avec `dt` etait le meme piege que celui corrige dans
        `dessiner` pour la lumiere : pendant les 3,5 s de ralenti il ne
        s'ecoule que 0,44 s de scene, l'age moyen restait sous 0,07, et toute
        la detonation -- le plan le plus important du film -- sortait en blanc.
        La table FEU ne servait qu'apres la reprise.
        """
        if dt > 0.0:
            self.vit *= np.float32(np.exp(-FROTTEMENT * dt))
            self.vit[:, 1] += np.float32(PESANTEUR * dt)
            self.pos += self.vit * np.float32(dt)
            self.temps += dt
        self.age += self.rythme * np.float32(dt_film * VIEILLIR)

    def dessiner(self, dt):
        """Projette les eclats, et les ajoute a l'image.

        L'energie deposee est proportionnelle a `dt` : un eclat brille *par
        seconde*, pas par image. Sans cela, le ralenti empile huit fois plus de
        lumiere au meme endroit qu'au temps normal, et la detonation devient un
        disque blanc ou l'on ne voit plus rien -- ni l'anneau, ni la couleur.
        """
        self.toile *= np.float32(TRAINEE)

        # La perspective : plus c'est loin, plus c'est petit et pale.
        z = self.pos[:, 2] + PROFONDEUR
        k = PROFONDEUR / np.maximum(z, 60.0)
        x = (DEMI_L * 0.5 + self.pos[:, 0] * k * 0.5).astype(np.int32)
        y = (DEMI_H * 0.46 + self.pos[:, 1] * k * 0.5).astype(np.int32)

        vu = ((z > 60.0) & (x >= 0) & (x < DEMI_L)
              & (y >= 0) & (y < DEMI_H) & (self.age < 1.0))
        if not vu.any():
            return

        teinte = self.feu[np.clip(self.age[vu] * 255.0, 0, 255).astype(np.int32)]
        # Un eclat proche brille plus fort, et s'eteint en vieillissant.
        force = (self.brille[vu] * k[vu] * (1.0 - self.age[vu]) ** 1.6
                 * np.float32(dt * FPS)).astype(np.float32)

        # On ajoute chaque eclat la ou il tombe. `np.add.at` ecrit directement
        # dans le tampon ; `np.bincount`, qui ferait la meme chose, commencerait
        # par se reserver et mettre a zero 5,5 Mo a chaque image -- soit 5 ms
        # contre 0,2. Le canal est glisse dans l'indice (pixel x 3 + canal).
        plat = (y[vu] * DEMI_L + x[vu]).astype(np.intp)
        idx = (plat[:, None] * 3 + CANAUX).ravel()
        vals = (teinte * (force[:, None] * np.float32(1.0 / 255.0))).ravel()
        np.add.at(self.suite, idx, vals)

    def image(self, sortie):
        """De l'energie accumulee a des pixels : halo, puis tone-mapping.

        Tout passe par `self.tampon`, reserve une fois : a chaque image on
        traite 691 200 nombres, et le moindre tableau intermediaire se paie.
        """
        v = self.toile.reshape(DEMI_H, DEMI_L, 3)
        t = self.tampon

        # Le halo est calcule en quart de resolution, puis reetire : personne
        # ne voit la difference sur une tache floue, et c'est quatre fois moins
        # de pixels a flouter.
        np.multiply(v, np.float32(-ECLAT), out=t)
        if HALO > 0.0:
            halo = np.repeat(np.repeat(flou(v[::2, ::2].sum(2), 3), 2, 0), 2, 1)
            # On met le halo a l'echelle *sur place*, puis on l'ajoute par
            # diffusion : ecrire `t -= halo[:, :, None] * k` reserverait au
            # passage un tableau de 691 200 nombres, et c'est 7 ms par image.
            np.multiply(halo, np.float32(-ECLAT * HALO * 0.5), out=halo)
            np.add(t, halo[:, :, None], out=t)

        # 1 - exp(-x) : ca monte vite dans le noir, ca sature en douceur dans
        # les hautes lumieres. C'est ce qui empeche le coeur de faire une tache.
        np.exp(t, out=t)
        np.subtract(np.float32(1.0), t, out=t)
        np.multiply(t, np.float32(255.0), out=t)
        np.copyto(sortie, t.transpose(1, 0, 2), casting="unsafe")


# --------------------------------------------------------------- la fenetre

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


def vitesse_du_temps(t):
    """Le ralenti, puis la reprise. Une multiplication, rien de plus."""
    if t < T_POINT:
        return 0.0
    if t < T_POINT + T_RALENTI:
        return RALENTI
    part = min((t - T_POINT - T_RALENTI) / T_REPRISE, 1.0)
    return RALENTI + (1.0 - RALENTI) * part * part


def point_qui_respire(toile, t):
    """Avant la detonation : un seul point, qui bat doucement."""
    toile.fill(0)
    souffle = 0.55 + 0.45 * np.sin(t * 3.1) ** 2
    for r, a in ((26, 0.06), (14, 0.14), (7, 0.45), (3, 1.0)):
        c = int(255 * a * souffle)
        pygame.draw.circle(toile, (c, c, min(255, int(c * 1.05))),
                           (LARGEUR // 2, int(HAUTEUR * 0.46)), r)


# ------------------------------------------------------------------ le film

def main():
    fenetre = ouvrir("une explosion")
    large, haut = fenetre.get_size()
    horloge = pygame.time.Clock()

    toile = pygame.Surface((LARGEUR, HAUTEUR))       # pour le point du debut
    petite = pygame.Surface((DEMI_L, DEMI_H))
    chemin = pygame.font.match_font("consolas") or pygame.font.match_font("segoeui")
    police = pygame.font.Font(chemin, max(11, round(26 * large / LARGEUR)))
    legende = police.render("%d eclats" % NB, True, ENCRE)
    pixels = np.empty((DEMI_L, DEMI_H, 3), np.uint8)

    etat = {"t": 0.0, "feu": Explosion(np.random.randint(1, 10_000_000))}

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    etat.update(t=0.0, feu=Explosion(np.random.randint(1, 10_000_000)))

        ecoule = min(horloge.tick(FPS) / 1000.0, 1 / 20)
        etat["t"] += ecoule
        t = etat["t"]
        feu = etat["feu"]

        if t < T_POINT:
            point_qui_respire(toile, t)
            pygame.transform.smoothscale(toile, (large, haut), fenetre)
        else:
            dt = ecoule * vitesse_du_temps(t)
            feu.avancer(dt, ecoule)
            feu.dessiner(dt)
            feu.image(pixels)
            pygame.surfarray.blit_array(petite, pixels)
            # Une seule mise a l'echelle. Passer par une image 720 x 1280
            # intermediaire, comme ailleurs dans ce dossier, reviendrait ici a
            # agrandir pour reduire aussitot : 3,7 ms perdues par image, et une
            # image plus molle. La fenetre fait deja la taille du tampon.
            pygame.transform.smoothscale(petite, (large, haut), fenetre)

        fenetre.blit(legende, (large // 2 - legende.get_width() // 2,
                               haut - round(66 * haut / HAUTEUR)))
        pygame.display.flip()


if __name__ == "__main__":
    sys.exit(main())
