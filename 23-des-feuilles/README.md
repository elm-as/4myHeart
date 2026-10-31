# 23 — Des feuilles

**Accroche :** *Et si des feuilles tombaient ?*

## L'idée

Une pierre tombe en ligne droite. Une feuille, elle, hésite.
Elle n'a pas de moteur mais elle plane : l'air sous elle la repousse,
elle s'incline, prend de la vitesse sur le côté, puis décroche et bascule
dans l'autre sens.

Cette oscillation pendulaire s'appelle le *fluttering*. Quand le vent
souffle plus fort, la feuille s'enroule sur elle-même en toupie (*tumbling*)
ou se fait emporter dans un tourbillon ascendant.

```
F_portance ∝ v² · sin(2θ)
F_traînée  ∝ v² · cos²(θ)
```

Et au sol, les feuilles mortes restent : le tapis s'épaissit,
formant un parterre d'ambre et de cuivre sous la brume d'automne.

## Lancer

```bash
python feuilles.py
```

`ESPACE` déclenche une bourrasque de vent · `ECHAP` quitte.

## Le déroulé

| Temps | Vent | Ce qu'on voit |
|---|---|---|
| 0 – 3 s | Brise calme | Le silence d'automne : les premières feuilles se détachent et oscillent doucement |
| 4 – 14 s | Vent montant | Les feuilles prennent de la gîte, basculent sur la tranche et zigzaguent |
| 15 – 28 s | Bourrasque | Tourbillons ascendants, volées de feuilles cuivrées qui dansent |
| 28 – 45 s | Rafales douces | Le parterre s'illumine au sol, les feuilles tombées frémissent au vent |

## Le détail dont je suis content : la rotation 3D sur la tranche

Une feuille n'est pas un rectangle 2D qui glisse. Elle a un recto éclairé
et un verso plus sombre. Quand elle pivote sur elle-même, son profil
s'écrase en `cos(φ)` :

```python
px_3d = px * math.cos(self.phi)
```

À `φ = π/2`, la feuille est vue strictement par la tranche : elle ne fait
qu'un pixel d'épaisseur, comme un trait de plume suspendu dans l'air,
puis elle dévoile sa face sombre en se retournant.

## À bricoler

| Variable | Effet |
|---|---|
| `NB_FEUILLES` | 180 : la densité de la nuée automnale |
| `COULEURS_FEUILLES` | La palette — ocre, pourpre, carmin, or et rouille |
| `portance_mag` | L'amplitude du zigzag latéral (*fluttering*) |
| `couple_rappel` | La vitesse à laquelle la feuille cherche à se redresser |
| `vent_base` | La force et la direction de la brise atmosphérique |
