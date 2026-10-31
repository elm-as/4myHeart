# 06 — Une horloge

**Accroche :** *Et si je codais une horloge de zéro ?*

## L'idée

Il n'y a pas un seul fichier image dans ce dossier. Pas de dessin, pas de police
d'icônes, rien. Un cercle, soixante traits, trois aiguilles — et **une formule** :

```
angle = 2π × (ce qui est passé / ce qui fait un tour)
```

Puis, pour poser un point sur le cercle à cet angle :

```python
x = centre + math.sin(angle) * rayon
y = centre - math.cos(angle) * rayon
```

Le sinus et le cosinus sont inversés par rapport à l'habitude, et le `y` est
soustrait. Les deux pour la même raison : on veut que zéro soit **en haut** et
que ça tourne **dans le sens des aiguilles**. Ce qui, ici, tombe bien.

Ces quatre lignes font tout : les traits, les trois aiguilles, et le fil rouge
du pourtour.

## Lancer

```bash
python horloge.py
```

`ESPACE` refait le dessin depuis le début · `ECHAP` quitte.

Elle affiche **ton heure réelle**.

## Le déroulé

| Temps | Ce qui se passe |
|---|---|
| 0 – 1,4 s | le cercle se trace, d'un seul trait, en partant du haut |
| 1,4 – 3,1 s | les soixante traits sortent un par un |
| 3,1 – 4 s | les aiguilles partent de midi et **tournent** jusqu'à l'heure juste |
| après | l'heure, et le fil rouge qui fait le tour à chaque minute |

La trotteuse est **fluide**, pas saccadée : elle utilise la fraction de seconde.
C'est un détail d'une ligne, et c'est ce qui fait la différence entre une montre
à quartz bon marché et une belle mécanique.

## Filmer

Filme-la **à une heure ronde moins une minute**. Comme ça la vidéo finit sur les
trois aiguilles qui se rejoignent, ou sur le passage à l'heure pile.

Sinon : lance-la à `H:59:30`, et laisse tourner jusqu'à `H+1:00:05`.

## À bricoler

| Ligne | Effet |
|---|---|
| `SECONDE` | la couleur du fil rouge |
| `RAYON` | la taille. Au-delà de `300` ça touche les bords |
| `TRACE_CERCLE` / `TRACE_TRAITS` / `TRACE_MAINS` | le rythme du dessin initial |
| `maintenant()` | remplace `time.localtime()` par un compte à rebours, et l'objet change de sens |
| `SS` | `2` pour des bords encore plus lisses (et ~30 images/s au lieu de 48) |
