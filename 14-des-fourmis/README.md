# 14 — Des fourmis

**Accroche :** *Et si des fourmis cherchaient à manger ?*

## L'idée

Aucune fourmi ne sait où est la nourriture. Aucune ne sait où sont les autres.
Il n'y a pas de chef, pas de plan, pas de carte — et pourtant, au bout de vingt
secondes, il y a des autoroutes.

Chaque fourmi ne fait que trois choses, et toujours les mêmes :

1. elle **renifle** devant elle — trois points : gauche, centre, droite
2. elle **tourne** vers le plus odorant, et avance
3. elle **laisse** derrière elle l'odeur de là d'où elle vient

La troisième ligne est la seule qui compte vraiment, parce qu'elle transforme le
sol en mémoire. Une fourmi qui rentre chargée laisse l'odeur *table*, et la
suivante n'a plus qu'à la suivre. Plus elles sont nombreuses à passer, plus ça
sent, plus elles passent.

Le sol, lui, **oublie** : l'odeur s'évapore et se répand un peu. Et c'est
l'oubli qui rend les routes nettes — sans lui, tout le sol finirait par sentir
pareil, et plus personne ne saurait où aller.

Deux odeurs, jamais mélangées :

| | qui la dépose | ce qu'elle veut dire |
|---|---|---|
| **bleu** | celles qui cherchent encore | « par ici on revient au nid » |
| **vert** | celles qui rentrent chargées | « par ici il y a à manger » |

Une route parcourue dans les deux sens porte donc les deux, et vire au blanc.
C'est à ça qu'on reconnaît une route qui marche.

## Lancer

```bash
python fourmis.py
```

`ESPACE` relance une autre colonie · `ECHAP` quitte.

## Le déroulé — et c'est ça, la vidéo

| Temps | Ce qu'on voit |
|---|---|
| 0 – 2 s | le nid crache **un front circulaire** : 1 200 fourmis partent dans toutes les directions à la fois |
| 2 – 5 s | les premiers tas sont touchés, et **de courts filaments verts** apparaissent, collés aux tas |
| 5 – 18 s | les filaments remontent jusqu'au nid, s'épaississent, **se redressent** : ce ne sont plus des chemins, ce sont des rayons |
| 18 – 40 s | les tas se vident un par un — et **chaque route s'éteint avec son tas** |
| 40 s | il ne reste que le nid, et des traces bleues qui pâlissent |

La seconde à filmer est la **cinquième** : c'est là qu'un trait vert traverse
enfin tout l'écran, du tas au nid, et qu'on comprend d'un coup ce qui se passe.

Mesuré sur cinq graines, et c'est d'une régularité rare pour une simulation de
ce genre :

| | |
|---|---|
| première bouchée prise | **2,1 s**, sur les cinq graines |
| les cinq tas s'éteignent entre | **18 et 40 s** |
| tout est mangé à | 34 à 44 s, 40 s en moyenne |
| temps mort avant la fin | **0,4 s** |

Autrement dit : il ne se passe pas une seconde sans que quelque chose bouge à
l'écran, et le plan se termine tout seul. Pas de coupe à prévoir.

## Le détail dont je suis content : une trace qui s'épuise

Une fourmi ne dépose pas la même quantité d'odeur du début à la fin. Elle part
d'une source avec une réserve pleine, et cette réserve s'épuise à mesure qu'elle
marche :

```python
self.force *= exp(-dt / SOUVENIR)     # SOUVENIR = 7 secondes
```

Une ligne, et c'est **tout le mécanisme du plus court chemin**. Deux trajets
mènent au même tas : le court est parcouru plus vite, donc marqué plus fort,
donc suivi plus souvent, donc marqué encore plus fort.

Et voilà ce qui est intéressant : en la retirant, **la colonie mange presque
pareil.** Mesuré sur trois graines, réserve figée à 1 :

| | sans `SOUVENIR` | avec |
|---|---|---|
| récolte en 46 s | 2 900 / 2 900 / 2 547 | 2 900 / 2 900 / 2 900 |
| tas vidés | 5 / 5 / 4 | 5 / 5 / 5 |
| **vert à l'écran, rapporté au bleu** | **0,09** | **0,21** |

Le gain de récolte est marginal. Ce qui change, c'est ce qu'on **voit** : il y a
deux fois moins de vert. Le bleu est déposé en permanence par un millier de
chercheuses, le vert seulement par la centaine qui rentre chargée ; quand la
réserve ne s'épuise jamais, le bleu sature tout et **l'odeur qui mène à la
nourriture devient illisible** — la seule chose que la vidéo avait à montrer.

C'est un réglage qui ne se voit sur aucune courbe de performance et qui décide
pourtant de tout le plan.

## L'autre détail : ce que la simulation ne fait pas

Le retour au nid est **guidé**, et il faut le dire.

L'odeur du nid ne survit pas loin du nid : une chercheuse qui erre depuis
longtemps n'a plus de réserve, donc ne dépose presque plus rien. Le bleu est
dense autour du nid et absent au bord de l'écran. Une fourmi chargée qui a perdu
la piste n'a alors plus rien à renifler.

Les fourmis ont donc un compas — le sens du nid, connu. Ce n'est pas de la
triche : une vraie fourmi compte ses pas et sait rentrer sans piste, les
biologistes appellent ça l'intégration de chemin. Mais sans lui, il n'y a pas de
film du tout. Mesuré sur trois graines, `COMPAS = 0` :

| | avec compas | sans |
|---|---|---|
| récolte en 46 s | 2 900 / 2 900 / 2 900 | 886 / 641 / 1 713 |
| tas vidés | 5 / 5 / 5 | 0 / 0 / 2 |
| **fourmis errant chargées, à la fin** | **0 / 0 / 0** | **873 / 292 / 431** |

Sept cents fourmis sur mille deux cents qui rentrent les bras pleins sans jamais
arriver : la boucle ne se ferme pas, donc rien ne se renforce, donc aucune route
n'apparaît.

Il faut donc être honnête sur ce qui s'auto-organise à l'écran : **c'est
l'aller.** Trouver un tas qu'aucune fourmi ne connaît et y amener toute la
colonie, ça, personne ne le souffle à personne. Le retour, lui, est aidé.

## Ce que ça coûte

Mesuré sur 600 images, colonie en régime établi :

| | ms par image |
|---|---|
| `vieillir` — évaporation + diffusion des deux odeurs | 1,9 |
| `avancer` — renifler, tourner, avancer, déposer, manger | 1,7 |
| `rendre` — deux odeurs, 1 200 points, tone-mapping | 7,0 |
| mise à l'échelle vers la fenêtre | ~1,0 |
| **total** | **≈ 11 ms** pour un budget de 16,7 |

Médiane 10,0 ms, p95 14,8 ms, **15 images sur 600** au-dessus du budget 60 i/s.

Deux choix expliquent l'essentiel :

- **Le sol vit en demi-résolution** (360 × 640). Évaporer et diffuser, c'est six
  passes sur 230 000 cases, deux fois par image. En pleine résolution ce serait
  quatre fois plus, et rien ne tiendrait.
- **L'image est faite de trois plans séparés**, pas d'un tableau `(H, L, 3)`.
  Un tableau à trois canaux oblige à écrire en travers de la mémoire à chaque
  couleur ajoutée ; trois plans restent contigus, et la seule transposition du
  programme est celle du blit, tout à la fin.

Chaque passe écrit dans un tampon réservé une fois pour toutes (`out=`). Écrit
naturellement — `a = a * (1 - part) + voisins * k` — ce serait huit tableaux
d'un mégaoctet réservés par image.

## Ce qui reste imparfait

- **Le rendu coûte deux fois la simulation.** 7 ms sur 11 partent à fabriquer
  l'image, alors que faire vivre mille deux cents fourmis et deux grilles d'odeur
  n'en coûte que 3,6. C'est le prix du tone-mapping sur 230 000 cases, trois
  fois. Si tu veux de la marge, c'est là qu'il faut couper, pas dans `NB`.
- **La colonie se verrouille sur ses premières routes.** Les cinq tas sont
  trouvés en quelques secondes, mais une route qui prend de l'avance capte toute
  la colonie. À `HASARD = 3.2`, un tas sur cinq n'était jamais fini, et le plan
  avait 15 s de vide. C'est le défaut classique de ces colonies ; ici il est
  réglé en laissant aux fourmis assez d'indécision (`HASARD = 4.5`) pour qu'elles
  ne se laissent jamais complètement enfermer dans une piste.
- Le vert est monté trois fois plus haut que le bleu **au rendu**. À poids égal
  il ne se verrait pas. C'est de l'affichage, la simulation n'en sait rien.
- Le nid et les tas sont dessinés, eux. Ce sont les deux seuls disques du
  programme — tout le reste à l'écran est de l'odeur ou une fourmi.

## À bricoler

Tous les chiffres ci-dessous sont mesurés, pas devinés.

| Ligne | Effet |
|---|---|
| `NB` | 1 200 fourmis. Presque gratuit à changer : `avancer` coûte 1,56 ms à 600, 1,81 à 1 200, 1,83 à 2 400 — le temps part dans les grilles, pas dans les fourmis |
| `SOUVENIR` | **le réglage central.** C'est lui qui fait gagner le chemin court, et c'est lui qui décide s'il y a du vert à l'écran |
| `EVAPORATION` | la vitesse d'oubli du sol. Trop lent, une route morte retient la colonie pendant dix secondes ; trop vite, rien ne tient |
| `DIFFUSION` | l'épaisseur des routes. À `0`, des traits d'un pixel que personne ne retrouve |
| `HASARD` | l'indécision. `3.2` : des routes superbes, mais un tas abandonné et 15 s de creux. `4.5` : tout est mangé, 0,4 s de creux |
| `COMPAS` | le sens du nid. **Doit rester au-dessus de `HASARD`**, sinon les chargées n'arrivent plus et il n'y a plus de film |
| `PORTEE` / `ECART` | la géométrie des trois capteurs : de combien elles voient devant, et sous quel angle |
| `REPAS` | la taille d'un tas, donc la durée du plan — mais mollement : `420` finit à 34 s, `500` à 37 s, `580` à 40 s |
| `NB_TAS` / `LOIN` | combien de tas, et à quelle distance du nid |
| `PLAFOND` | au-delà, une case ne sent pas plus fort. C'est ce qui empêche une seule route d'écraser toutes les autres |
