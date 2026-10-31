# 10 — Un trou noir

**Accroche :** *Et si je mettais un trou noir au milieu ?*

## L'idée

Personne ne dessine de disque ici. On lâche vingt mille poussières autour d'un
point, avec **une seule loi** — celle de Newton, vieille de 1687 :

```python
self.vit += vers * (GM * dt / (r2 * r))[:, None]
```

Et un frottement minuscule, parce que ces poussières se frottent les unes aux
autres. C'est tout le programme.

Le nuage s'organise seul en disque, parce que les orbites qui vont à contresens
s'annulent et que seules survivent celles qui tournent dans le même sens. Puis le
frottement leur fait perdre, tour après tour, ce qui les tenait en l'air — et
elles tombent.

Le rond noir au centre n'est pas dessiné non plus. C'est juste **l'endroit d'où
l'on ne revient pas**.

La couleur, elle, n'est pas décorative : c'est la **vitesse**. Rouge sombre loin,
blanc bleuté tout près. Ce qui explique pourquoi le centre brûle.

## Lancer

```bash
python trou_noir.py
```

`ESPACE` relance un nuage neuf · `ECHAP` quitte.

## Le déroulé

| Temps | Rayon moyen | Ce qu'on voit |
|---|---|---|
| 1,5 s | 462 px | un nuage désordonné |
| 8 s | 292 px | le disque se forme, les premières tombent |
| 20 s | 179 px | un vrai disque d'accrétion, brûlant au centre |
| 40 s | 227 px | l'équilibre : ce qui tombe est remplacé au loin |

## Filmer

Les **huit premières secondes** sont les plus précieuses : c'est le moment où le
désordre devient une forme. Ne les coupe pas au montage, même si « il ne se passe
rien ».

Puis laisse tourner 30 secondes de plus. Ça ne s'arrête jamais.

## À bricoler

| Ligne | Effet |
|---|---|
| `FROTTEMENT` | `0.0` : les orbites tiennent pour toujours, rien ne tombe. `0.15` : tout s'effondre en dix secondes |
| `GM` | la masse. Double-la et tout accélère |
| `HORIZON` | la taille du rond noir |
| `TRAINEE` | `0.96` : de longues comètes qui tracent les orbites |
| `palette()` | les six couleurs, de la plus lente à la plus rapide |
| `0.72, 1.06` dans `semer()` | l'écart à l'orbite ronde — c'est lui qui fait les vagues du disque |
| `NB` | `60000` si ta machine suit (ici : 20 000 à 49 images/s) |
