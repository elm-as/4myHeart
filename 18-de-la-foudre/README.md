# 18 — De la foudre

**Accroche :** *Et si la foudre cherchait le sol ?*

## L'idée

Personne ne dessine le zigzag. Pas de courbe, pas de fractale écrite à la main,
aucune forme prévue. Il y a un champ électrique, et une règle de croissance qui
tient en une ligne.

C'est le modèle du **claquage diélectrique** (Niemeyer, Pietronero et Wiesmann,
1984) — le même qui produit les figures de Lichtenberg :

- le nuage, en haut, est à potentiel **0** ; le sol, en bas, à **1** ;
- entre les deux, l'air : le potentiel y vérifie l'équation de Laplace,
  `∇²φ = 0`. On la résout par relaxation — chaque case devient la moyenne de
  ses quatre voisines ;
- **le canal déjà formé est un conducteur** : lui aussi est à 0. C'est tout ce
  qui compte — une branche qui avance *tire le potentiel avec elle* et déforme
  le champ devant elle ;
- à chaque pas, on regarde les cases libres qui touchent le canal, et on en
  allume **une au hasard**, avec une chance proportionnelle à `φ^η`.

Voilà. Le zigzag, les branches qui meurent, celle qui prend toute la place, le
fait que ça descende sans jamais aller droit : tout sort de cette ligne.

Quand une branche touche le sol, on remonte les parents jusqu'au nuage : ce
chemin-là est le canal principal, et c'est lui qui s'embrase — en trois éclats
séparés de quelques centièmes de seconde, comme un vrai éclair.

## Lancer

```bash
python foudre.py
```

`ESPACE` lance un autre éclair · `ECHAP` quitte. Après la frappe, le programme
recommence tout seul : chaque éclair est différent.

## Le déroulé — et c'est ça, la vidéo

| Temps | Ce qu'on voit |
|---|---|
| 0 – 2 s | **la nuit.** Un ciel presque noir, des nuages qu'on devine, une ligne d'horizon |
| 2 – 18 s | le traceur descend. Il hésite, il essaie à gauche, à droite, il fait des branches qui n'aboutissent pas. **Il ne va jamais tout droit** |
| 12 – 18 s | il approche du sol. On le voit venir, et c'est ça qui tient : on sait ce qui va se passer, on ne sait pas quand |
| ~18,6 s | **il touche.** Tout le canal s'embrase, le ciel s'éclaire, le paysage apparaît une demi-seconde |
| +0,13 s, +0,28 s | deux répliques, plus faibles. Un éclair ne frappe presque jamais une seule fois |
| 19 – 23 s | le noir revient, il reste la trace du canal, à peine |

**Il n'y a pas de seconde à filmer : il y a une seconde à attendre.** Les seize
secondes de tâtonnement ne sont pas une introduction, c'est le sujet — et c'est
pour ça que la vidéo doit rester lente jusqu'au bout.

Selon le tirage, le canal met entre **17 et 24 secondes** à trouver le sol
(1 038 à 1 409 cases, à une case par image).

## Le détail dont je suis content : un seul bouton

Tout le caractère de l'éclair tient dans l'exposant `η` de `φ^η`. Mesuré sur
quatre tirages, jusqu'au contact avec le sol :

| `η` | cases posées | branches mortes | largeur occupée | ce que ça donne |
|---|---|---|---|---|
| 1,0 | — | — | — | une décharge grasse, qui remplit tout |
| 2,0 | 1 702 | 406 | 106 cases | un buisson : trop de branches, on perd le trait |
| **2,5** | **1 180** | **265** | **78 cases** | **un éclair** |
| 3,0 | 967 | 206 | 91 cases | plus sec, moins de branches |
| 4,0 | 647 | 116 | 69 cases | presque un trait droit : ça ne cherche plus |

À `η = 1`, la probabilité est simplement proportionnelle au champ : toutes les
directions se valent à peu près, et la décharge s'étale. Plus `η` monte, plus
l'écart entre une case un peu favorable et une case très favorable est
amplifié — et plus la décharge devient sélective, donc filiforme. À 4, elle ne
tâtonne plus du tout, et la vidéo n'a plus de sujet.

C'est le seul réglage de la physique. Tous les autres sont de la mise en scène.

## L'autre détail : un champ qu'on ne résout jamais vraiment

Résoudre Laplace proprement sur 57 600 cases, c'est des centaines d'itérations.
Le faire **à chaque case posée** — 1 200 fois — serait hors de question.

Mais on n'en a pas besoin. Au départ, la solution exacte est connue : sans
canal, le potentiel est un simple dégradé du nuage au sol, et on l'écrit
directement. Ensuite, chaque case ajoutée ne dérange le champ **que près
d'elle**. Huit passes de Jacobi par image suffisent à rattraper — et c'est ce
qui permet de tenir les 60 images par seconde.

Sauf que le nombre de passes n'est pas qu'un réglage de précision : il change
l'éclair. Mesuré sur trois tirages :

| passes par image | cases jusqu'au sol | résidu de Laplace | ms par image |
|---|---|---|---|
| 1 | 1 925 | 1,5·10⁻⁴ | 0,29 |
| 2 | 1 612 | 9,2·10⁻⁵ | 0,47 |
| 4 | 1 261 | 6,8·10⁻⁵ | 0,81 |
| **8** | **1 229** | **3,4·10⁻⁵** | **1,60** |
| 16 | 1 066 | 2,0·10⁻⁵ | 3,81 |

Moins on relaxe, plus le champ **retarde** : la pointe qui vient d'avancer n'a
pas encore vidé le potentiel autour d'elle, les vieilles branches paraissent
plus attirantes qu'elles ne le sont, et la décharge repart en arrière. Résultat,
il faut 60 % de cases en plus pour descendre la même hauteur. Entre 8 et 16
passes, l'écart tombe à 13 % : c'est là qu'on arrête de payer pour rien.

## Le détail idiot qui a coûté le plus cher : 255

L'éclat se fait en superposant une image toute prête — le ciel éclairé, le
canal, sa lueur — sur la nuit, avec une opacité qui retombe. Au premier essai,
**l'image de la frappe** — la seule qui doit absolument passer — mettait 20 ms.
Toutes les autres en mettaient 1,5.

| opacité du calque | ms |
|---|---|
| 0, 64, 128, 200, 254 | 1,0 à 2,3 |
| **255** | **20,4** |

À 255, pygame considère le calque comme opaque et bascule sur un autre chemin
de recouvrement. La correction est un `min(254, …)`. Elle ne change rien à
l'image : un pixel à 254/255 d'opacité sur un fond noir, personne ne le voit.

## Ce que ça coûte

| | ms par image |
|---|---|
| une case de croissance (bord, tirage, parent) | 0,15 |
| huit passes de relaxation | 1,54 |
| `Vue.dessiner`, image ordinaire | 1,59 |
| `Vue.dessiner`, image d'éclat | 3,59 |
| **boucle complète, `--plein` 720 × 1280** | **3,2** |
| **boucle complète, fenêtre 356 × 633** | **6,0** |

La fenêtre coûte **plus cher** que le plein format : il faut réduire l'image
720 × 1280 à la taille de la fenêtre, et cette réduction coûte 3,4 ms à elle
seule — plus que tout le reste réuni.

L'embrasement, lui, coûte 21 ms, mais il n'arrive qu'une fois : on compose
l'image entière de l'éclair au moment du contact, et pendant la seconde que dure
l'éclat il n'y a plus qu'à la mélanger au noir.

## Ce qui reste imparfait

- **Le champ n'est jamais exactement résolu.** Résidu de 3·10⁻⁵ — petit, mais le
  tableau plus haut montre que ça déplace le résultat. L'éclair qu'on voit est
  celui d'un champ légèrement en retard sur le canal.
- **Le modèle est en deux dimensions.** Un vrai éclair branche dans trois : vu
  de face, ses branches se croisent et se cachent. Ici, rien ne se recouvre
  jamais, et ça se sent — c'est propre là où ça devrait être touffu.
- **La grille se voit.** Le canal avance d'une case à la fois, en horizontal ou
  en vertical : les segments sont tous à angle droit, et à 4 pixels par case on
  distingue les marches. Les vraies décharges n'ont pas d'axes privilégiés. Une
  croissance à huit voisins adoucirait, au prix de diagonales trop droites.
- **Le sol attire uniformément.** Le relief est là pour l'image, pas pour la
  physique : une colline n'attire pas plus la foudre qu'un creux, alors qu'en
  vrai le champ se concentre sur les pointes. Il suffirait de ne pas imposer le
  même potentiel partout sur le sol.
- **Rien ne dit combien de temps ça dure.** Un traceur réel descend en 20
  millisecondes ; ici il met 18 secondes. C'est un ralenti d'un facteur mille,
  assumé — sans lui il n'y a pas de vidéo, juste un flash.

## À bricoler

Tous les chiffres ci-dessous sont mesurés, pas devinés.

| Ligne | Effet |
|---|---|
| `ETA` | 2,5. **Le seul réglage qui change la physique** — voir le tableau plus haut |
| `PAR_IMAGE` | cases posées par image. À 2, l'éclair descend deux fois plus vite et la vidéo dure 9 s au lieu de 18 |
| `RELAX` | 8 passes. En dessous de 4, le champ retarde et la décharge part en arrière |
| `NUAGE` | l'épaisseur du nuage conducteur, en haut |
| `HORIZON`, `RELIEF` | la ligne de sol et ses bosses. Décoratif : le sol attire pareil partout |
| `DEPART` | où l'éclair naît, en largeur. À `0.5`, il part du milieu et descend en louvoyant |
| `ECLATS` | les trois éclats : instant et force. C'est ce qui fait qu'on croit à un vrai éclair et pas à un fondu |
| `DECLIN` | 0,22 s : la durée d'un éclat. Plus long, ça devient une lampe qui s'éteint |
| `T_APRES` | 4,5 s de noir avant le suivant. C'est le temps qu'il faut pour que l'œil redescende |
| `TRACEUR` | la couleur du canal qui cherche. C'est le réglage le plus délicat de la vidéo : trop vif, il n'y a plus de surprise ; trop sombre, on ne voit rien pendant seize secondes |
| `ZOOM` | 4 : la grille fait 180 × 320. À 2, quatre fois plus de cases, un éclair beaucoup plus fin — et quatre fois plus cher |
