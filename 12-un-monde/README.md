# 12 — Un monde

**Accroche :** *Et si j'inventais un monde ?*

## L'idée

Il n'y a **aucune carte** dans ce programme. Il y a un nombre — la graine — et
six grilles de valeurs au hasard, de plus en plus fines, qu'on additionne :

```python
relief = grille(3) + grille(6)/2 + grille(12)/4 + ... + grille(96)/32
```

La première grille donne les continents. La dernière donne les cailloux. Les
quatre du milieu donnent tout le reste. **C'est tout le terrain.**

Ensuite, trois lectures du même relief, et rien d'autre :

- sa **hauteur** donne la couleur — océan, sable, herbe, forêt, roche, neige
- sa **pente** donne l'ombre, et donc le relief qu'on croit voir
- sa **descente** donne les rivières : on part d'un sommet, on va toujours vers
  le voisin le plus bas, et on recommence. L'eau ne fait jamais autre chose.

Change la graine, et c'est une autre planète. Le programme, lui, ne change pas.

## Lancer

```bash
python monde.py
```

`ESPACE` fabrique un autre monde · `ECHAP` quitte.

> `ESPACE` fige l'image **une seconde** : tout est recalculé d'un coup. C'est
> normal, et c'est une seconde à couper au montage.

## Le déroulé — et c'est ça, la vidéo

| Temps | Ce qu'on voit |
|---|---|
| 0 – 6 s | les six grilles s'ajoutent, du flou vers le détail — en noir et blanc |
| 6 – 9 s | la couleur arrive, et le nuage gris devient une carte |
| 9 – 11,5 s | l'ombre monte, et **la carte se met à avoir du relief** |
| 11,5 – 16,5 s | l'eau descend : les rivières se tracent de la source vers la mer |
| après | le soleil continue de tourner, très lentement. Ça ne s'arrête jamais |

C'est la **seconde 9** qu'il faut filmer : l'instant où une image plate devient
un paysage, sans qu'un seul pixel de couleur ait bougé. Seule l'ombre est
apparue.

## Le détail dont je suis content : `mettre_a_plat`

Une carte de bruit brute donne un monde différent **en proportions** à chaque
graine : l'une presque toute noyée, l'autre presque toute en neige. Une vidéo
sur trois est ratée, et on ne peut rien y faire depuis les réglages.

La fonction remplace donc chaque altitude par **son rang**, ramené entre 0 et 1.
Du coup chaque seuil de la palette *est* sa part exacte de la carte. Vérifié sur
trois graines très différentes :

| Graine | Eau | Sable | Neige |
|---|---|---|---|
| 1234567 | 38,0 % | 3,5 % | 7,0 % |
| 42 | 38,0 % | 3,5 % | 7,0 % |
| 7777777 | 38,0 % | 3,5 % | 7,0 % |

Toujours 38 % d'eau. Ce qui change d'une graine à l'autre, c'est **la forme des
continents** — c'est-à-dire la seule chose qu'on voulait voir changer.

Conséquence pratique : `MER = 0.38` ne veut pas dire « le niveau 0,38 », ça veut
dire **38 % d'eau**. Mets `0.70`, tu obtiens exactement 70 % d'océan.

## L'autre détail : le fondu qui ne coûte rien

Faire monter l'ombre, c'est calculer `couleur × (1 + (ombre − 1) × force)` à
chaque image — 2,7 millions de multiplications, **30 ms**, soit 24 images par
seconde pendant les 2,5 s les plus belles du film.

Mais cette formule est exactement un fondu linéaire entre la carte plate et la
carte éclairée. Autant le laisser faire à la carte graphique :

```python
toile.blit(m.plat, (0, 0))
soleil.set_alpha(int(255 * releve))
toile.blit(soleil, (0, 0))
```

Deux blits, **moins de 3 ms au lieu de 30**, la même image à un niveau près —
et la révélation du relief passe de 24 à 60 images par seconde. Sur les 150
images de ce passage, il y en avait 100 au-dessus du budget de 16,7 ms ; il en
reste 1.

Le reste de `eclairer()` écrit dans des tampons déjà réservés (`out=`), au lieu
de construire quatre tableaux de 3,7 Mo par ligne de calcul : **30 ms au lieu de
44** quand il faut vraiment recalculer. Sur tout le film, 61 % de travail en
moins.

## Ce qui reste imparfait

Une fois tout en place, le soleil tourne, et chaque pas de 0,01 radian force un
recalcul complet — **9 fois par seconde, 30 ms chacun**. L'image est quasiment
immobile à ce moment-là, donc ça ne se voit pas à l'œil ; mais un
enregistreur qui capture à 60 i/s dupliquera quelques images. Si ça te gêne au
montage, ralentis la rotation (le `0.09` dans `main`) plutôt que d'élargir le
pas.

## À bricoler

Tous les chiffres ci-dessous sont mesurés, pas devinés.

| Ligne | Effet |
|---|---|
| `MER` | **c'est la part d'eau, directement.** `0.20` : un monde sec. `0.70` : un archipel |
| `CELLULES` | `3` : quelques grandes masses. `6` : beaucoup d'îles (2,7 fois plus de côtes) |
| `OCTAVES` | `2` : des collines molles, 0,23 s de calcul. `8` : rugueux, 1,0 s. À 6, on est au bon endroit |
| `LISSAGE_RIVIERES` | `0` : 41 rivières au lieu de 66, et plus courtes — elles tombent dans le premier trou venu. `8` : 73, plus longues, mais elles ignorent le terrain |
| `NB_RIVIERES` | une sur deux seulement survit au filtre des 12 pas. `400` en donne 215 |
| `TERRAIN` | les onze couleurs, du fond de l'océan à la neige |
| `T_OCTAVES` … `T_RIVIERES` | le minutage des quatre temps du film |
| `2.35` dans `main` | la direction du soleil. C'est elle qui décide de quel côté tombent les ombres |
