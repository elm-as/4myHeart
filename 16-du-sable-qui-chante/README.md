# 16 — Du sable qui chante

**Accroche :** *Et si le son dessinait dans le sable ?*

## L'idée

Une plaque carrée, du sable dessus, un haut-parleur en dessous. La plaque
vibre. Le grain ne tient nulle part — **sauf là où la plaque ne bouge pas**.
Il finit donc par dessiner tout seul les endroits immobiles.

Ces endroits ont une équation. Pour une plaque carrée libre, la forme qui vibre
à une fréquence donnée est une somme de deux ondes croisées :

```
w(x, y) = cos(n·π·x)·cos(m·π·y)  ±  cos(m·π·x)·cos(n·π·y)
```

Les lignes où `w = 0` sont les **lignes nodales**. Elles ne sont dessinées nulle
part dans ce programme : aucun trait n'est tracé, aucune courbe n'est calculée.
Ce sont 80 000 grains qui les trouvent.

Chaque grain, à chaque image, ne fait qu'une chose :

- il regarde de combien la plaque bouge sous lui (`|w|`) ;
- plus ça bouge, plus il a de chances d'être éjecté. S'il l'est, il retombe un
  peu au hasard, et un peu plus bas dans la pente — vers le calme ;
- là où la plaque ne bouge pas, il ne repart jamais. Il est arrivé.

Deux lignes de physique. Les croix, les grilles, les anneaux, les fleurs : rien
de tout ça n'est demandé.

C'est la seule idée du dossier où **la musique ne se pose pas sur l'image, elle
la fabrique**.

## Lancer

```bash
python sable.py
```

`ESPACE` redisperse le sable et repart de zéro · `ECHAP` quitte.

## Le déroulé — et c'est ça, la vidéo

Treize paliers, rangés par fréquence croissante. Le nombre en haut monte à
chaque changement, et la figure entière se refait ailleurs en une seconde et
demie.

| Temps | Hz | Mode | Ce qu'on voit |
|---|---|---|---|
| 0 – 2 s | — | — | le sable, étalé, immobile. **Le silence.** |
| 2 – 7 s | 120 | (1,2)− | une diagonale se creuse, deux arcs aux coins |
| 7 – 10,4 s | 240 | (1,3)+ | **une croix**, avec un nœud épais au centre |
| 10,4 – 13,8 s | 312 | (2,3)+ | la diagonale revient, entourée de vagues |
| 13,8 – 17,2 s | 408 | (1,4)+ | une diagonale nette, quatre arcs autour |
| 17,2 – 20,6 s | 480 | (2,4)+ | **l'anneau**, seul au centre, dans un losange |
| 20,6 – 24 s | 600 | (3,4)+ | la diagonale s'épaissit, les vagues se serrent |
| 24 – 27,4 s | 624 | (1,5)+ | une croix fine, quatre boucles dans les coins |
| 27,4 – 30,8 s | 696 | (2,5)− | une amande barrée en diagonale |
| 30,8 – 34,2 s | 816 | (3,5)+ | **un cercle traversé par une croix** |
| 34,2 – 37,6 s | 888 | (1,6)+ | une diagonale et des boucles qui s'emboîtent |
| 37,6 – 41 s | 960 | (2,6)+ | **une grille droite, un cercle dans la case du milieu** |
| 41 – 44,4 s | 1080 | (3,6)+ | **un X, et un anneau dans chaque quartier** |
| 44,4 – 47,8 s | 1248 | (4,6)+ | **une fleur à quatre pétales.** C'est la fin |

Les trois moments à filmer sont **18,7 s**, **39 s** et **46 s** — une seconde et
demie après chaque changement, quand la figure vient de se poser : l'anneau
seul, la grille aux cercles, la fleur. Ce sont les trois qu'on reconnaît sans
savoir ce qu'on regarde.

La formation, mesurée en pixels couverts de sable — une figure qui se resserre
est une figure dont le nombre baisse :

| mode | 0,5 s | 1 s | 1,5 s | 2 s | 3 s |
|---|---|---|---|---|---|
| (1,2)− 120 Hz — *le sable part de partout* | 71 020 | 65 125 | 56 106 | 46 032 | 29 753 |
| (2,4)+ 480 Hz | 26 008 | 24 139 | 19 244 | 15 241 | 12 497 |
| (3,5)+ 816 Hz | 16 421 | 13 664 | 12 435 | 12 025 | 11 798 |
| (4,6)+ 1248 Hz | 15 938 | 13 386 | 12 385 | 11 926 | 11 230 |

Le premier palier dure 5 s et les autres 3,4 s, pour cette seule raison : la
première fois, le sable part de partout ; les fois suivantes, il part d'une
figure déjà faite. Une figure se refait en 1,5 s et met 3 s à se resserrer
complètement.

## Le détail dont je suis content : deux erreurs qui font la même tache

Le grain saute, ou ne saute pas. Toute la figure tient dans ces deux décisions,
et je me suis trompé sur les deux.

**Erreur 1 — un saut proportionnel à l'agitation.** Ça semble plus fin : plus la
plaque bouge, plus le grain est projeté loin. Sauf qu'en approchant du calme, le
grain ralentit, ralentit, et s'arrête **au bord** de la zone tranquille — des
deux côtés. Chaque ligne nodale sort en double, avec un vide au milieu.

**Erreur 2 — un seuil net.** « Au-dessus de `SEUIL`, il saute ; en dessous, il
reste. » Le grain s'arrête alors exactement là où il franchit le seuil, c'est-à-
dire sur le contour `|w| = SEUIL`. La ligne sort **creuse** : du sable sur ses
deux bords, rien dedans.

Les deux corrections tiennent en une ligne chacune :

```python
pas   = saute.astype(np.float32)                       # saut de longueur fixe
saute = amplitude > hasard(NB) * (2.0 * SEUIL)         # seuil tiré au sort
```

Le seuil tiré au sort veut dire : la chance de décoller vaut `|w| / 2·SEUIL`.
Un grain mal placé finit toujours par repartir ; un grain au fond du calme ne
repart jamais. C'est la seule position stable, et c'est la ligne nodale.

## L'autre détail : la largeur du trait n'est pas un réglage de dessin

Le sable ne fait pas un trait d'un pixel. Il fait une **crête**, et sa largeur
sort d'une compétition entre deux termes : `PENTE` tire le grain vers le calme,
`BRUIT` l'en écarte. Mesuré à 3 s sur le mode (2,4), en pixels couverts :

| `PENTE` \ `BRUIT` | 2 | 4 | 8 |
|---|---|---|---|
| **0,3** | 50 320 | 49 272 | 47 471 |
| **0,8** | 12 909 | 16 849 | 24 624 |
| **1,5** | 10 950 | 13 401 | 19 574 |
| **2,3** | 13 399 | 14 244 | 18 417 |

À `PENTE = 0,3` le grain ne descend plus : les 50 000 pixels ne sont pas une
crête large, c'est du sable qui n'est jamais arrivé (amplitude moyenne sous les
grains : 0,063, contre 0,004 quand ça converge). En haut à gauche du tableau, la
figure est floue ; en bas à gauche, elle est nette mais fine comme un cheveu, et
après compression vidéo elle clignote.

Le programme est réglé à `1,0 / 8,0` : une crête de 4 à 6 pixels, encore
granuleuse. On voit les grains, pas une courbe.

## Ce que ça coûte

Mesuré sur les 2 868 images de la séquence complète, en 720 × 1280 :

| | ms par image |
|---|---|
| `secouer` — 80 000 grains, un saut chacun | 5,7 |
| `dessiner` — comptage, teintes, recopie de la plaque | 5,3 |
| texte + `blit_array` | 1,8 |
| mise à l'échelle vers la fenêtre | 2,7 |
| **total** | **≈ 15,7 ms** pour un budget de 16,7 |

Médiane 15,7 ms, p95 18,8. C'est le programme le plus serré du dossier. En
`--plein`, la mise à l'échelle tombe de 2,7 à 0,5 ms — c'est la seule ligne du
tableau qui dépend de la taille de ta fenêtre, et c'est elle qui décide.

Deux optimisations font toute la différence, et aucune ne change une seule
image :

**Le hasard, tiré une fois pour toutes.** Il faut 240 000 nombres au hasard par
image : un par grain pour le décollage, deux pour la direction.

| | ms par image |
|---|---|
| `standard_normal` (gaussien) | 6,0 |
| `random_sample` (uniforme) | 2,4 |
| une tranche dans une réserve d'un million | **0,00** |

**Ne colorier que ce qui est occupé.** Le sable ne couvre que 3 à 6 % de la
plaque — 12 000 à 25 000 pixels sur 435 600. Le reste ne change pas.

| | ms par image |
|---|---|
| faire passer les 435 600 pixels par la table des teintes | 7,0 |
| recopier la plaque d'un bloc, puis peindre les occupés | **1,4** |

Sur l'image entière : 12,4 ms contre 5,1.

Et le coût va bien comme le nombre de grains, sans surprise de cache cette
fois :

| grains | `secouer` | `dessiner` | total | pixels couverts |
|---|---|---|---|---|
| 20 000 | 1,3 | 4,4 | 5,6 | 11 641 |
| 40 000 | 2,9 | 4,8 | 7,7 | 17 889 |
| **80 000** | **5,8** | **5,3** | **11,1** | **25 659** |
| 160 000 | 12,1 | 7,3 | 19,4 | 35 094 |
| 320 000 | 23,7 | 9,7 | 33,4 | 45 669 |

Doubler les grains ne double pas le dessin : ils tombent au même endroit.

## Ce qui reste imparfait

- **Aucun son n'est produit.** Le programme affiche une fréquence, il ne la joue
  pas. C'est une vidéo muette à qui on ajoute une musique au montage — et
  l'accroche promet un peu plus que ça.
- **Les fréquences sont plausibles, pas mesurées.** `f = F0 · (n² + m²)` est la
  bonne loi pour une plaque mince, mais `F0 = 24 Hz` est choisi pour que les
  nombres tombent bien. Une vraie plaque d'acier de 20 cm donnerait d'autres
  valeurs.
- **La forme de la plaque est une approximation.** `cos·cos ± cos·cos` est la
  solution de Ritz pour une plaque carrée libre, celle de tous les livres. La
  vraie solution des bords libres en diffère de quelques pour cent — assez pour
  déplacer une ligne de deux ou trois pixels, pas assez pour changer la figure.
- **Le sable ne s'empile pas.** On est en 2D vu de dessus : une crête de sable
  est une densité, pas un volume. Sur une vraie plaque, la crête déborde quand
  il y a trop de sable, et s'élargit. Ici elle sature en blanc.
- **Le sable ne tombe jamais de la plaque.** Le bord renvoie les grains vers
  l'intérieur. C'est faux — une vraie plaque en perd à chaque changement — mais
  après douze figures il n'en resterait plus assez pour la douzième. 0,6 % des
  grains traînent contre le rebord.

## À bricoler

Tous les chiffres ci-dessous sont mesurés, pas devinés.

| Ligne | Effet |
|---|---|
| `MODES` | les douze figures, et leur ordre. Le signe compte autant que `n` et `m` : `(2,4)+1` et `(2,4)-1` n'ont rien à voir |
| `F0` | l'échelle des fréquences affichées. Ne change rien au dessin, seulement au nombre |
| `NB` | 80 000 grains. Deux fois plus coûte deux fois plus cher et ne couvre que 37 % de pixels en plus |
| `SEUIL` | l'amplitude à partir de laquelle le grain risque de décoller. Plus haut, la figure se fait plus vite et plus large ; plus bas, elle se fige avant d'être finie |
| `PENTE` | ce qui tire vers le calme. **C'est le réglage qui décide si la figure est nette ou floue** — voir le tableau plus haut |
| `BRUIT` | ce qui écarte au hasard. C'est lui qui donne son grain au trait |
| `T_MODE` | 3,4 s par palier. En dessous de 2 s, la figure n'a pas fini de se faire quand la suivante arrive |
| `T_PREMIER` | 5 s : le premier palier part de sable étalé partout, il lui faut plus de temps |
| `ECLAT` | l'opacité d'un grain seul. Plus bas, seules les crêtes denses se voient |
| `LUEUR` | la lueur bleue qui montre où la plaque vibre. À `0`, la plaque est parfaitement noire et on ne voit plus que le sable — plus photographique, moins explicatif |
| `COTE` | 660 px. C'est à la fois la taille de la plaque à l'écran et la finesse de la grille |
