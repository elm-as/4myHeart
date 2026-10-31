# 17 — Du feu

**Accroche :** *Et si je simulais du feu ?*

## L'idée

Pas d'images de flammes, pas de textures, pas de dégradé peint à la main. Un
champ de chaleur sur une grille de **180 × 320**, et trois règles :

1. ce qui est chaud **monte** — la poussée d'Archimède ;
2. ce qui monte **se mélange** — la turbulence ;
3. ce qui se mélange **refroidit** — et finit par disparaître.

La flamme est ce qui reste quand on laisse tourner ces trois règles.

Le sol n'est pas allumé d'un coup : il y a **trois braises**, qui rougeoient
avant de prendre. Chacune pousse un front qui avance à vitesse constante dans un
combustible irrégulier — il traîne là où ça résiste, court là où ça brûle bien.
Il faut 26 secondes pour que les trois fronts se rejoignent.

## Lancer

```bash
python feu.py
```

`ESPACE` rallume tout · `ECHAP` quitte.

## Le déroulé — et c'est ça, la vidéo

| Temps | Ce qu'on voit | Sol allumé | Hauteur de flamme |
|---|---|---|---|
| 0 – 2,6 s | **trois points rouges dans le noir.** C'est tout | 0 % | — |
| 3 s | la première braise prend : une flamme de 12 px | 0,3 % | 12 px |
| 5 – 8 s | elle monte, elle respire, les premières étincelles partent | 7 → 26 % | 104 → 220 px |
| 11 s | **deux foyers**, chacun le sien, qui avancent l'un vers l'autre | 53 % | 304 px |
| 15 – 20 s | ils se rejoignent. Ce n'est plus des feux, c'est un feu | 81 → 95 % | 392 → 456 px |
| 26 s | tout le sol brûle. Le maximum de la séquence | 100 % | **572 px** |
| 26 – 45 s | ça respire : la flamme monte, retombe, remonte | 100 % | 412 → 532 px |

La seconde à filmer est la **onzième** : deux feux séparés, chacun avec ses
étincelles, et on comprend sans un mot qu'ils vont se rejoindre.

À partir de 26 s la vidéo ne raconte plus rien de nouveau — mais elle ne se
répète pas non plus : la flamme ne repasse jamais deux fois par la même forme.
On peut laisser tourner.

## Le détail dont je suis content : un vent qui ne peut pas se comprimer

Un fluide qui n'est ni comprimé ni dilaté vérifie `div(v) = 0`. C'est la
condition qui coûte cher dans les vraies simulations de fluide : on résout une
équation de Poisson à chaque image pour projeter le champ de vitesse — une
vingtaine d'itérations sur toute la grille, et c'est le poste le plus lourd.

Ici on ne la résout pas. On écrit d'abord une **fonction de courant** `ψ(x,y,t)`,
et on prend la vitesse comme :

```
u = +∂ψ/∂y        v = −∂ψ/∂x
```

Alors `div(v) = ∂²ψ/∂x∂y − ∂²ψ/∂y∂x = 0`, exactement, sans rien calculer. Et
comme `ψ` est une somme de sinus, les dérivées sont des sinus aussi : tout le
champ de vent tient en **huit produits extérieurs** par image.

Je me suis quand même trompé du premier coup, et c'est la mesure qui l'a dit.
J'avais écrit les deux amplitudes séparément :

```python
self.u += outer(sx, cy) * (a * ky * GH * 0.15)      # faux
self.v -= outer(cx, sy) * (a * kx * GL * 0.15)      # faux : GL ≠ GH
```

`GL = 180` et `GH = 320` : les deux termes ne viennent plus de la **même**
fonction `ψ`, et la divergence revient. À l'œil, ça se voyait à peine. En la
mesurant, ça crève les yeux — il suffit de raffiner la grille et de regarder si
le résidu tend vers zéro :

| grille | divergence moyenne | version corrigée |
|---|---|---|
| 180 × 320 | 2,60 % du vent | **0,057 %** |
| 360 × 640 | 2,76 % | **0,014 %** |
| 720 × 1280 | 2,80 % | **0,0036 %** |
| 1440 × 2560 | 2,81 % | **0,0009 %** |

À gauche, ça converge vers 2,8 % : l'erreur est dans le modèle, et raffiner ne
la fera jamais partir. À droite, ça **divise par quatre à chaque fois qu'on
divise la maille par deux** — c'est la signature d'une dérivée centrée, donc il
ne reste que l'erreur de la mesure elle-même. Le champ, lui, est exact.

Et puis on l'abîme, volontairement, deux fois :

| | divergence moyenne |
|---|---|
| la fonction de courant seule | 0,005 % du vent |
| × l'atténuation dans l'air froid (l'air immobile ne doit pas tourbillonner) | 0,061 % |
| + la poussée d'Archimède (le champ complet) | 0,308 % |

La dernière ligne n'est pas un défaut : un gaz qui chauffe **se dilate** pour de
vrai. Mais autant savoir de combien.

## L'autre détail : le transport ne peut pas exploser

Chaque case regarde d'où vient l'air qu'elle reçoit — on remonte le courant d'un
pas de temps — et prend la chaleur qu'il y avait là-bas, interpolée entre quatre
cases. C'est la méthode semi-lagrangienne, et elle a une propriété qu'on ne paie
pas : la valeur obtenue est toujours **comprise entre les quatre valeurs de
départ**. Elle ne peut donc pas grandir toute seule, quel que soit le pas.

Mesuré à 20 s, en multipliant le pas de temps par quinze :

| pas de calcul | température max | hauteur de flamme |
|---|---|---|
| 1/60 s | 1,548 | 114 cases |
| 1/30 s | 1,568 | 103 cases |
| 1/10 s | 1,525 | 48 cases |
| 1/4 s | 1,506 | 40 cases |

Rien n'explose, jamais — même à un pas 15 fois trop grand. Ce qu'on perd est
ailleurs : à chaque pas on interpole, donc on lisse, et la flamme **rétrécit**.
À 1/4 de seconde il ne reste qu'un tas de braises tièdes. La stabilité est
gratuite ; la finesse, non.

## Ce que ça coûte

Mesuré sur les 2 700 images de la séquence complète :

| | ms par image |
|---|---|
| `Foyer.avancer` — vent, transport, refroidissement, sol | 3,7 |
| `Etincelles.avancer` — 900 particules | 0,4 |
| `Vue.dessiner` — palette, halo, agrandissement, étincelles | 4,7 |
| **total** | **≈ 8,9 ms** pour un budget de 16,7 |

Médiane 8,9 ms, p95 11,7, **1 image sur 1000** au-dessus du budget. Et c'est
mesuré en `--plein`, 720 × 1280 : dans une fenêtre de 356 × 633, le total tombe
à 7,9 ms.

Toute la marge vient d'un seul choix : **on n'agrandit qu'une fois, directement
à la taille de la fenêtre.** La version naturelle — fabriquer une image
720 × 1280, y ajouter un halo lui aussi en 720 × 1280, puis la réduire — fait
trois fois le travail sur 921 600 pixels :

| `Vue.dessiner` | fenêtre 356 × 633 | `--plein` 720 × 1280 |
|---|---|---|
| halo sur la grande image, puis réduction | 19,0 ms | 16,8 ms |
| **le programme** | **3,0 ms** | **5,0 ms** |

Six fois moins cher, pour une image que je n'arrive pas à distinguer de l'autre
— le halo est flou de toute façon, le fabriquer sur 57 600 pixels ou sur 921 600
donne la même tache.

## Ce qui reste imparfait

- **Ce n'est pas un solveur de fluide.** Il n'y a pas de pression, donc pas de
  vraie interaction entre la flamme et l'air qui l'entoure : le vent est décidé
  d'avance et la chaleur se contente de le suivre. Un vrai feu fabrique son
  propre tirage ; celui-ci le subit.
- **Le tirage global est un réglage, pas une conséquence.** `TIRAGE = 8` cases/s
  d'aspiration constante, et `souffle()` qui fait monter la flamme quand le
  foyer s'élargit : les deux sont des coefficients honnêtes, mais des
  coefficients. Sans eux la flamme garde la même hauteur du début à la fin, ce
  qui est faux — et surtout, ce qui ne raconte rien.
- **Le feu ne consomme rien.** Le sol allumé le reste, indéfiniment. Il faudrait
  un stock de combustible qui s'épuise pour que l'incendie finisse par
  s'éteindre derrière son propre front, comme un vrai feu de forêt.
- **Il n'y a pas de fumée.** Elle serait invisible sur fond noir — mais elle
  masquerait les étincelles, et le haut de l'image ne serait pas aussi net.
- **La flamme monte à 570 px sur 1280.** Le tiers haut de l'image reste noir
  toute la vidéo, à part les étincelles. C'est un feu vu de nuit, pas un mur de
  feu : assumé, mais ça laisse beaucoup de vide.

## À bricoler

Tous les chiffres ci-dessous sont mesurés, pas devinés.

| Ligne | Effet |
|---|---|
| `POUSSEE` | 95 cases/s à température 1. **C'est la hauteur de la flamme**, avec `REFROID` |
| `REFROID` | 0,86 par seconde. La flamme monte tant qu'elle est visible : baisse-le et elle sort du cadre, monte-le et il ne reste qu'un tapis de braises |
| `TIRAGE` | le courant d'air général. Fait monter même l'air froid — à `0`, les fumées stagnent |
| `TOURBILLONS` | les quatre termes du vent : amplitude, longueur d'onde en x, en y, dérive. **Les deux amplitudes d'un même terme doivent rester couplées** (voir plus haut), sinon le vent se comprime |
| `VENT_FROID` | la part de turbulence dans l'air froid. À `1`, tout le fond de l'image ondule alors qu'il ne s'y passe rien |
| `BRAISES` | où sont les trois braises, et quand chacune prend. C'est tout le scénario |
| `VITESSE` | 4 cases/s : le sol entier est pris à 26 s. À `8`, c'est fini en 14 s et on ne voit pas les foyers se rejoindre |
| `RESISTE` | l'irrégularité du combustible. À `0`, les fronts avancent comme des règles |
| `SOURCE` | la chaleur injectée. Au-dessus de `1,1`, la base sature en blanc et on perd tout le détail |
| `RESPIRE` | de combien le foyer bat d'un endroit à l'autre, lentement. C'est lui qui évite le mur de feu uniforme |
| `ETINCELLES` | 900. Sans elles la flamme est un dégradé qui ondule — et ça se voit que c'est un dégradé |
| `HALO` | la lueur ajoutée autour du feu. À `0`, l'image devient dure et l'on voit la grille |
| `ZOOM` | 4 : la grille fait 180 × 320. À `2` (grille 360 × 640) c'est quatre fois plus cher et beaucoup plus fin |
