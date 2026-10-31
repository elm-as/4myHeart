# 07 — De la neige

**Accroche :** *Et si je faisais tomber de la neige ?*

## L'idée

Faire tomber des flocons, tout le monde sait le faire. Le sujet ici est
ailleurs : **la neige reste.**

Le sol n'est pas une image. C'est un tableau de 720 nombres — une épaisseur par
colonne de pixels. Quand un flocon touche, il ajoute un peu de matière autour de
lui, puis il disparaît. Et à chaque image, le tableau se lisse contre lui-même :

```python
neige[1:-1] = neige[1:-1] * (1 - 2*L) + L * (neige[:-2] + neige[2:])
```

Cette ligne, répétée soixante fois par seconde, est ce qui transforme des
milliers de petits tas en une congère. C'est de la **diffusion** : exactement ce
que fait la chaleur dans une barre de métal, et exactement ce que fait la neige
au vent.

## Lancer

```bash
python neige.py
```

`ESPACE` déneige tout et on recommence · `ECHAP` quitte.

## Le déroulé

| Temps | Épaisseur moyenne |
|---|---|
| 2 s | 2 px — on ne voit rien |
| 25 s | 33 px — le sol a changé de forme |
| 50 s | 83 px |
| 80 s | **147 px** (et jusqu'à 230 px dans les creux) |

C'est une vidéo **lente**. Il faut 60 à 90 secondes pour que ça vaille le coup.
Si tu veux la faire en 20 s, monte `DEPOT` à `45`.

## Filmer

Un plan fixe, long, sans coupe. Le spectateur ne doit pas remarquer que la neige
monte — il doit juste s'apercevoir, à la fin, que le paysage n'est plus le même
qu'au début. C'est exactement pour ça que ça marche.

Astuce de montage : garde la **première image** et superpose-la en fondu à la fin.

## Le détail dont je suis content

Un flocon ne se pose pas sur une colonne, il se pose **autour** — selon une
petite cloche de 27 pixels de large :

```python
CLOCHE = np.exp(-(_ecart / (ETALEMENT * 0.55)) ** 2)
CLOCHE *= DEPOT / CLOCHE.sum()
```

Sans ça, la congère ressemble à une scie : la diffusion ne rattrape jamais des
dépôts trop ponctuels. Avec ça, elle est lisse dès la première seconde. La
normalisation par `.sum()` garantit qu'un flocon dépose toujours la même
quantité de neige, quelle que soit la largeur choisie.

## À bricoler

| Ligne | Effet |
|---|---|
| `DEPOT` | la vitesse d'accumulation. **Le réglage à toucher en premier** |
| `LISSAGE` | `0.02` : la neige forme des pics. `0.4` : elle s'étale comme de l'eau |
| `VENT` | `70` et la neige part franchement de côté |
| `terrain()` | la forme du sol sous la neige — trois sinus, change-les |
| `NEIGE` | les trois teintes de la congère, du dessus vers le fond |
| `CIEL_HAUT` / `CIEL_BAS` | passe en gris clair et c'est une tempête en plein jour |
