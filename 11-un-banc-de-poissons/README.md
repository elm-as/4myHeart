# 11 — Un banc de poissons

**Accroche :** *Et si des poissons suivaient trois règles ?*

## L'idée

Il n'y a pas de chef dans ce programme. Pas de trajectoire écrite, pas de forme
prévue. Chaque poisson ne connaît que ses voisins immédiats, et ne suit que
**trois règles** :

1. ne pas coller ses voisins
2. aller dans le même sens qu'eux
3. ne pas trop s'en éloigner

Le banc n'est écrit nulle part. **Il apparaît.**

## Lancer

```bash
python banc.py
```

`ESPACE` recommence · `P` lâche le prédateur tout de suite · `ECHAP` quitte.

## Le déroulé — et c'est ça, la vidéo

Les trois règles s'allument **une par une**, et on peut mesurer ce que chacune
apporte. `accord` vaut 0 si chacun nage dans son coin, 1 si tous vont exactement
dans le même sens :

| Temps | Règles | Étalement | Accord | Ce qu'on voit |
|---|---|---|---|---|
| 5 s | aucune | 396 px | **0,04** | du désordre |
| 12 s | + séparation | 377 px | 0,06 | une nuée régulière, toujours sans direction |
| 19 s | + alignement | 364 px | **0,27** | des courants se forment |
| 30 s | + cohésion | **161 px** | **0,82** | un animal |
| 38 s | (prédateur) | 115 px | **1,00** | il fuit d'un seul bloc |

C'est la **seconde 21** qu'il faut filmer : le moment où la troisième règle
s'allume et où la nuée devient une bête.

## Les deux réglages qui décident de tout

Ce projet m'a pris deux essais ratés avant de marcher, et pour deux raisons
différentes :

**L'équilibre des forces.** Avec une cohésion trop forte devant la séparation,
le banc ne se forme pas : il **s'effondre en boules compactes et immobiles**. Il
a fallu monter la séparation d'un facteur 44.

**Les rayons de perception.** Avec 1 200 poissons qui ne voient qu'à 95 pixels,
on n'obtient jamais *un* banc — seulement un essaim qui remplit l'aquarium
uniformément (accord bloqué à 0,35). Moins de poissons qui voient plus loin, et
le banc se forme enfin. Les trois rayons comptent autant que les trois forces.

## Le détail technique dont je suis content

Les trois règles sont écrites **sans une seule boucle**. Chacune est une
multiplication de matrices :

```python
accel += P_ALIGNEMENT * ((proches @ vit) / combien - vit)
```

Et les distances entre les 250 000 couples se calculent sans jamais construire
le tableau des différences, avec l'identité `|a−b|² = |a|² + |b|² − 2a·b` :

```python
dist2 = carres[:, None] + carres[None, :] - 2.0 * (pos @ pos.T)
```

Résultat : **168 images par seconde** alors que chaque poisson regarde tous les
autres, à chaque image.

## À bricoler

| Ligne | Effet |
|---|---|
| `P_COHESION` | monte-le à `4` et regarde le banc s'effondrer en boules. C'est instructif |
| `R_COHESION` | `60` : plusieurs petits bancs indépendants au lieu d'un seul |
| `NB` | `1500` et ça redevient un essaim qui remplit tout |
| `ETAPES` | quand chaque règle s'allume, et le texte affiché |
| `P_FUITE` / `R_PREDATEUR` | la panique |
| `PREDATEUR_A` | `999` pour qu'il ne vienne jamais |
