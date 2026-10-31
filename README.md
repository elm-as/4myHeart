# 4myHeart

Des programmes courts qui font quelque chose de beau, filmés et montés sur une
musique douce. Pas de tutoriel, pas de voix off, pas d'explication.

**Une idée → du code → `RUN` → la magie.**

---

## La recette (ne jamais en sortir)

| Temps | Ce qu'on voit |
|---|---|
| 0 – 2 s | **Une phrase.** « Et si je faisais pousser un arbre ? » |
| 2 – 8 s | **Le code défile.** On ne le lit pas, on le sent. Scroll lent. |
| 8 – 10 s | **`RUN`.** Le silence juste avant. |
| 10 – 40 s | **Le résultat.** C'est tout. On laisse respirer. |

Trois règles :

1. **Ça doit se comprendre sans un mot.** Si tu dois expliquer, l'idée est mauvaise.
2. **Le résultat doit être plus beau que le code.** Toujours.
3. **Pas de coupe pendant le résultat.** Le plan long est ce qui rend la chose hypnotique.

---

## Les projets

| # | Dossier | Langage | Ce qu'on voit | Durée |
|---|---|---|---|---|
| 01 | [`01-coeur-qui-bat`](01-coeur-qui-bat) | C | Une équation devient un cœur, et il bat | ~20 s |
| 02 | [`02-arbre-qui-pousse`](02-arbre-qui-pousse) | Python | Une graine devient un cerisier en fleur | ~15 s |
| 03 | [`03-lettre-de-poussiere`](03-lettre-de-poussiere) | Python | 12 000 grains s'assemblent en une phrase, puis s'envolent | ~10 s / phrase |
| 04 | [`04-une-goutte`](04-une-goutte) | Python | Une goutte sur un lac, puis l'averse, en perspective | ~30 s |
| 05 | [`05-un-million-de-des`](05-un-million-de-des) | Python | Un million de lancers, et la courbe en cloche apparaît seule | ~25 s |
| 06 | [`06-une-horloge`](06-une-horloge) | Python | Une horloge se dessine elle-même, sans une seule image | ~60 s |
| 07 | [`07-de-la-neige`](07-de-la-neige) | Python | Il neige — et la neige **reste** : le paysage change | ~80 s |
| 08 | [`08-l-infini`](08-l-infini) | C + Python | Une ligne de maths, et on y tombe jusqu'à ×50 000 | ~28 s |
| 09 | [`09-un-coucher-de-soleil`](09-un-coucher-de-soleil) | Python | Ciel → soleil → mer → la première étoile | ~42 s |
| 10 | [`10-un-trou-noir`](10-un-trou-noir) | Python | Un nuage s'organise en disque et tombe | ~40 s |
| 11 | [`11-un-banc-de-poissons`](11-un-banc-de-poissons) | Python | 3 règles allumées une par une → un banc apparaît | ~40 s |
| 12 | [`12-un-monde`](12-un-monde) | Python | Un nombre devient un continent, avec ses rivières | ~30 s |
| 13 | [`13-une-explosion`](13-une-explosion) | Python | Un point, puis 5 000 éclats qui refroidissent et retombent | ~28 s |
| 14 | [`14-des-fourmis`](14-des-fourmis) | Python | 1 200 fourmis sans chef, et des autoroutes apparaissent | ~40 s |
| 15 | [`15-de-la-gravite`](15-de-la-gravite) | Python | Un nuage tombe sur lui-même et devient un système | ~45 s |
| 16 | [`16-du-sable-qui-chante`](16-du-sable-qui-chante) | Python | 80 000 grains fuient le bruit, et la figure apparaît | ~48 s |
| 17 | [`17-du-feu`](17-du-feu) | Python | Trois braises dans le noir, et tout le sol finit par brûler | ~45 s |
| 18 | [`18-de-la-foudre`](18-de-la-foudre) | Python | Elle cherche le sol pendant 18 s, puis elle le trouve | ~23 s |
| 19 | [`19-un-flocon`](19-un-flocon) | Python | Une case de glace, et la symétrie à six sort toute seule | ~32 s |
| 20 | [`20-de-l-eau`](20-de-l-eau) | Python | 1 408 points qui refusent d'être serrés, et ça fait une vague | ~30 s |
| 21 | [`21-une-ville`](21-une-ville) | Python | Un rectangle coupé en deux, 127 fois, puis les lumières | ~38 s |
| 22 | [`22-une-galaxie`](22-une-galaxie) | Python | 110 000 étoiles, l'onde de densité de Lindblad forme deux bras spiraux | ~40 s |
| 23 | [`23-des-feuilles`](23-des-feuilles) | Python | Aérodynamique, portance et spirales de feuilles mortes au vent | ~45 s |

La suite est dans [**IDEES.md**](IDEES.md).

---

## Lancer

```bash
pip install pygame numpy          # une seule fois

python 02-arbre-qui-pousse/arbre.py           # ESPACE = replanter
python 03-lettre-de-poussiere/poussiere.py    # ESPACE = phrase suivante
python 04-une-goutte/pluie.py                 # ESPACE = recommencer
python 05-un-million-de-des/des.py
python 06-une-horloge/horloge.py
python 07-de-la-neige/neige.py                # ESPACE = déneiger
python 09-un-coucher-de-soleil/coucher.py     # ESPACE = recommencer la soirée
python 10-un-trou-noir/trou_noir.py           # ESPACE = relancer le nuage
python 11-un-banc-de-poissons/banc.py         # ESPACE = recommencer, P = prédateur
python 12-un-monde/monde.py                   # ESPACE = un autre monde
python 13-une-explosion/explosion.py          # ESPACE = une autre explosion
python 14-des-fourmis/fourmis.py              # ESPACE = une autre colonie
python 15-de-la-gravite/gravite.py            # ESPACE = un autre nuage
python 16-du-sable-qui-chante/sable.py        # ESPACE = on redisperse le sable
python 17-du-feu/feu.py                       # ESPACE = on rallume
python 18-de-la-foudre/foudre.py              # ESPACE = un autre eclair
python 19-un-flocon/flocon.py                 # ESPACE = un autre flocon
python 20-de-l-eau/eau.py                     # ESPACE = on remonte le barrage
python 21-une-ville/ville.py                  # ESPACE = une autre ville
python 22-une-galaxie/galaxie.py              # ESPACE = une autre galaxie
python 23-des-feuilles/feuilles.py            # ESPACE = une bourrasque
```

Les deux projets en C :

```bash
cd 01-coeur-qui-bat
gcc coeur.c -o coeur -lm -O2
./coeur "je pense à toi"

cd 08-l-infini
gcc infini.c -o infini -lm -O3 -march=native -fopenmp
python voir.py
```

---

## Le format : 9:16, toujours, quelle que soit la taille de ton écran

Tous les programmes **dessinent** dans 720 × 1280. Mais 1280 pixels de haut ne
tiennent pas sur un portable de 14 pouces — SDL annonce ici un écran de
1280 × 720, soit presque deux fois moins haut que l'image.

Alors la fenêtre s'ajuste toute seule : elle prend 88 % de la hauteur
disponible et **garde exactement la forme**. Sur cette machine elle fait
**356 × 633**, soit un rapport de 0,5624 contre 0,5625 pour un 9:16 parfait —
un dixième de pixel d'écart.

Tu captures donc la fenêtre telle quelle, sans jamais recadrer. C'est déjà du
vertical.

```bash
python 04-une-goutte/pluie.py --plein    # force le 720 x 1280 d'origine
```

Utilise `--plein` quand tu branches un écran externe : l'image sera plus nette,
et toujours au même format.

**Le cœur en C**, lui, mesure ton terminal au démarrage et s'y ajuste. Fais-le
étroit et haut (une quarantaine de colonnes, soixante-dix lignes) et le cœur
reste rond, centré, avec de la marge au-dessus et en dessous.

---

## Filmer (Windows)

- **Enregistrement** : [ShareX](https://getsharex.com) (gratuit, capture une région précise) ou OBS.
  À défaut, `Win + Alt + R` (Xbox Game Bar) capture la fenêtre active.
- **Les fenêtres Python font déjà 720 × 1280** : c'est du 9:16, le format Shorts / Reels / TikTok.
  Tu captures la fenêtre, tu n'as rien à recadrer.
- **Pour le terminal** : Windows Terminal, thème sombre, une police à chasse fixe fine
  (Cascadia Mono, JetBrains Mono), zoom à fond, et **désactive le curseur clignotant**.
- **Le code qui défile** : filme ton éditeur en vrai, thème sombre, police grande.
  Scroll à la molette, lentement. Pas de zoom, pas d'effet.

## Monter

Un seul conseil, mais il compte : **cale le moment du `RUN` sur le moment où la musique
s'ouvre.** Tout le reste du montage découle de ça.

## Musiques

| Morceau | Pour quel genre de fin |
|---|---|
| Tom Rosenthal — *Go Solo* | Quelque chose se construit, puis reste |
| Lost Sky — *Vision pt. II* | Montée, puis explosion visuelle |
| Ólafur Arnalds — *Near Light* | Lent, minéral, géométrique |
| Nils Frahm — *Says* | Répétition, boucle, hypnose |
| Ludovico Einaudi — *Experience* | Quelque chose qui grandit sans s'arrêter |
| Sigur Rós — *Hoppípolla* | Une naissance, un monde |
| Bon Iver — *Holocene* | Petitesse, immensité, étoiles |

> Vérifie les droits avant de publier. Sur TikTok / Reels, passe par la bibliothèque
> audio intégrée : c'est libéré pour la plateforme.

---

*Ce dossier ne sert à rien d'utile. C'est exactement pour ça qu'il existe.*
