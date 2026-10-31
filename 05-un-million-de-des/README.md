# 05 — Un million de dés

**Accroche :** *Et si je lançais un dé un million de fois ?*

## L'idée

On lance cinq dés, on note la somme, on recommence. C'est **tout** le programme.

Personne ne dessine de courbe. Personne ne calcule de moyenne. On empile
bêtement des résultats — et au bout d'un moment une forme apparaît, toujours la
même, que personne n'a demandée.

À la fin, on superpose la courbe que les maths avaient prévue **avant** qu'on
lance quoi que ce soit. Elle tombe pile dessus.

C'est le théorème central limite. Mais on n'a pas besoin de le nommer pour le
voir : c'est bien ça qui rend la vidéo bonne.

## Lancer

```bash
python des.py
```

`ESPACE` recommence · `ECHAP` quitte.

## Le déroulé

| Temps | Compteur | Ce qu'on voit |
|---|---|---|
| 2 s | **1** | un seul lancer. Cinq dés, une barre d'un pixel. |
| 9 s | ~125 | ça part dans tous les sens, aucune forme |
| 16 s | ~16 000 | la cloche se devine |
| 22 s | **1 000 000** | elle est parfaite |
| 22 – 24 s | | la courbe théorique se pose dessus |

Le compteur monte **par puissances de dix**, pas linéairement. C'est la seule
façon de voir à la fois le premier lancer et le millionième dans la même vidéo :

```python
return min(OBJECTIF, int(10.0 ** (math.log10(OBJECTIF) * avance)))
```

## Filmer

Le moment de la vidéo, c'est **la seconde 22** : quand la courbe bleue se pose
sur les barres et qu'elle colle. Cale-la sur le temps fort de la musique et ne
coupe pas avant 4 secondes après.

Ne coupe pas non plus le début : les 125 premiers lancers, qui ne ressemblent à
rien, sont ce qui rend la fin impressionnante.

## À bricoler

| Ligne | Effet |
|---|---|
| `NB_DES` | `1` : la courbe ne vient jamais, tout reste plat (et c'est instructif). `2` : un triangle. `5` : la cloche. **Fais la vidéo avec 1, puis 2, puis 5.** |
| `FACES` | `20` pour des dés de jeu de rôle |
| `OBJECTIF` | `10_000_000` — ça tient encore |
| `DUREE` | la durée de la montée |
| `BARRE` / `COURBE` | les deux couleurs qui comptent |

## Vérifié

À un million de lancers : total exact `1 000 000`, somme la plus fréquente `18`
(la moyenne théorique vaut 17,5 — il n'y a pas de somme entière à 17,5, donc 17
et 18 se partagent le sommet). 83 images/seconde.
