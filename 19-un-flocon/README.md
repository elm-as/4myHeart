# 19 — Un flocon

**Accroche :** *Et si je faisais naître un flocon ?*

## L'idée

La symétrie n'est écrite nulle part dans le fichier. Cherche : pas de rotation,
pas de miroir, pas de « et on recopie sur les six branches ». Il y a une grille
hexagonale, **une** case de glace au milieu, et deux lignes de règle.

Le modèle est celui de Clifford Reiter (2005), le plus simple qui donne de vrais
flocons. Chaque case porte un nombre `s` : l'eau qu'elle contient. Une case est
de la glace dès que `s ≥ 1`. À chaque pas, on partage cette eau en deux :

- les cases **réceptives** — la glace, et tout ce qui la touche — mettent leur
  eau de côté : elle ne diffuse plus. Et elles en reçoivent un peu plus, `γ`, à
  chaque pas : c'est la vapeur du nuage qui vient se poser ;
- les autres laissent leur eau diffuser vers les six voisines.

Puis on recolle les deux parts :

```
u ← u + (α/2)·(moyenne des six voisines − u)      (ce qui diffuse)
s ← u + v                                          (+ ce qui est mis de côté)
```

Ce qui se passe alors est la seule chose qui compte : **une pointe qui dépasse
touche plus de vapeur qu'un creux.** Elle grossit donc plus vite, donc elle
dépasse davantage. C'est l'instabilité de Mullins-Sekerka, et c'est elle qui
fabrique les branches. Personne ne les dessine.

Et la symétrie ? Elle vient de ce que les six directions de la grille sont
identiques, et que le départ est une seule case. Les six branches ne se
recopient pas l'une l'autre : **elles subissent exactement la même chose.**

## Lancer

```bash
python flocon.py
```

`ESPACE` fait naître un autre flocon · `ECHAP` quitte. Le programme enchaîne
tout seul : il tire une famille au hasard à chaque fois.

## Le déroulé — et c'est ça, la vidéo

| Temps | Ce qu'on voit |
|---|---|
| 0 – 1,2 s | un fond bleu nuit, vide. **Une case, qu'on ne voit pas encore** |
| 1 – 6 s | un petit hexagone apparaît au centre et grandit lentement |
| 6 – 12 s | les six pointes se déclarent. À partir de là on sait ce que c'est |
| 12 – 26 s | les branches partent, se ramifient, portent des branches secondaires. Une auréole sombre les suit : c'est l'air qu'elles ont vidé de sa vapeur |
| 26 s | le flocon touche le bord du cadre. Il s'arrête |
| +5 s | on le regarde, puis un autre commence — d'une autre famille |

Le moment à filmer est **entre la 6ᵉ et la 12ᵉ seconde** : celui où six pointes
sortent d'une tache ronde, sans que rien n'ait été demandé.

Le plan ne s'épuise pas : deux flocons de la même famille ne sont pas non plus
identiques, parce que les erreurs d'arrondi ne tombent jamais au même endroit —
et que l'instabilité les amplifie (voir plus bas).

## Les six familles

Trois nombres suffisent à tout changer. Mesuré jusqu'à ce que le flocon touche
le bord du cadre :

| `α` | `β` | `γ` | pas | cases de glace | ce que ça donne |
|---|---|---|---|---|---|
| 1,00 | 0,40 | 0,0001 | 2 422 | 6 769 | l'étoile à six branches, la plus classique |
| 1,00 | 0,35 | 0,0010 | 3 283 | 11 889 | des branches plus fines, plus longues, très plumeuses |
| 2,00 | 0,40 | 0,0001 | 1 215 | 6 001 | des aiguilles |
| 1,00 | 0,60 | 0,0100 | **557** | **19 999** | une plaque, presque pleine |
| 1,00 | 0,50 | 0,0010 | 1 220 | 11 575 | des dendrites avec des plaques au bout |
| 1,60 | 0,45 | 0,0005 | 1 106 | 9 451 | un compromis, très découpé |

`β` est le nombre qui compte : c'est la vapeur disponible au départ. Sous 0,4 il
n'y en a pas assez pour remplir, donc ça fait des fils ; au-dessus de 0,6 il y
en a partout, donc ça fait des plaques. Entre les deux, ça fait des flocons.

Le nombre de pas varie d'un facteur six d'une famille à l'autre. C'est pour ça
que la cadence est **inscrite dans la table** — elle est mesurée, pas choisie :

| famille | pas par image | durée à l'écran |
|---|---|---|
| l'étoile | 1,55 | 26 s |
| les branches fines | 2,10 | 26 s |
| la plaque | **0,36** | 26 s |

Sans ça, la même vidéo durerait entre 9 et 55 secondes selon le tirage.

## Le détail dont je suis content : la symétrie, mesurée

Puisque personne ne l'a écrite, autant vérifier qu'elle est là. On tourne le
flocon fini de 60° — en coordonnées axiales, `(q, r) → (−r, q+r)` — et on le
compare à lui-même :

| famille | écart maximum après rotation | sur des valeurs allant jusqu'à |
|---|---|---|
| la plaque (557 pas) | **6,0·10⁻⁷** | 6,57 |
| l'étoile (2 422 pas) | **1,6·10⁻³** | 1,28 |

La première ligne, c'est exactement le bruit d'arrondi du `float32` : la
symétrie est parfaite à la précision de la machine.

La seconde est trois mille fois plus grande, et c'est le plus intéressant du
programme. Le modèle est le même, la grille est la même — mais l'étoile pousse
dans le **régime instable**, celui où une pointe qui dépasse d'un cheveu se met
à dépasser de plus en plus. Et ce que cette instabilité amplifie, faute de mieux,
c'est l'erreur d'arrondi : un 10⁻⁷ du premier pas devient un 10⁻³ au deux
millième.

Autrement dit : les six branches ne sont pas identiques, elles sont identiques
**à un millième près** — et ce millième, c'est la machine qui l'a inventé. C'est
aussi pour ça que deux flocons de la même famille ne se ressemblent jamais tout
à fait.

## L'autre détail : la symétrie n'est pas dans la physique, elle est dans la grille

Le test tient en une ligne : on remplace la moyenne des **six** voisines par la
moyenne des **quatre** voisines d'un carré, on ne touche à rien d'autre.

| grille | pas | cases de glace | résultat |
|---|---|---|---|
| hexagonale (6 voisines) | 2 422 | 6 769 | **six branches** |
| carrée (4 voisines) | 1 425 | 4 057 | **quatre branches**, en croix |

Même diffusion, même seuil, même instabilité — et un cristal à quatre branches,
qui n'existe pas dans la nature. Un flocon a six branches parce que la molécule
d'eau fait des liaisons à 120°, pas parce que la croissance « aime » le six.
Toute la physique du flocon est dans la géométrie du réseau.

## Ce que ça coûte

| | ms par image |
|---|---|
| un pas de croissance (68 121 cases, six décalages) | 0,61 |
| cadence moyenne : 1,1 pas par image | 0,7 |
| `Vue.dessiner` | 11,5 |
| **total** | **≈ 12,2 ms** pour un budget de 16,7 |

**C'est le dessin qui coûte, pas la physique** — et de vingt fois. La raison est
la grille hexagonale : un pixel n'appartient pas à une case par simple division
entière, il faut une table. Elle est calculée une fois au démarrage, mais il
faut quand même la parcourir à chaque image :

| | ms |
|---|---|
| aller chercher `s` pour chaque pixel à travers la table | 1,1 |
| passer de `s` à une couleur (table de 512 teintes) | 3,3 |
| le halo (deux réductions / agrandissements) | 3,9 |
| l'agrandissement final vers la fenêtre | 2,5 |

L'image est calculée en 360 × 640, moitié moins que la fenêtre, puis agrandie —
sinon les deux premières lignes coûtent quatre fois plus.

Le calcul de la table, lui, est la seule partie pénible des hexagones. On
inverse la transformation, ce qui donne des coordonnées fractionnaires, puis on
arrondit **en coordonnées cubiques** : on arrondit les trois, et on corrige
celle qui a le plus bougé. Arrondir simplement les deux coordonnées du tableau
donnerait des losanges au lieu d'hexagones — et ça se verrait tout de suite, le
flocon serait penché.

## Ce qui reste imparfait

- **Ce n'est pas de la physique du cristal.** Reiter ne modélise ni la
  température, ni les faces du cristal, ni la vitesse propre à chaque face. Il
  modélise une diffusion et un seuil. Que ça donne des flocons qu'on reconnaît
  est presque une surprise — mais ça ne prédit rien.
- **C'est trop symétrique.** Un vrai flocon n'est pas symétrique : ses six bras
  traversent des zones d'humidité différentes en tombant, et finissent
  différents. Ici les six bras vivent exactement la même histoire, à un millième
  près. Pour faire vrai, il faudrait faire varier `β` au cours du temps — ce qui
  donnerait un flocon symétrique **par couches**, comme les vrais.
- **C'est plat.** Un flocon est un objet en trois dimensions, avec une épaisseur
  qui change du centre au bord. Ici il n'y a qu'une couche de cases.
- **La grille se voit sur les branches.** Les six bras sont alignés sur les axes
  du réseau, et les ramifications font toutes le même angle. C'est vrai des
  vrais flocons aussi — mais eux n'ont pas de pixels.
- **Le flocon ne tombe pas.** Il pousse au centre de l'image, immobile. Une
  chute lente, avec une rotation, rendrait la vidéo plus vivante et coûterait un
  deuxième passage de rendu.

## À bricoler

Tous les chiffres ci-dessous sont mesurés, pas devinés.

| Ligne | Effet |
|---|---|
| `FAMILLES` | les six jeux de `(α, β, γ)` — et le nombre de pas mesuré, qui sert à donner la même durée à toutes |
| `β` (2ᵉ colonne) | **le réglage qui décide de tout** : 0,35 des fils, 0,60 une plaque |
| `α` | la vitesse de diffusion. Plus haut, la vapeur arrive plus vite aux pointes, et le flocon devient une aiguille |
| `γ` | ce qui se dépose sur la glace à chaque pas. À `0,01`, le flocon est fini quatre fois plus tôt et il est plein |
| `N` | 261 cases de côté. Plus grand, des branches plus détaillées, et le coût monte comme le carré |
| `RMAX` | 112 : le rayon où l'on s'arrête. C'est ce qui cadre le flocon dans la largeur |
| `RAYON` | 2,7 px par case. Avec `N` et `RMAX`, c'est tout le cadrage |
| `DUREE` | 26 s de croissance, quelle que soit la famille |
| `HALO` | la lueur autour de la glace. À `0`, l'image devient dure et le flocon a l'air découpé aux ciseaux |
| `BORD`, `COEUR` | le bleu du pourtour et le blanc du cœur. C'est l'épaisseur de la glace qu'on colore, rien d'autre |
