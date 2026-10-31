# 03 — La lettre de poussière

**Accroche :** *Et si des mots étaient faits de poussière ?*

## L'idée

1. On écrit une phrase **une seule fois**, dans une image que personne ne verra.
2. On note où sont les pixels allumés : ce sont des destinations.
3. On lâche 12 000 grains, et on leur dit une seule chose : *va vers ton point.*

Aucun grain ne sait qu'il écrit une lettre. Il n'en connaît qu'un pixel.
Puis on leur retire leur destination — et la phrase se défait.

## Lancer

```bash
python poussiere.py
```

`ESPACE` passe à la phrase suivante · `ECHAP` quitte.

## Écrire tes phrases

Tout est en haut du fichier, dans `PHRASES`. Rien d'autre à toucher :

```python
PHRASES = [
    "ta première phrase",
    "la deuxième,\nsur deux lignes",
    "merci",
]
```

`\n` = un saut de ligne. **Trois lignes courtes valent mieux qu'une longue** —
la police rapetisse au-delà de 22 caractères et les grains se dispersent.

## Le déroulé, par phrase

| Temps | Ce qui se passe |
|---|---|
| 0 – 3,2 s | les grains arrivent et s'assemblent |
| 3,2 – 6,2 s | la phrase tient, et respire |
| 6,2 – 9,6 s | elle s'érode, s'élève, s'éteint |

Puis la suivante, en boucle.

**La phrase ne se défait pas d'un coup.** Chaque grain a son propre instant de
départ : la phrase s'effrite pendant deux bonnes secondes avant de lâcher. C'est
toute la différence entre une explosion — qui est laide — et un effacement.

## Filmer

L'érosion est le plus beau moment : **ne coupe jamais dessus.** Laisse-la finir.
Si tu ne veux qu'une seule phrase à l'écran, mets-en une seule dans `PHRASES` —
elle se reformera en boucle.

## À bricoler

| Ligne | Effet |
|---|---|
| `TRAINEE` | `0.95` = longues traînées de comète, `0.5` = net et sec |
| `TEINTES` | la couleur des grains |
| `NB_GRAINS` | `25000` = lettres pleines, mais plus lourd |
| `VOL` / `REPOS` / `CHUTE` | le rythme des trois temps |
| `MONTEE` | `-34` = ça s'élève ; mets `+34` et la phrase retombe |
| `TOURNOIE` | monte-le à `80` et les grains partent en tourbillon |
| `0.45` dans `envol` | l'étalement des départs : `0.0` = tout part d'un coup |
