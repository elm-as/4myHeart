# 22 — Une galaxie

**Accroche :** *Et si je faisais une galaxie ?*

## L'idée

Personne ne dessine de spirale ici. Pas de courbe en `r = exp(θ)`, pas une seule
forme prévue. Il y a 110 000 étoiles, chacune sur son ellipse, et une seule idée
— celle de Bertil Lindblad, 1927 :

```
les ellipses ne sont pas toutes orientées pareil.
Leur inclinaison tourne doucement avec le rayon :

        inclinaison(a) = TORSION · a
```

C'est tout. Deux ellipses voisines se croisent quelque part ; sur toute la
galaxie, les endroits où elles se croisent forment **deux bras**.

Et les bras ne sont pas des objets : ce sont des **embouteillages**. Les étoiles
y entrent, s'y serrent, et en ressortent — comme les voitures dans un bouchon
qui remonte l'autoroute alors qu'aucune voiture ne recule. Aucune étoile
n'appartient à un bras.

Au début du film la torsion vaut zéro : toutes les ellipses sont alignées et on
ne voit qu'un disque allongé. On la fait monter, et les bras se forment seuls.

## Lancer

```bash
python galaxie.py
```

`ESPACE` fait une autre galaxie · `ECHAP` quitte.

## Le déroulé — et c'est ça, la vidéo

L'amplitude du mode à deux branches, mesurée couronne par couronne, dit
exactement où en sont les bras : **0 = les étoiles sont réparties partout,
1 = toutes dans deux rayons opposés.**

| Temps | Torsion (en tours sur le disque) | Bras | Ce qu'on voit |
|---|---|---|---|
| 0 – 1,5 s | — | — | le noir |
| 2 s | 0,07 | 0,30 | un disque, avec une barre au milieu |
| 4 s | 0,26 | 0,39 | la barre se tord aux deux bouts |
| **6 s** | **0,51** | **0,49** | **deux bras, ouverts. Le maximum de contraste** |
| 8 s | 0,78 | 0,49 | ils s'enroulent, ils s'affinent |
| 10 s | 1,00 | 0,40 | un tour complet : les bras commencent à se confondre |
| 13 s | 1,16 | 0,34 | la torsion s'arrête. C'est l'image du film |
| 13 – 40 s | 1,16 | 0,33 | la figure tourne d'un bloc, les étoiles la traversent |

La seconde à filmer est la **sixième** : le moment où la barre du début se
tord et devient deux bras.

Le contraste des bras est maximal à un demi-tour de torsion, puis **il baisse**.
C'est le problème de l'enroulement, et il est mesuré ici : plus la torsion
augmente, plus les bras se serrent, jusqu'à ne plus se distinguer du disque.
Une vraie galaxie a fait cent tours depuis sa formation — s'il suffisait de
laisser la torsion augmenter, il n'y aurait plus de spirales nulle part. C'est
exactement le problème que la théorie des ondes de densité est venue résoudre :
la figure tourne à **sa** vitesse, pas à celle des étoiles. Ici on l'obtient en
arrêtant la torsion et en faisant tourner le motif entier.

Le film s'arrête à 1,16 tour et non à 0,51, où le contraste est pourtant le plus
fort : à un demi-tour, les deux bras sont si ouverts qu'ils ressemblent à un
anneau. L'œil et la mesure ne sont pas d'accord, et j'ai suivi l'œil.

## Le détail dont je suis content : les étoiles ne sont pas sur leurs ellipses

Premier essai : chaque étoile exactement sur son ellipse. Résultat, on ne voyait
pas une galaxie mais **des cerceaux emboîtés** — les ellipses individuelles,
une par une, parce qu'à 110 000 étoiles pour 130 000 pixels il n'y en a pas
assez pour que les courbes se fondent.

La correction n'est pas un lissage, c'est de la physique : une vraie étoile
n'est pas sur une orbite parfaite, elle oscille autour. On lui donne donc un
écart fixe, tiré au hasard, proportionnel à son rayon.

| dispersion | bras (mode 2) | pixels occupés | étoiles par pixel occupé |
|---|---|---|---|
| 0 % | 0,359 | 29 181 | 3,77 |
| **3,4 %** | **0,333** | **33 423** | **3,29** |
| 8 % | 0,253 | 34 879 | 3,15 |

À 3,4 %, les cerceaux disparaissent (14 % de pixels occupés en plus) et les bras
ne perdent que 7 % de leur contraste. À 8 %, on a perdu un tiers des bras pour
5 % de pixels de plus : c'est du flou, pas de la dispersion.

## L'autre détail : deux comptages suffisent pour une image en couleur

Une étoile dépose son éclat dans un tableau, et son éclat **multiplié par sa
teinte** dans un second. Le rapport des deux donne la teinte moyenne du pixel,
pondérée par la lumière — ce qui est exactement ce que fait un capteur. Deux
comptages, là où trois seraient nécessaires en rouge-vert-bleu.

Ensuite, teinte et luminosité ne sont pas combinées à la main. Elles sont
réduites à 16 et 256 niveaux, mises bout à bout en un seul indice, et la couleur
sort d'une table de 4 096 entrées — **avec le tone-mapping déjà dedans** :

| | ms par image |
|---|---|
| palette, puis exponentielle, puis multiplication à trois canaux | 6,3 |
| une seule lecture dans la table teinte × lumière | **3,6** |

Et comme la galaxie est ronde alors que l'image est haute, on ne calcule qu'un
carré de 360 × 360 qu'on pose au milieu : les deux bandes noires du haut et du
bas sont gratuites, et ça fait **44 % de pixels en moins** (129 600 au lieu de
230 400) sur chaque ligne du tableau ci-dessus.

## Ce que ça coûte

| | ms par image |
|---|---|
| `avancer` — 110 000 positions recalculées de zéro | 2,1 |
| les deux comptages (lumière, chaleur) | 2,5 |
| la table teinte × lumière | 3,6 |
| halo + agrandissement vers la fenêtre | 3,2 |
| **total** | **≈ 11,5 ms** pour un budget de 16,7 |

Une étoile, dans ce programme, c'est **six nombres** : son demi-grand axe, sa
phase, sa vitesse angulaire, son éclat, sa teinte et son écart à l'ellipse. Sa
position n'est rangée nulle part — elle se recalcule entièrement à chaque image,
en dix lignes, et ça coûte 2,1 ms. Il n'y a aucun état à conserver : on peut
sauter à la seconde 3 000 d'un seul calcul.

## Ce qui reste imparfait

- **Il n'y a pas de gravité.** C'est une cinématique, pas une dynamique : les
  orbites sont posées, pas calculées. Une étoile ne sent ni le bulbe, ni les
  autres étoiles, ni le bras qu'elle traverse — alors qu'en vrai c'est le bras
  qui, en la freinant, l'y retient un peu plus longtemps.
- **Les bras ne se nourrissent pas eux-mêmes.** Dans une vraie galaxie, la
  surdensité d'un bras attire, comprime le gaz, allume des étoiles jeunes — qui
  rendent le bras plus visible encore. Ici les étoiles bleues sont bleues parce
  qu'elles sont loin du centre, pas parce qu'elles viennent de naître.
- **La torsion s'arrête d'un coup.** C'est un aveu : je ne simule pas ce qui
  maintient les bras, je le décrète. Le tableau plus haut montre ce qui se
  passerait sinon.
- **C'est vu de face, et parfaitement plat.** Pas d'épaisseur, pas
  d'inclinaison, pas de bandes de poussière — et ce sont elles qui donnent aux
  photos de galaxies leur relief.
- **Le bulbe est un simple tas.** Il devrait avoir sa propre dynamique, des
  orbites désordonnées en trois dimensions. Ici c'est le même modèle, écrasé
  vers le centre.

## À bricoler

Tous les chiffres ci-dessous sont mesurés, pas devinés.

| Ligne | Effet |
|---|---|
| `TORSION` | 0,048 rad/px, soit 1,16 tour sur le disque. **Le seul réglage qui fasse les bras** — voir le tableau |
| `T_TORSION` | 13 s pour l'installer. C'est toute la dramaturgie du film |
| `E_MAX` | l'aplatissement des ellipses. À `0`, elles sont des cercles et il n'y a plus de croisements, donc plus de bras du tout |
| `DISPERSION` | 3,4 % : ce qui empêche de voir les ellipses une par une. À `0`, des cerceaux ; à `8 %`, de la purée |
| `NB` | 110 000 étoiles. En dessous de 60 000, la dispersion ne suffit plus à combler |
| `ECHELLE` | la décroissance du disque. Plus grand, un disque étalé ; plus petit, tout est dans le bulbe |
| `BULBE` | 8 % des étoiles au centre. À `0,25`, le cœur est un projecteur et mange les bras |
| `VITESSE` | 26 : la vitesse de rotation. Courbe plate, donc le centre tourne beaucoup plus vite que le bord — et ça se voit à l'œil nu au bout de dix secondes |
| `FIGURE` | 0,085 rad/s : la rotation de la figure elle-même, une fois la torsion arrêtée |
| `ECLAT` | le tone-mapping. Au-dessus de `0,6`, le bulbe sature en blanc |
| `COTE` | 360 : le carré de calcul. C'est lui qui fixe à la fois la finesse et le coût |
