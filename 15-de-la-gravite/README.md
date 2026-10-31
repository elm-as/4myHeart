# 15 — De la gravité

**Accroche :** *Et si je donnais la gravité à des particules ?*

## L'idée

Il n'y a **pas de soleil** dans ce programme. Pas de centre, pas d'orbite
prévue, pas une seule ellipse dessinée. Il y a six cents points qui ne savent
rien faire d'autre que s'attirer :

```
              m
a  =  G . -----------
          (r² + e²)^1.5
```

Chaque point attire chaque autre point. Six cents points, donc **360 000
attractions par image**, 21 millions par seconde. C'est le seul calcul du
programme.

Tout le reste est une conséquence, et c'est ça qui vaut le coup d'œil :

- le nuage **tombe sur lui-même**. Il n'a aucune raison de faire autrement.
- en tombant, **il tourne plus vite** — le moment angulaire se conserve, comme
  la patineuse qui ramène les bras. Personne n'a programmé cette accélération.
- ce qui tombe droit finit au centre et y reste. Ce qui tournait assez vite
  **rate le centre**, remonte, redescend : ça orbite.
- au bout de quarante secondes il y a un cœur dense et des orbites autour.
  On appelle ça un système.

La couleur ne dit qu'une chose : **la vitesse**. Bleu sombre pour les lents du
bord, blanc pour les rapides du cœur. C'est la troisième loi de Kepler, affichée
sans l'avoir écrite nulle part.

## Lancer

```bash
python gravite.py
```

`ESPACE` relance un autre nuage · `ECHAP` quitte.

## Le déroulé — et c'est ça, la vidéo

| Temps | Ce qu'on voit | Rayon de mi-masse |
|---|---|---|
| 0 – 2,5 s | le nuage, **figé**. Six cents points, rien d'autre | 101 |
| 2,5 – 8 s | la gravité s'allume : ça tourne, et ça commence à tomber | 84 |
| 8 – 18 s | **l'effondrement.** Le nuage se fragmente, des bras se forment, un cœur apparaît | 64 → 45 |
| 18 – 45 s | le cœur est blanc, le reste orbite autour. Ça ne s'arrête plus | 45 → 50 |

La seconde à filmer est la **dixième** : c'est le moment où le nuage cesse
d'être un nuage et devient une spirale, sans qu'aucune spirale n'ait été
demandée.

Mesuré sur cinq graines : rayon de mi-masse final entre 42 et 54, entre 82 et
86 % des corps encore dans le cadre à 45 s, et 45 à 77 corps définitivement
éjectés. Le plan ne s'épuise pas — au bout de trois minutes le système tourne
toujours.

## Le détail dont je suis content : l'ordre de deux lignes

Faire avancer un corps, c'est deux lignes. Et selon **l'ordre dans lequel on les
écrit**, on obtient un système qui tient une heure ou un système qui explose.

```python
x += v*dt ; v += a*dt      # la position bouge avec l'ANCIENNE vitesse
v += a*dt ; x += v*dt      # ... avec la nouvelle
```

L'énergie totale — cinétique plus potentielle — ne doit pas bouger d'un pouce :
rien n'entre, rien ne sort. C'est le juge, et il est impitoyable :

| | à 10 s | à 20 s | à 40 s |
|---|---|---|---|
| Euler explicite (ancienne vitesse) | **+35,1 %** | **+43,3 %** | **+53,8 %** |
| Euler semi-implicite (nouvelle vitesse) | −0,048 % | −0,083 % | −0,018 % |
| saute-mouton (à cheval sur le pas) | −0,004 % | −0,006 % | **−0,003 %** |

La première ligne **fabrique de l'énergie à chaque pas**. Et ça ne se voit pas
comme un bug, ça se voit comme de la mauvaise physique : le nuage ne tombe pas,
il gonfle. Son rayon de mi-masse passe à 111 puis 137, quand les deux autres
méthodes le ramènent à 45.

Le programme utilise le saute-mouton : un demi-coup de pied, un pas, un demi-coup
de pied. Et comme la stabilité vient de **la symétrie du pas et non de sa
finesse**, on peut se permettre un pas aussi gros qu'une image :

| pas de calcul | dérive à 40 s |
|---|---|
| 1/60 s (un par image) | −0,003 % |
| 1/120 s | −0,000 % |
| 1/240 s | −0,000 % |

Quatre fois plus de calcul pour gagner trois millièmes de pour cent. Le pas reste
à 1/60, et les 22 ms économisées par image sont exactement ce qui fait tenir le
programme à 60 images par seconde.

## L'autre détail : six matrices, jamais réservées deux fois

Le calcul des forces manipule des matrices 600 × 600 — chaque ligne est un
corps, chaque colonne un autre. Écrit naturellement, il en crée six à chaque
appel, soit 8,6 Mo à réserver et à jeter **soixante fois par seconde** :

| | ms par calcul |
|---|---|
| écriture naturelle (`r2 = dx*dx + dy*dy + e2`, etc.) | 7,92 |
| tampons réservés une fois, tout en `out=` | **2,42** |

Trois fois plus rapide, au résultat près — l'écart entre les deux est exactement
zéro. C'est la différence entre un programme qui tient les 60 images par seconde
et un qui n'y arrive pas.

Il y a une deuxième leçon, moins attendue. Le coût devrait aller comme le nombre
de paires, c'est-à-dire comme N². Il va **plus vite que ça** :

| corps | paires | coût | coût si c'était vraiment en N² |
|---|---|---|---|
| 300 | 90 000 | 0,42 ms | — |
| 600 | 360 000 | **2,41 ms** | 1,7 ms |
| 900 | 810 000 | 9,23 ms | 3,8 ms |
| 1 200 | 1 440 000 | 22,97 ms | 6,7 ms |

À 600 corps, les quatre matrices pèsent 5,8 Mo et tiennent encore dans le cache
du processeur. À 900 elles pèsent 13 Mo, n'y tiennent plus, et chaque opération
va rechercher ses nombres en mémoire. **C'est le cache, pas l'arithmétique, qui
fixe le nombre de corps de cette vidéo.**

## Ce que ça coûte

Mesuré sur 400 images, système en régime établi :

| | ms par image |
|---|---|
| `avancer` — le saute-mouton, dont 2,4 ms de forces | 3,0 |
| `dessiner` + `image` — traînée, palette, tone-mapping | 4,0 |
| mise à l'échelle vers la fenêtre | ~1,0 |
| **total** | **≈ 8 ms** pour un budget de 16,7 |

Médiane 6,5 ms, p95 9,2 ms, **1 image sur 400** au-dessus du budget 60 i/s.
C'est le programme le plus confortable du dossier depuis longtemps — parce que
600 corps, c'est peu à dessiner.

## Ce qui reste imparfait

- **Ce n'est pas un système solaire, c'est un amas.** Le payoff annoncé dans
  `IDEES.md` disait « nuage → orbites → système solaire » ; ce que la gravité
  produit vraiment, à partir d'un nuage sans astre central, c'est un cœur dense
  entouré d'un halo d'orbites. C'est plus proche d'un amas d'étoiles que du
  système solaire — et c'est la vérité de la simulation, pas un raté. Pour avoir
  de vraies ellipses képlériennes il faudrait poser un corps lourd au milieu dès
  le départ, donc décider à l'avance ce qu'on prétend découvrir.
- **Un corps sur huit finit éjecté.** Entre 45 et 77 selon la graine, envoyés à
  l'infini par une rencontre rapprochée. C'est de la vraie physique — les amas
  s'évaporent — mais à l'écran ce sont des traits qui partent vers les bords et
  qui ne reviennent jamais.
- **Le cœur est plus petit que le cadre.** Le nuage se contracte d'un facteur 2
  seulement, donc le système final occupe le tiers central de l'image. Le
  `ZOOM = 1.2` rattrape un peu ; au-delà, le nuage de départ ne tient plus dans
  la largeur.
- L'adoucissement `e` est ce qui empêche deux corps qui se croisent de partir à
  l'infini. C'est un mensonge nécessaire : sans lui, la force devient infinie à
  distance nulle, et aucun pas de temps ne suffit.

## À bricoler

Tous les chiffres ci-dessous sont mesurés, pas devinés.

| Ligne | Effet |
|---|---|
| `NB` | 600 corps. **Le réglage le plus cher du programme** : 900 coûte 4 fois plus, 1 200 en coûte 10 |
| `G` | la vitesse à laquelle tout se passe. L'effondrement va exactement comme `1/√G` : le nuage perd la moitié de son rayon en 5,9 s à `120`, 4,2 s à `240`, 3,0 s à `480` |
| `ADOUCI` | plus petit, des rencontres plus violentes et plus d'éjections ; plus grand, tout devient mou |
| `RAYON` | la taille du nuage de départ. Avec `ZOOM`, c'est ce qui décide du cadrage |
| `ROTATION` | ce n'est pas la taille du cœur qu'elle change, c'est la violence. `0` : effondrement droit, 72 corps éjectés et un halo qui part à 974 px. `0.4` : le plus calme, 44 éjectés. `0.8` : ça tourne en tombant. `1.2` : 85 éjectés, ça se défait |
| `DESORDRE` | le bruit de vitesse initial. C'est lui qui fait les grumeaux — donc les bras |
| `PAS` | 1/60. Le diviser par 4 ne change rien à l'énergie et coûte 4 fois plus |
| `TRAINEE` | **c'est le réglage qui dessine les orbites** — la demi-vie d'une trace. `0.90` : 0,11 s, des tirets, 8 000 pixels allumés. `0.97` : 0,38 s, des trajectoires, 20 000 pixels. `0.99` : 1,15 s, 39 000 pixels et le cœur qui bave |
| `VITE` | la vitesse qui correspond au blanc. Baisse-la et le disque entier devient blanc |
| `FROID` | les cinq couleurs, du plus lent au plus rapide |
