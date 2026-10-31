# 21 — Une ville

**Accroche :** *Et si je générais une ville ?*

## L'idée

Il n'y a pas de plan dans ce programme. Pas de carte, pas de modèle de ville,
pas une seule rue écrite à la main. Il y a un rectangle — le cadre de l'image —
et une règle qu'on applique cent vingt-sept fois :

```
prends une parcelle, coupe-la en deux par une droite,
et laisse une rue dans la coupure.
```

C'est tout. La largeur de la rue ne dépend que de la **profondeur** de la
coupure : 20 pixels pour la première, 3 pour la dernière. Ce qui en sort — des
avenues qui traversent toute l'image, des rues qui les relient, des ruelles qui
ne mènent nulle part — n'a jamais été décrit nulle part.

Puis on recommence, plus petit : chaque îlot est reculé d'un trottoir, recoupé
en immeubles, et chaque immeuble est percé de fenêtres. Et on allume.

## Lancer

```bash
python ville.py
```

`ESPACE` construit une autre ville · `ECHAP` quitte. Le programme enchaîne tout
seul.

## Le déroulé — et c'est ça, la vidéo

Un plan de ville pour une graine donnée : **127 rues, 128 îlots, 438 immeubles,
4 208 fenêtres allumées, 86 lampadaires.** Calculé en 289 ms au démarrage ;
l'animation ne fait que dévoiler dans l'ordre.

| Temps | Ce qu'on voit |
|---|---|
| 0 – 1,5 s | le noir |
| 1,5 – 4 s | **les avenues.** Trois traits larges qui coupent l'image en morceaux |
| 4 – 8 s | les rues, puis les ruelles. Le quadrillage se referme, de plus en plus fin |
| 7 – 14 s | **les immeubles sortent**, du centre vers les bords, en tache d'huile |
| 13 – 18 s | les lampadaires s'allument, avenue par avenue : un trait de points orange |
| 15 – 33 s | **les fenêtres.** Une, deux, dix, deux cents à la seconde, puis ça ralentit |
| 33 – 38 s | la ville entière, la nuit, vue d'avion |

La seconde à filmer est la **quinzième** : le moment où le plan cesse d'être un
dessin technique et devient habité — les premières fenêtres, éparses, dans une
ville encore noire.

Un immeuble sur huit reste éteint, et les autres n'allument qu'entre 22 % et
92 % de leurs fenêtres, tiré immeuble par immeuble. C'est ce qui évite le
quadrillage parfait : une ville où toutes les fenêtres sont allumées ne
ressemble à rien.

## Le détail dont je suis content : je me trompais sur la bonne règle

Le problème de toute subdivision récursive, c'est les **lanières** : des
parcelles longues et fines qui ne ressemblent à rien. J'étais sûr que le remède
était de choisir la **direction** de la coupe — couper en travers du plus long
côté, pour ne jamais rallonger une parcelle déjà longue.

Mesuré sur huit villes, en regardant l'élancement de chaque îlot (le rapport
long/court de sa meilleure boîte englobante) :

| règle de coupe | élancement médian | p99 | **lanières (> 2,5)** |
|---|---|---|---|
| en travers du plus long côté | 1,23 | 2,79 | **1,9 %** |
| direction tirée au hasard | 1,22 | 3,28 | **3,5 %** |
| coupe n'importe où entre 8 % et 92 % | 1,59 | 6,36 | **22,8 %** |

La direction ne fait presque rien : 1,9 % contre 3,5 %, et l'îlot médian ne
bouge pas. Ce qui fait tout, c'est la **position** : couper toujours près du
milieu — entre 34 % et 66 % de la largeur — au lieu de couper n'importe où. Ça
divise le nombre de lanières par **douze**.

Et avec le recul c'est évident : une coupe à 8 % détache une bande étroite qui
sera à son tour coupée dans le mauvais sens, et l'erreur se transmet. Une coupe
au milieu ne peut pas produire pire que ce qu'elle a reçu.

La règle de direction reste dans le programme — elle coûte une ligne et fait
quand même gagner la moitié des lanières restantes. Mais ce n'est pas elle qui
fait la ville.

## L'autre détail : tout est convexe, et ça règle tout

Une seule fonction fait les rues, les trottoirs, les cours et les lots :
`couper(parcelle, n, d)`, qui garde la moitié d'un polygone d'un côté d'une
droite (Sutherland-Hodgman, quinze lignes).

Elle suffit parce que **couper un convexe par une droite donne deux convexes**.
Tout descend du rectangle de départ, donc tout est convexe, et ça se vérifie :
128 îlots sur 128, 438 immeubles sur 438.

Et sur un convexe, reculer le contour d'une marge — le trottoir, la cour entre
deux immeubles, la marge des fenêtres — n'est pas un calcul d'offset avec ses
cas dégénérés. C'est la même fonction, appliquée une fois par côté, avec `d`
décalé de la marge :

```python
for chaque côté (a, b):
    n = normale au côté
    poly = couper(poly, n, n·a - marge)
```

Un offset de polygone quelconque demanderait de gérer les arêtes qui se
croisent, les trous qui apparaissent, les morceaux qui se détachent. Ici il n'y
a rien à gérer : si la parcelle est trop petite pour la marge, la fonction rend
`None`, et on ne construit pas.

## Ce que ça coûte

| | |
|---|---|
| calculer le plan entier (rues, îlots, immeubles, fenêtres) | **289 ms**, une fois |
| une image, médiane | **1,25 ms** |
| une image, p95 | 3,46 ms |

L'animation est quasi gratuite parce qu'**on ne redessine jamais**. Il y a deux
calques qui ne font que grandir : le plan (rues et toits) et la lumière. Une
image, c'est deux recouvrements de 921 600 pixels, plus les trois ou quatre
fenêtres qui viennent de s'allumer.

Chaque lumière est un petit disque flou pré-calculé, posé **en addition** : deux
lampadaires proches s'additionnent, comme de la vraie lumière, et une avenue
bordée de lampes finit par former un ruban continu. C'est un blit de 23 × 23
pixels par lampe, fait une fois dans la vie de la lampe.

## Ce qui reste imparfait

- **C'est vu du dessus, donc il n'y a pas de hauteur.** Les immeubles ont bien
  une hauteur tirée au sort, mais elle ne sert qu'à éclairer plus ou moins le
  liseré du toit. Une vraie vue aérienne aurait des ombres portées, et c'est ce
  qui manque le plus.
- **Les fenêtres sont sur le toit.** D'en haut on verrait des toits, pas des
  fenêtres. C'est une convention — celle des plans de ville nocturnes — mais
  c'en est une.
- **Pas de nature.** Pas de parc, pas de fleuve, pas de place. Une vraie ville
  a des vides, et ce sont eux qui la rendent lisible. Ici la subdivision remplit
  tout : il suffirait de tirer au sort quelques îlots à ne pas bâtir.
- **Toutes les rues sont droites.** La subdivision par droites ne peut pas faire
  autrement. Les villes qui ont poussé avant l'automobile sont courbes.
- **Rien ne bouge.** Pas de voitures, pas de feux qui changent. Une traînée de
  phares le long des avenues ferait beaucoup, et coûterait une ligne de plus
  par image.
- **Les avenues sont les premières coupures, donc elles traversent toute
  l'image.** C'est juste pour une avenue, faux pour une rue : dans une vraie
  ville, une rue s'arrête quand elle rencontre un obstacle.

## À bricoler

Tous les chiffres ci-dessous sont mesurés, pas devinés.

| Ligne | Effet |
|---|---|
| `RUES` | la largeur de rue par profondeur : `[20, 13, 9, 7, 5, 4, 3]`. C'est toute la hiérarchie de la ville, et c'est la seule chose qui la rend lisible |
| `PROFOND` | 7 coupures successives → 128 îlots. À 8, il y en a le double et deux fois plus fins |
| `AIRE_MIN` | 2 600 px² : au-dessous, on ne coupe plus. Avec `PROFOND`, c'est ce qui fixe la taille d'un îlot |
| `0.34, 0.66` (dans `diviser`) | **le réglage le plus important du fichier** — voir le tableau. À `0.08, 0.92`, un îlot sur quatre devient une lanière |
| `BIAIS` | une coupure sur cinq part de travers. C'est ce qui donne les avenues diagonales ; à `0`, on obtient un damier |
| `PENCHE` | le désordre d'angle, 0,13 radian. À `0`, tout est parfaitement aligné et ça fait plan cadastral |
| `LOTS` | 2 100 px² par immeuble. À 5 500, on obtient 193 gros immeubles au lieu de 438 petits |
| `TROTTOIR`, `COUR` | les deux marges. Elles font tout l'aspect « bâti serré » ou « quartier pavillonnaire » |
| `VIDE`, `OCCUPE` | un immeuble sur huit reste noir, les autres allument 22 à 92 % de leurs fenêtres. **C'est ce qui fait que ça respire** |
| `PART_FROIDE` | une fenêtre sur six est bleue — un écran, un néon. À `0`, la ville devient monochrome et plate |
| `T_LUMIERE` | 19 s pour allumer 4 208 fenêtres, en cloche : lentement, puis vite, puis lentement |
