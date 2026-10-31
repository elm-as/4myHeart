/*
 *  infini.c  --  Une ligne de maths, et on tombe dedans pour toujours.
 *
 *  Toute l'image tient dans cette repetition :
 *
 *      z  <-  z * z + c
 *
 *  On la repete pour chaque point c du plan. Si z file vers l'infini, on
 *  colorie le point selon le temps qu'il a mis a partir. S'il ne part
 *  jamais, on le laisse noir. C'est tout. Il n'y a rien d'autre.
 *
 *  Le noir qu'on voit est donc l'ensemble des points qui restent. Et son
 *  bord n'a pas de fin : on peut zoomer indefiniment, il y aura toujours
 *  de la structure, toujours nouvelle, toujours la meme.
 *
 *  Ce programme n'affiche rien lui-meme : il crache des images brutes sur
 *  sa sortie standard, et voir.py les met a l'ecran. C'est ce qui permet
 *  d'avoir a la fois la vitesse du C et une vraie fenetre.
 *
 *      gcc infini.c -o infini -lm -O3 -march=native -fopenmp
 *      python voir.py
 *
 *      ./infini --bench     pour mesurer, sans rien afficher
 */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef _OPENMP
  #include <omp.h>
#endif

#ifdef _WIN32
  #include <fcntl.h>
  #include <io.h>
#endif

#define LARGEUR 360
#define HAUTEUR 640

/* Un point du bord ou l'on peut descendre tres loin sans jamais toucher
 * le fond. Ces decimales ne sont pas decoratives : chacune est un palier. */
#define CIBLE_RE (-0.743643887037158704752191506114774)
#define CIBLE_IM ( 0.131825904205311970493132056385139)

#define DEBUT 1.5e0          /* demi-largeur de depart */
#define FIN 2.0e-5           /* ou l'on s'arrete, avant de remonter */
#define VITESSE 0.40         /* nats de zoom par seconde */
#define MAXI_PLAFOND 620

/* Pourquoi s'arreter a 2e-5, alors que le double tient jusqu'a 1e-13 ?
 * Parce que plus on descend, plus il faut d'iterations pour distinguer un
 * point qui part tres tard d'un point qui ne part jamais. Passe une certaine
 * profondeur, avec un plafond de 620, tout est declare "interieur" et
 * l'ecran devient noir. Descendre plus bas demanderait des milliers
 * d'iterations -- et une image toutes les deux secondes. */

static unsigned char image[LARGEUR * HAUTEUR * 3];

static double maintenant(void)
{
#ifdef _OPENMP
    return omp_get_wtime();
#else
    return (double)clock() / CLOCKS_PER_SEC;
#endif
}

static int combien_d_iterations(double demi)
{
    double profondeur = log10(DEBUT / demi);
    int maxi = (int)(90.0 + 46.0 * profondeur);
    return maxi > MAXI_PLAFOND ? MAXI_PLAFOND : maxi;
}

/* La palette : trois cosinus dephases. Trois lignes pour tout un ciel.
 *
 * Le sqrt n'est pas decoratif. Plus on descend, plus les points mettent
 * d'iterations a partir -- et si la couleur tournait au rythme de mu, elle
 * ferait un tour complet d'un pixel a l'autre : tout virerait au gris.
 * La racine etale les grands comptes et garde des bandes lisibles au fond. */
static void teinter(double mu, unsigned char *px)
{
    const double TAU = 6.283185307179586;
    double q = 0.25 * sqrt(mu > 0.0 ? mu : 0.0) + 0.35;
    double c[3];
    c[0] = 0.46 + 0.42 * cos(TAU * (q + 0.00));
    c[1] = 0.42 + 0.40 * cos(TAU * (q + 0.14));
    c[2] = 0.52 + 0.38 * cos(TAU * (q + 0.28));
    for (int i = 0; i < 3; i++) {
        double v = c[i] < 0.0 ? 0.0 : (c[i] > 1.0 ? 1.0 : c[i]);
        px[i] = (unsigned char)(v * 255.0 + 0.5);
    }
}

static void calculer(double demi, int maxi)
{
    double pas = 2.0 * demi / LARGEUR;
    double gauche = CIBLE_RE - demi;
    double haut = CIBLE_IM - pas * HAUTEUR / 2.0;

#ifdef _OPENMP
    #pragma omp parallel for schedule(dynamic, 8)
#endif
    for (int j = 0; j < HAUTEUR; j++) {
        double ci = haut + j * pas;
        unsigned char *ligne = image + (size_t)j * LARGEUR * 3;

        for (int i = 0; i < LARGEUR; i++) {
            double cr = gauche + i * pas;
            double zr = 0.0, zi = 0.0, zr2 = 0.0, zi2 = 0.0;
            int n = 0;

            while (n < maxi && zr2 + zi2 <= 4096.0) {
                zi = 2.0 * zr * zi + ci;
                zr = zr2 - zi2 + cr;
                zr2 = zr * zr;
                zi2 = zi * zi;
                n++;
            }

            unsigned char *px = ligne + i * 3;
            if (n >= maxi) {                     /* le point ne part jamais */
                px[0] = px[1] = px[2] = 0;
            } else {
                /* Le compte lisse : sans lui, on verrait des anneaux nets
                 * la ou la couleur devrait glisser. */
                double mu = n + 1.0 - log2(0.5 * log(zr2 + zi2));
                teinter(mu, px);
            }
        }
    }
}

int main(int argc, char **argv)
{
    int bench = (argc > 1 && strcmp(argv[1], "--bench") == 0);

    if (bench) {
        double paliers[] = {1.5e0, 1.0e-3, 1.0e-6, 1.0e-9, 3.0e-13};
        for (int k = 0; k < 5; k++) {
            int maxi = combien_d_iterations(paliers[k]);
            double t0 = 0.0, t1 = 0.0;
#ifdef _OPENMP
            t0 = omp_get_wtime();
#endif
            for (int r = 0; r < 5; r++) calculer(paliers[k], maxi);
#ifdef _OPENMP
            t1 = omp_get_wtime();
#endif
            double ms = (t1 - t0) / 5.0 * 1000.0;
            fprintf(stderr, "demi=%9.1e  maxi=%4d  ->  %6.1f ms  (%5.1f images/s)\n",
                    paliers[k], maxi, ms, 1000.0 / ms);
        }
        return 0;
    }

#ifdef _WIN32
    _setmode(_fileno(stdout), _O_BINARY);   /* sinon Windows abime les octets */
#endif

    /* On ne calcule pas 60 images par seconde -- on en calcule 5, et on dit
     * a l'afficheur a quel instant chacune correspond. Lui se charge de
     * zoomer dans la derniere recue en attendant la suivante : c'est ce qui
     * rend la descente fluide alors qu'elle est lente a calculer. */
    double duree = log(DEBUT / FIN) / VITESSE;
    double origine = maintenant();

    for (;;) {
        double temps = maintenant() - origine;
        if (temps > duree + 2.0) {                 /* arrive au fond, on repart */
            origine = maintenant();
            temps = 0.0;
        }

        double demi = DEBUT * exp(-VITESSE * temps);
        calculer(demi, combien_d_iterations(demi));

        if (fwrite(&temps, sizeof temps, 1, stdout) != 1) return 0;
        if (fwrite(image, 1, sizeof image, stdout) != sizeof image) return 0;
        if (fflush(stdout) != 0) return 0;
    }
}
