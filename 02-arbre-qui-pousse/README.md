# 02 — L'arbre qui pousse

**Accroche :** *Et si je faisais pousser un arbre ?*

## L'idée

Il n'y a pas d'arbre dans ce code. Il y a **une règle, répétée dix fois** :

> une branche, c'est un trait — puis deux branches plus petites au bout.

C'est tout. L'arbre, c'est ce que la règle devient. 4 700 branches sortent de
ces quatre lignes-là, et aucune n'a été écrite à la main.

## Lancer

```bash
python arbre.py
```

`ESPACE` replante un arbre différent · `ECHAP` quitte.

La fenêtre fait 720 × 1280 — du 9:16, prêt à filmer sans recadrage.

## Le déroulé

| Temps | Ce qui se passe |
|---|---|
| 0 – 11 s | l'arbre pousse, génération par génération |
| 9 – 12 s | les fleurs s'ouvrent au bout des plus petites branches |
| après | le vent, en boucle, indéfiniment |

## Filmer

Appuie sur `ESPACE` **au moment exact où la musique démarre** : la pousse et le
morceau partent ensemble. Laisse tourner 15 secondes, puis 5 secondes de vent
pour finir sur du calme.

Essaie plusieurs `ESPACE` avant d'enregistrer — certaines graines donnent des
arbres bien plus beaux que d'autres.

## À bricoler

| Ligne | Effet |
|---|---|
| `PROFONDEUR` | 12 = un arbre immense (et plus lent), 7 = un arbuste |
| `FEUILLES` | la couleur des fleurs — des ors pour l'automne |
| `VENT` | le `0.030` : monte-le à `0.08` et c'est la tempête |
| `0.70, 0.82` dans `Branche` | à quel point les branches rétrécissent |
| `0.13` dans `nb = 2 if ...` | la fréquence des branches en trop |

## Pourquoi c'est rapide

Deux mille fleurs par image, ça ne se dessine pas deux mille fois : une fleur est
**une petite image préparée une seule fois au démarrage**, à chaque taille
d'éclosion. Ensuite on ne fait plus que la coller. C'est ce qui fait passer
l'animation de 23 à 37 images par seconde.
