# 13 — Une explosion

**Accroche :** *Et si une explosion était juste des maths ?*

## L'idée

Il n'y a **aucune image** dans ce programme. Pas une texture, pas un sprite, pas
un dessin de flamme. Il y a cinq mille points, et trois lignes qui leur sont
appliquées à tous, à chaque image :

```python
vitesse *= frottement       # l'air freine
vitesse += pesanteur        # tout retombe
position += vitesse
```

C'est toute la physique. Le reste est de la géométrie.

Le seul endroit où il faut réfléchir, c'est la **direction de départ**. On ne
peut pas tirer deux angles au hasard : un anneau de latitude est d'autant plus
court qu'on monte vers le pôle, donc on entasserait les éclats aux deux pôles et
l'explosion aurait la forme d'un sablier. Archimède a montré que la sphère et le
cylindre qui l'enveloppe ont la même aire par tranche de hauteur — il suffit
donc de tirer **la hauteur** uniformément, pas la latitude :

```python
z = hasard(-1, 1)
phi = hasard(0, 2*pi)
r = sqrt(1 - z*z)
```

Trois lignes, et la sphère est parfaitement régulière.

À partir de là, **tout le reste arrive tout seul, sans être dessiné** :

- les éclats partent presque tous à la même vitesse, donc ils sont sur une
  sphère, donc on les voit s'accumuler sur le bord : **c'est l'anneau.** Personne
  ne l'a tracé, c'est de la projection.
- ils refroidissent, donc ils passent du blanc au jaune, à l'orange, au rouge, à
  la braise. C'est **une seule table de sept couleurs**, lue à l'âge de l'éclat.
- la pesanteur finit par gagner, donc la sphère devient une pluie.

## Lancer

```bash
python explosion.py
```

`ESPACE` relance une autre explosion · `ECHAP` quitte.

Contrairement au monde du 12, `ESPACE` est **instantané** : il n'y a rien à
précalculer, juste cinq mille directions à retirer. Aucune image à couper au
montage.

## Le déroulé — et c'est ça, la vidéo

| Temps | Ce qu'on voit |
|---|---|
| 0 – 2,5 s | **un point seul**, qui respire. Rien d'autre à l'écran |
| 2,5 – 6 s | **la détonation, huit fois plus lente.** Blanc, puis doré |
| 6 – 8,5 s | le temps **reprend sa vitesse**, en accélérant doucement |
| 8,5 – 20 s | la boule remplit l'écran, vire à l'orange puis au rouge |
| 20 – 30 s | la pesanteur gagne : **ce n'est plus une explosion, c'est une pluie de braises** |

C'est la **seconde 2,5** qu'il faut caler sur la musique. Tout le reste du
montage en découle : c'est le seul instant net du film.

Le ralenti n'est pas un effet de post-production, c'est **une multiplication** —
la seule du programme :

```python
dt = ecoule * vitesse_du_temps(t)     # 0, puis 0,125, puis 1
```

## Le détail dont je suis content : deux temps, pas un

Un éclat a besoin de **deux horloges**, et les confondre coûte la moitié du film.

`dt` est le temps de la scène, celui que le ralenti divise par huit. Il commande
le **mouvement** : c'est bien ce qu'on veut, les éclats doivent partir au
ralenti.

Mais il ne doit surtout pas commander le **refroidissement**. Pendant les 3,5 s
de ralenti, il ne s'écoule que **0,44 s de scène**. En faisant vieillir avec
`dt`, l'âge moyen restait sous 0,07 pendant les sept premières secondes — et
comme la table de couleurs ne quitte le blanc qu'à partir de 0,10 :

| t | ancien (âge sur `dt`) | maintenant (âge sur le temps du film) |
|---|---|---|
| 4 s | blanc | blanc |
| 6 s | blanc | **jaune** |
| 9 s | blanc | orange |
| 13 s | orange | rouge |
| 40 s | orange, et les 5 000 éclats toujours allumés | noir, tout s'est éteint |

Autrement dit : **la détonation au ralenti — le plan le plus important — sortait
en noir et blanc**, et la palette de feu ne servait qu'après la reprise. Pire,
plus rien ne s'éteignait jamais : à 40 s les 5 000 éclats brillaient encore.

Un éclat pâlit **sous nos yeux**, pas dans le référentiel de la simulation. Il
vieillit donc en temps de spectateur :

```python
def avancer(self, dt, dt_film):
    ...
    self.age += self.rythme * dt_film * VIEILLIR
```

C'était exactement le même piège que celui déjà corrigé pour la lumière dans
`dessiner` — l'énergie y est déposée *par seconde*, sinon le ralenti empile huit
fois plus de lumière au même endroit et la détonation devient un disque blanc.
Le premier piège avait été vu, le second non.

Vérifié après correction : 5 000 éclats vivants à 10 s, 3 323 à 20 s, 1 527 à
30 s, 726 à 40 s, plus un seul à 60 s.

## L'autre détail : ne jamais agrandir pour réduire

Tout est accumulé dans une image **deux fois plus petite** (360 × 640), puis
étirée d'un coup jusqu'à la fenêtre. C'est quatre fois moins de pixels à
traiter, et le flou que donne l'agrandissement est exactement celui qu'on veut
pour du feu.

Le piège serait de passer par une image 720 × 1280 intermédiaire, comme le font
les autres programmes du dossier. Mesuré ici :

| Chemin | Coût par image |
|---|---|
| demi-image → fenêtre, directement | **1,03 ms** |
| demi-image → 720 × 1280 → fenêtre | 5,51 ms |

4,5 ms perdues par image pour agrandir ce qu'on va réduire aussitôt — et une
image plus molle au bout. La fenêtre fait déjà la taille du tampon.

Même logique à l'intérieur de `image()` : le halo est flouté en **quart** de
résolution avant d'être réétiré. Personne ne voit la différence sur une tache
floue, et c'est quatre fois moins de pixels.

## Ce que ça coûte

Mesuré sur 688 images, du point jusqu'à la pluie :

| | ms par image |
|---|---|
| `avancer` — les trois lignes, 5 000 éclats | 0,12 |
| `dessiner` — projection + dépôt de lumière | 1,25 |
| `image` — halo, puis tone-mapping | 9,6 |
| mise à l'échelle vers la fenêtre | 1,0 |
| **total** | **≈ 12 ms** pour un budget de 16,7 |

Médiane 10,8 ms, et **3 images sur 688** passent au-dessus du budget 60 i/s.
Le gros morceau est `image()`, et dedans, les deux tiers sont le halo.

`np.add.at` fait le dépôt des éclats. `np.bincount`, qui ferait la même chose,
commencerait par se réserver et mettre à zéro 5,5 Mo à chaque image : 5 ms
contre 0,2.

## Ce qui reste imparfait

- **La boule reste petite longtemps.** À la fin du ralenti (6 s) elle ne fait
  que 63 pixels de rayon sur 360 de large. Trois secondes et demie de film sur
  un petit objet centré : si ça te paraît long au montage, baisse `T_RALENTI`
  plutôt que d'accélérer `RALENTI`.
- **Ça déborde du cadre**, un peu : 2 % des éclats sortent à 10 s, 6,4 % à 15 s.
  C'est voulu — un cadre trop large ferait une explosion timide — mais si tu
  veux tout garder, monte `PROFONDEUR`.
- **Le plan utile s'arrête vers 28 s.** L'image ne se vide pas seulement parce
  que les éclats s'éteignent : ils sortent aussi par le bas. À 30 s il reste
  1 527 éclats vivants, mais **614 seulement sont encore dans le cadre**, et à
  34 s il n'en reste que 279. Au-delà, il n'y a plus de quoi tenir un plan.

## À bricoler

Tous les chiffres ci-dessous sont mesurés, pas devinés.

| Ligne | Effet |
|---|---|
| `NB` | 5 000 éclats. À 20 000, `dessiner` passe de 1,3 à 4 ms — ça tient encore |
| `VITESSE` | la taille de l'explosion. Le rayon final vaut `VITESSE / FROTTEMENT`, divisé par deux à l'écran |
| `DISPERSION` | `0` : une sphère parfaite, un anneau net et froid. `0.4` : un nuage, plus de bord |
| `COEUR` | la part qui part moins vite et remplit le centre. À `0`, la boule est creuse |
| `FROTTEMENT` | l'air. Plus haut, ça s'arrête plus vite et plus près |
| `PESANTEUR` | faible exprès, pour que ça flotte. Monte-le et l'explosion devient une gerbe |
| `VIEILLIR` | la vitesse de refroidissement, **par seconde de film**. C'est elle qui décide de la couleur à chaque instant |
| `TRAINEE` | ce qui reste de l'image précédente : c'est ce qui fait les filaments. `0.98` : des traits très longs |
| `ECLAT` / `HALO` | la force du tone-mapping et du halo. Au-delà de `1`, tout devient blanc |
| `T_POINT` … `RALENTI` | le minutage des trois temps du film |
| `FEU` | les sept couleurs, du blanc à la braise éteinte |
