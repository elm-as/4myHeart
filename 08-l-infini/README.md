# 08 — L'infini

**Accroche :** *Et si je dessinais l'infini ?*

## L'idée

Toute l'image tient dans cette répétition :

```
z ← z² + c
```

On la répète pour chaque point `c` du plan. Si `z` file vers l'infini, on colorie
le point selon le **temps qu'il a mis à partir**. S'il ne part jamais, on le
laisse noir.

C'est tout. Il n'y a rien d'autre dans ce programme.

Le noir qu'on voit est donc l'ensemble des points qui restent. Et son bord n'a
pas de fin : on peut descendre indéfiniment, il y aura toujours de la structure,
toujours nouvelle, toujours la même.

## Lancer

```bash
gcc infini.c -o infini -lm -O3 -march=native -fopenmp
python voir.py
```

`ECHAP` quitte. La descente dure 28 secondes, puis remonte et recommence.

Deux fichiers, parce que le C calcule vite mais ne sait pas ouvrir de fenêtre,
et que Python ouvre des fenêtres mais calcule 300 fois trop lentement (mesuré :
2,8 secondes par image en numpy). Chacun fait ce qu'il sait faire.

## Le truc dont je suis le plus content

Le C ne calcule pas 60 images par seconde — il en calcule 5 quand ça devient
profond. Beaucoup trop peu pour que la descente soit fluide.

**On ne lui demande pas de suivre.** Chaque image est estampillée de l'instant
auquel elle correspond ; en attendant la suivante, la fenêtre continue de zoomer
*dedans*, en recadrant son centre :

```python
facteur = exp(VITESSE * (mon_temps - instant))
cadre = Rect(centre, LARGEUR / facteur, HAUTEUR / facteur)
```

Deux images successives ne diffèrent que de quelques pour cent d'échelle :
personne ne voit la couture, et le zoom ne s'arrête jamais. C'est exactement ce
que font les vrais explorateurs de fractales.

## Pourquoi ça s'arrête à ×50 000

Le `double` tient jusqu'à un grossissement de 10¹³. Mais plus on descend, plus
il faut d'itérations pour distinguer *« part très tard »* de *« ne part
jamais »*. Passé une certaine profondeur, avec un plafond de 620 itérations,
tout est déclaré intérieur et **l'écran devient entièrement noir**.

Descendre plus bas demanderait des milliers d'itérations — et une image toutes
les deux secondes. Monte `MAXI_PLAFOND` et `FIN` ensemble si tu veux essayer,
mais regarde le compteur d'images avant de lancer l'enregistrement.

## Filmer

Plan fixe, 28 secondes, aucune coupe. Le compteur `x 5e+04` en bas est là exprès :
c'est lui qui dit au spectateur ce qui est en train de se passer.

Si tu veux une descente plus lente et plus contemplative, baisse `VITESSE` à
`0.25` dans **les deux fichiers** (ils doivent rester d'accord).

## À bricoler

| Ligne | Effet |
|---|---|
| `CIBLE_RE` / `CIBLE_IM` | l'endroit où l'on tombe. Chaque point donne un autre monde |
| `teinter()` | les trois cosinus. Change les déphasages `0.00 / 0.14 / 0.28` |
| `0.25 * sqrt(mu)` | la largeur des bandes de couleur |
| `VITESSE` | la vitesse de chute (à changer dans `infini.c` **et** `voir.py`) |
| `LARGEUR` / `HAUTEUR` | `540 x 960` pour plus de finesse, si ta machine suit |

## Mesuré

| Profondeur | Itérations | Images/s calculées |
|---|---|---|
| ×1 | 90 | 102 |
| ×1 500 | 236 | 42 |
| ×50 000 | ~314 | ~20 |

Moyenne sur toute la descente : **48 images calculées par seconde**, affichage à 60.
