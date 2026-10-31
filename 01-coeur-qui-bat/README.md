# 01 — Le cœur qui bat

**Accroche :** *Et si une équation avait un cœur ?*

## L'idée

Il n'y a pas de dessin dans ce programme. Il y a une inégalité :

```
(x² + y² − 1)³ − x²y³  ≤  0
```

Tous les points qui la vérifient sont à l'intérieur d'un cœur. Le programme
demande simplement à chaque caractère du terminal : *« est-ce que tu es dedans ? »*

Le battement n'est pas un clignotement : c'est deux coups rapprochés, un petit
puis un grand, comme un vrai cœur.

## Lancer

```bash
gcc coeur.c -o coeur -lm -O2
./coeur "je pense à toi"
```

Le message est optionnel. Sans argument, il n'y a que le cœur.

## Filmer

1. Windows Terminal, thème sombre, zoom au maximum (`Ctrl` + molette).
2. La fenêtre doit faire **au moins 84 × 36 caractères**, sinon l'image se replie.
3. Montre d'abord **l'équation seule à l'écran**, 2 secondes. C'est l'accroche.
4. Puis le code, puis `gcc`, puis `./coeur`.
5. Laisse battre **20 secondes sans couper**.

`Ctrl + C` pour arrêter.

## À bricoler

| Ligne | Effet |
|---|---|
| `LARGEUR` / `HAUTEUR` | taille du cœur |
| `COULEURS[]` | la palette — essaie des bleus pour quelque chose de plus froid |
| `battement()` | le rythme : rapproche les deux coups, il s'affole |
| `0.13` dans `pulsation` | l'amplitude du battement |
