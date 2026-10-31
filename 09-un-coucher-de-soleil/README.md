# 09 — Un coucher de soleil

**Accroche :** *Et si je codais un coucher de soleil ?*

## L'idée

Aucune photo, aucune texture, aucun dégradé tout fait.

Le ciel entier tient dans **quatre listes de couleurs** — quatre moments de la
soirée : le jour, l'or, la braise, la nuit. À chaque instant, on fabrique le ciel
en mélangeant les deux moments qui entourent l'heure qu'il est. Une
interpolation, rien de plus.

Et la mer n'est pas peinte non plus. C'est le ciel, retourné et assombri :

```python
mer[y] = ciel[2 * HORIZON - y] * facteur
```

Une ligne. Le soleil s'y reflète tout seul, et les couleurs du soir aussi — parce
que ce sont littéralement les mêmes.

## Lancer

```bash
python coucher.py
```

`ESPACE` recommence la soirée · `ECHAP` quitte. Durée : 42 secondes.

## Le déroulé

| Temps | Ce qu'on voit |
|---|---|
| 0 – 14 s | fin d'après-midi, le soleil descend |
| 14 – 22 s | il touche l'eau, le ciel s'embrase |
| 22 – 26 s | il disparaît. Le chemin de lumière s'éteint |
| **28 s** | **la première étoile.** Une seule. |
| 30 – 42 s | les 149 autres arrivent, chacune à son heure |

## Filmer

Toute la vidéo existe pour **la seconde 28**. Une étoile, seule, dans un ciel
encore rouge. Cale-la sur le moment où la musique s'ouvre, et ne coupe surtout
pas avant que les autres soient arrivées.

Si tu veux que ce soit plus lent, monte `DUREE`. Tout le reste suit — rien n'est
écrit en secondes dans le code, tout est écrit en **parts de soirée**.

## Deux pièges que j'ai dû corriger

**Le soleil.** Son halo est collé en addition, et une addition **ignore le canal
alpha**. Écrire la décroissance de la lueur dans l'alpha ne sert donc à rien :
les soixante cercles s'additionnent tous à pleine intensité et le soleil devient
un disque blanc plat. La décroissance doit être dans la *couleur* — du gris de
plus en plus sombre.

**Les étoiles.** Peintes par-dessus le ciel, elles apparaissaient **noires** :
une étoile encore pâle est plus sombre que le ciel qui l'entoure. Une étoile
n'écrase pas le ciel, elle lui **ajoute** de la lumière :

```python
ecran.fill((c, c, c + 16), (x, y, 2, 2), special_flags=pygame.BLEND_RGB_ADD)
```

## À bricoler

| Ligne | Effet |
|---|---|
| `MOMENTS` | **le cœur du fichier.** Quatre moments × quatre couleurs. Change-les et c'est une autre planète |
| `HORIZON` | monte-le à `950` : un ciel immense. Descends-le à `500` : une mer immense |
| `PREMIERE_ETOILE` | à quelle part de la soirée elle arrive |
| `SOLEIL_X` | décale-le : à `0.5` c'est symétrique et plus froid |
| `couleur_du_soleil()` | blanc → or → orange → rouge. Les quatre étapes du disque |
| `DUREE` | la longueur de la soirée |

93 à 128 images par seconde.
