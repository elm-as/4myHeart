# 20 — De l'eau

**Accroche :** *Et si je simulais de l'eau ?*

## L'idée

Il n'y a pas de surface dans ce programme. Pas de hauteur d'eau, pas de courbe,
pas de maillage. Il y a 1 408 points, et **une seule consigne** :

```
la densité autour de chaque point doit valoir ρ₀
```

Rien d'autre. La vague, l'écume, l'éclaboussure qui monte le long du mur, la
flaque qui finit par s'aplatir : tout ça est ce que fait un tas de points qui
refusent d'être serrés, dans un champ de pesanteur.

La méthode est **PBF** — *Position Based Fluids*, Macklin et Müller, 2013. Elle
ne calcule aucune force de pression. Elle déplace les points :

1. la gravité pousse tout le monde : `p = x + dt·v` ;
2. on mesure la densité autour de chaque point, avec un noyau lisse ;
3. on calcule de combien il faudrait bouger pour que cette densité revienne à
   ρ₀ — c'est un multiplicateur de Lagrange, `λ` ;
4. on bouge. Puis on recommence trois fois ;
5. la vitesse, à la fin, est simplement `(p − x) / dt`.

L'intérêt par rapport à la SPH classique : **la correction est une position,
pas une force.** Ça ne peut donc pas exploser — au pire le fluide est un peu
compressible. C'est ce qui permet un pas de temps d'une image entière au lieu
d'un millième de seconde.

Le `ρ₀` n'est pas choisi, il est **mesuré** au démarrage : on calcule la densité
qu'aurait un empilement régulier à l'espacement de départ. Se tromper dessus
fait un fluide qui gonfle ou qui s'écrase tout seul. Ici : 0,0612 pour une
valeur observée au cœur du bloc de 0,0612.

## Lancer

```bash
python eau.py
```

`ESPACE` remonte le barrage · `ECHAP` quitte.

## Le déroulé — et c'est ça, la vidéo

| Temps | Ce qu'on voit | Compression | Front |
|---|---|---|---|
| 0 – 2,2 s | une colonne d'eau, immobile, tenue par un barrage qu'on ne voit pas | 0,0 % | 255 |
| 2,2 s | **le barrage lâche.** La colonne s'effondre sur elle-même | — | — |
| 3 s | la base part vers la droite, le haut tombe | 1,4 % | 228 |
| 4 s | l'impact. C'est le pire moment pour le solveur | **7,5 %** | 181 |
| 5 s | la vague file vers le mur de droite et commence à grimper | 3,0 % | 265 |
| **6 s** | **elle atteint le haut du cadre** — 318 sur 320 | 2,7 % | **318** |
| 7,5 s | elle retombe et repart vers la gauche | 2,7 % | 242 |
| 10 – 14 s | le ballottement : deux allers-retours, de plus en plus mous | 3,0 % | 205 → 127 |
| 20 – 30 s | la surface s'aplatit. Vitesse maximale : 2,7 unité/s | 3,0 % | 120 |

La seconde à filmer est la **sixième** : la vague monte le long du mur de droite
jusqu'en haut de l'image, se retourne, et lâche trois gouttes qui partent seules.

## Le détail dont je suis content : 45 places pour 8 voisins

Pour savoir qui est près de qui, on range les points dans une grille dont la
case fait un rayon de noyau, puis on lit les neuf cases autour. Chaque case
garde cinq points : ça fait **45 places candidates**.

Sauf qu'un point n'a que **8 voisins** à portée. Les 37 autres places sont
vides ou trop loin — et on les traînerait dans chacun des quatre passages de
correction, à chaque image.

Alors on les compacte : une fois par image, on garde les seize premiers vrais
voisins dans un tableau serré.

| | ms par image |
|---|---|
| travailler sur les 45 places candidates | 11,1 |
| compacter d'abord, puis travailler sur 16 | **6,2** |

Le résultat est identique au chiffre près — compression moyenne 3,5 % dans les
deux cas. C'est juste 37 colonnes de zéros qu'on ne multiplie plus.

Et la compaction elle-même n'a pas de boucle : on marque les voisins valides, on
compte combien en précèdent chacun sur sa ligne (`cumsum`), et ce compte **est**
l'indice où l'écrire.

## L'autre détail : ce qui empêche de tout traverser

Un point qui avance de plus d'un rayon de noyau en un pas passe à travers ses
voisins **sans les avoir vus** : ils n'étaient pas dans la grille au début du
pas, ils n'y seront plus à la fin. Et comme il ne les a pas vus, il ne les a pas
repoussés. La densité devient fausse, la correction devient énorme, et l'erreur
se nourrit d'elle-même.

Mesuré sur la même scène, avec un noyau une fois et demie plus petit :

| | compression max | compression moyenne | vitesse max |
|---|---|---|---|
| `H = 4,0`, sans limite de vitesse | 27,9 % | 15,6 % | **18 960** |
| `H = 4,0`, vitesse limitée à 120 | 27,9 % | 12,5 % | 637 |
| **`H = 6,67` (le programme), sans limite** | **7,4 %** | **2,6 %** | 260 |
| `H = 6,67`, vitesse limitée à 195 | 7,5 % | 2,6 % | 209 |

À `H = 4`, un point à 400 unités/s franchit 6,7 unités par image, soit une fois
et demie le rayon : il traverse. La vitesse part à 18 960 et le fluide est un
gaz. La limite de vitesse le contient — mais ne le répare pas : 28 % de
compression, c'est de la mousse, pas de l'eau.

À `H = 6,67`, le même point franchit un demi-rayon, et **il n'y a plus de
problème du tout** : avec ou sans limite, c'est le même fluide. La limite reste
dans le programme comme une ceinture de sécurité pour qui touchera aux réglages.

La vraie leçon n'est pas « il faut limiter la vitesse », c'est : **le rayon du
noyau doit être choisi avec le pas de temps, pas contre lui.**

## Ce que ça coûte

| | ms par image |
|---|---|
| ranger la grille et compacter les voisins | 1,5 |
| quatre passes de correction de densité | 5,2 |
| viscosité XSPH | 0,8 |
| déposer 1 408 taches sur la grille d'image | 1,0 |
| couleurs + agrandissement 180 × 320 → 720 × 1280 | 2,8 |
| **total** | **≈ 11,4 ms** pour un budget de 16,7 |

Les passes de correction coûtent ce qu'elles rapportent :

| passes | compression max | compression moyenne | ms |
|---|---|---|---|
| 1 | 30,7 % | 12,8 % | 3,9 |
| 2 | 13,9 % | 5,1 % | 5,1 |
| 3 | 10,9 % | 3,5 % | 6,4 |
| **4** | **7,5 %** | **2,6 %** | **7,0** |

La quatrième passe coûte 0,7 ms et fait gagner un quart de la compression
restante : c'est la dernière qui vaut son prix.

Et pour le dessin, un détail qui vaut huit fois son poids. Chaque point dépose
une petite tache gaussienne de 9 × 9 cases sur la grille d'image — 81 dépôts par
point. Faits séparément, ce sont 81 tableaux de 57 600 cases à remettre à zéro :

| | ms |
|---|---|
| 81 comptages séparés | 8,3 |
| un seul comptage, sur 114 048 indices d'un coup | **1,0** |

Ce n'est pas le comptage qui coûte, c'est l'allocation.

## Ce qui reste imparfait

- **L'eau est compressible de 2,6 % en moyenne, 7,5 % à l'impact.** De la vraie
  eau ne se comprime pas d'un millionième. Ça se voit : au moment du choc, la
  masse « rebondit » légèrement, comme si elle était un peu élastique.
- **Le terme anti-grumeaux ne sert à rien ici.** La méthode le prescrit contre
  l'instabilité de traction ; mesuré, il ne change rien (distance au plus proche
  voisin : 3,85 unités avec, 3,85 sans, pour 4,00 au repos). Le noyau est assez
  large — 1,67 fois l'espacement, huit voisins — pour que le problème n'existe
  pas. Il reste dans le code parce qu'il protège les autres réglages.
- **Les murs sont parfaitement mous.** Un point qui sort est remis dedans, point.
  Il perd donc toute sa vitesse perpendiculaire : pas de rebond, pas de
  frottement non plus. C'est à peu près ce que fait de l'eau contre du béton,
  mais ce n'est pas un choix, c'est une absence de choix.
- **Il n'y a pas de tension superficielle.** Les gouttes qui se détachent sont
  rondes parce que le noyau est rond, pas parce qu'une surface les tire.
- **Cinq points par case, et pas plus.** Quand une case en contient six, le
  sixième est oublié pour une image. Mesuré : ça arrive sur deux cases au pire
  moment de l'impact, et le point est repris à l'image suivante.
- **1 408 points, c'est peu.** Une vraie simulation de vague en compte des
  millions. Ici, un point « pèse » 4 × 4 unités, soit 16 × 16 pixels à l'écran :
  c'est la taille du plus petit détail possible.

## À bricoler

Tous les chiffres ci-dessous sont mesurés, pas devinés.

| Ligne | Effet |
|---|---|
| `ESPACE` et `H` | **le couple qui décide de tout.** Le rapport doit rester vers 1,67 : plus serré, moins de voisins et une densité bruitée ; plus large, quatre fois plus de paires |
| `COLONNES`, `LIGNES` | la colonne de départ : 22 × 64. Plus large, elle s'effondre moins haut ; plus haute, elle dépasse du cadre |
| `G` | 80. C'est aussi ce qui fixe la vitesse maximale atteinte, donc la validité du pas de temps |
| `ITERATIONS` | 4 passes. Voir le tableau : en dessous de 3, l'eau devient molle |
| `RELACHE` | l'epsilon de `λ`. Trop petit, les corrections s'emballent près de la surface ; trop grand, le fluide ne se corrige plus |
| `VMAX` | 195 unités/s = un demi-rayon de noyau par image. Ne sert à rien tant qu'on ne touche pas à `H` — et sauve tout dès qu'on y touche |
| `VISCO` | 0,055. À `0`, la surface grouille : chaque point garde sa vitesse propre |
| `VOISINS` | 16 places après compaction. À 8, des voisins sont perdus dans les zones serrées |
| `SEUIL` | la densité où l'eau devient visible. C'est ce qui dessine le liseré blanc de l'écume |
| `ETALE` | la largeur de la tache d'un point à l'image. Plus petite, on voit les points un par un ; plus large, l'eau devient une soupe |
