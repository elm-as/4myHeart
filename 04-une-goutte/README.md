# 04 — Une goutte

**Accroche :** *Et si je faisais tomber une goutte ?*

## L'idée

Il n'y a aucune image dans ce programme. Il y a un lac vu de biais, et **une
seule ligne de maths** :

```
échelle = F / Z
```

Un point à la distance `Z` est d'autant plus petit, et d'autant plus proche de
l'horizon, que `Z` est grand. Tout le reste en découle.

Et le plus beau tient dans une deuxième ligne. Un rond dans l'eau est un cercle —
mais vu de biais, un cercle est une **ellipse**, d'autant plus écrasée qu'elle est
loin. Cet écrasement vaut exactement `H / Z` :

```python
ry = rx * H / ride.z
```

C'est pour ça que les ronds du fond ressemblent à des traits et ceux du bord à
des cercles. Personne ne l'a dessiné. C'est la géométrie qui le fait.

## Lancer

```bash
python pluie.py
```

`ESPACE` recommence depuis la première goutte · `ECHAP` quitte.

## Le déroulé

| Temps | Ce qui se passe |
|---|---|
| 0 – 1,2 s | rien. Le lac, le noir. |
| **1,2 s** | **une goutte.** Une seule. Elle tombe, elle touche, un rond s'ouvre. |
| 1,2 – 4,5 s | le rond s'élargit, s'efface. Le silence revient. |
| 4,5 – 17 s | l'averse s'installe, doucement, puis complètement |
| après | ~600 gouttes en l'air, ~850 ronds sur l'eau, indéfiniment |

**C'est le silence entre 1,2 s et 4,5 s qui fait la vidéo.** Ne le raccourcis pas.
Une goutte, puis plus rien pendant trois secondes, puis tout.

## Filmer

Cale la première goutte sur la première note. Et laisse tourner **au moins
25 secondes** : la montée de l'averse est lente exprès, c'est elle le sujet.

## Le détail dont je suis content

Les gouttes ne tombent pas au hasard **à l'écran** : elles tombent au hasard
**sur le lac**. Ce n'est pas pareil. Une bande lointaine du lac est immense et
n'occupe que trois pixels ; une bande proche est minuscule et remplit le bas de
l'image. Tirer la profondeur uniformément ferait tomber toute la pluie sur nos
pieds — il faut tirer proportionnellement à la surface :

```python
z = math.sqrt(PROCHE**2 + random.random() * (LOIN**2 - PROCHE**2))
```

Ce `sqrt` est toute la différence entre une flaque et un lac.

## À bricoler

| Ligne | Effet |
|---|---|
| `HORIZON` | monte-le à `250` : on domine le lac. Descends-le à `600` : on est dedans |
| `H` | la hauteur de la caméra. `2.0` = à ras de l'eau, les ronds s'aplatissent tous |
| `AVERSE` | `340` gouttes/s. À `800` c'est un déluge (et ça rame) |
| `VIE_RIDE` | combien de temps un rond survit |
| `LUEUR` | la couleur. Essaie un ambre `(220, 180, 130)` : ça devient un lac au couchant |
| `SILENCE` | la durée du vide après la première goutte. **Le réglage le plus important** |
