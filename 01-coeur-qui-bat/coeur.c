/*
 *  coeur.c  --  Un coeur qui bat, dessine par une seule equation.
 *
 *  L'equation, c'est celle-ci :
 *
 *      (x^2 + y^2 - 1)^3  -  x^2 * y^3  <=  0
 *
 *  Tous les points (x, y) qui la verifient sont a l'interieur d'un coeur.
 *  Le reste du programme ne fait que demander, pour chaque caractere de
 *  ton terminal : "est-ce que tu es dedans ?" -- et choisir un symbole.
 *
 *  Le programme mesure ton terminal au demarrage et s'y ajuste. Fais-le
 *  etroit et haut, et tu obtiens du 9:16 : le coeur reste rond, centre,
 *  avec de la place au-dessus et en dessous. Rien a recadrer.
 *
 *  Compilation :  gcc coeur.c -o coeur -lm -O2
 *  Lancement   :  ./coeur "ton message"
 *                 ./coeur "ton message" 40 70      (taille imposee)
 */

#include <stdio.h>
#include <math.h>
#include <string.h>
#include <stdlib.h>

#ifdef _WIN32
  #include <windows.h>
  #define DORS(ms) Sleep(ms)
#else
  #include <unistd.h>
  #include <sys/ioctl.h>
  #define DORS(ms) usleep((ms) * 1000)
#endif

#define MAX_COLONNES 400
#define MAX_LIGNES 240

/* Une case de terminal est a peu pres deux fois plus haute que large.
 * Sans ce nombre, le coeur serait un oeuf. */
#define RATIO_CAR 2.1

/* Du plus discret au plus intense. */
static const char NUANCES[] = " .:-=+*#%@";
/* Palette 256 couleurs : rouge profond -> rose -> presque blanc. */
static const int  COULEURS[] = {52, 88, 124, 160, 196, 203, 210, 217, 224, 231};
#define NB_NUANCES ((int)(sizeof(NUANCES) - 1))

static char toile[MAX_LIGNES][MAX_COLONNES * 24];

static void active_les_couleurs(void)
{
#ifdef _WIN32
    HANDLE h = GetStdHandle(STD_OUTPUT_HANDLE);
    DWORD mode;
    if (GetConsoleMode(h, &mode))
        SetConsoleMode(h, mode | 0x0004 /* VIRTUAL_TERMINAL_PROCESSING */);
    SetConsoleOutputCP(CP_UTF8);
#endif
}

/* De quelle taille est la fenetre ou l'on ecrit ? */
static void mesurer_le_terminal(int *colonnes, int *lignes)
{
#ifdef _WIN32
    CONSOLE_SCREEN_BUFFER_INFO info;
    if (GetConsoleScreenBufferInfo(GetStdHandle(STD_OUTPUT_HANDLE), &info)) {
        *colonnes = info.srWindow.Right - info.srWindow.Left + 1;
        *lignes = info.srWindow.Bottom - info.srWindow.Top + 1;
    }
#else
    struct winsize w;
    if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &w) == 0 && w.ws_col > 0 && w.ws_row > 0) {
        *colonnes = w.ws_col;
        *lignes = w.ws_row;
    }
#endif
}

static int borner(int v, int mini, int maxi)
{
    return v < mini ? mini : (v > maxi ? maxi : v);
}

/*  Le battement.  Un vrai coeur ne fait pas "toc... toc... toc".
 *  Il fait "ta-DOUM ...... ta-DOUM".  Deux coups : un petit, un grand.  */
static double battement(double t)
{
    double p = fmod(t, 1.0);                    /* une seconde = un cycle */
    double coup1 = exp(-pow((p - 0.00) / 0.055, 2.0));
    double coup2 = exp(-pow((p - 0.17) / 0.075, 2.0)) * 0.55;
    return coup1 + coup2;
}

int main(int argc, char **argv)
{
    const char *message = (argc > 1) ? argv[1] : "";
    int colonnes = 84, lignes = 34;
    double t = 0.0;

    mesurer_le_terminal(&colonnes, &lignes);
    if (argc > 3) {
        colonnes = atoi(argv[2]);
        lignes = atoi(argv[3]);
    }
    colonnes = borner(colonnes, 20, MAX_COLONNES);
    lignes = borner(lignes - 1, 12, MAX_LIGNES);   /* -1 : sinon le terminal defile */

    /*  L'ajustement.  On veut que le coeur reste rond quelle que soit la
     *  forme de la fenetre. La hauteur vue vaut donc la largeur vue,
     *  multipliee par le nombre de lignes, par leur elancement, et divisee
     *  par le nombre de colonnes. Ensuite on elargit juste ce qu'il faut
     *  pour que le coeur tienne dans les deux sens.  */
    double elancement = (double)lignes * RATIO_CAR / (double)colonnes;
    double demi_x = 1.42;
    if (demi_x * elancement < 1.30) demi_x = 1.30 / elancement;
    double demi_y = demi_x * elancement;

    /* Le bas du coeur, puis deux lignes de repos, puis le message. */
    int ligne_du_message = (int)(lignes / 2.0 * (1.0 + 1.175 / demi_y)) + 2;
    if (ligne_du_message > lignes - 1) ligne_du_message = lignes - 1;

    active_les_couleurs();
    printf("\x1b[2J\x1b[?25l");                 /* efface tout, cache le curseur */

    for (;;) {
        /* Le coeur respire : il gonfle sur le battement. */
        double pulsation = 1.0 + 0.13 * battement(t);
        /* Et il apparait doucement dans les 2 premieres secondes. */
        double eveil = t < 2.0 ? t / 2.0 : 1.0;
        eveil = eveil * eveil * (3.0 - 2.0 * eveil);   /* adouci */

        for (int ligne = 0; ligne < lignes; ligne++) {
            char *curseur = toile[ligne];
            int couleur_active = -1;
            *curseur = '\0';

            for (int col = 0; col < colonnes; col++) {
                /* On place la case dans un repere mathematique centre sur
                   le coeur -- d'ou le petit decalage vers le bas. */
                double x = (col - colonnes / 2.0) / (colonnes / 2.0) * demi_x / pulsation;
                double y = -(ligne - lignes / 2.0) / (lignes / 2.0) * demi_y / pulsation - 0.175;

                double r = x * x + y * y - 1.0;
                double valeur = r * r * r - x * x * y * y * y;   /* l'equation */

                int niveau;
                if (valeur <= 0.0) {
                    /* Dedans : plus on est au coeur du coeur, plus c'est dense. */
                    double profondeur = pow(-valeur, 0.30) * 2.6;
                    if (profondeur > 1.0) profondeur = 1.0;
                    niveau = 3 + (int)(profondeur * (NB_NUANCES - 4));
                } else if (valeur < 0.09) {
                    niveau = 1;                  /* le halo, juste au bord */
                } else {
                    niveau = 0;                  /* le vide */
                }

                niveau = (int)(niveau * eveil);
                if (niveau >= NB_NUANCES) niveau = NB_NUANCES - 1;

                if (niveau == 0) {
                    if (couleur_active != -1) {
                        curseur += sprintf(curseur, "\x1b[0m");
                        couleur_active = -1;
                    }
                    *curseur++ = ' ';
                    *curseur = '\0';
                } else {
                    if (COULEURS[niveau] != couleur_active) {
                        couleur_active = COULEURS[niveau];
                        curseur += sprintf(curseur, "\x1b[38;5;%dm", couleur_active);
                    }
                    *curseur++ = NUANCES[niveau];
                    *curseur = '\0';
                }
            }
            if (couleur_active != -1) strcat(curseur, "\x1b[0m");
        }

        /* Le message vient se poser dans l'image, sous le coeur. */
        if (*message) {
            int large = (int)strlen(message);
            int marge = (colonnes - large) / 2;
            if (marge < 0) marge = 0;
            sprintf(toile[ligne_du_message], "\x1b[38;5;217m%*s%s\x1b[0m",
                    marge, "", message);
        }

        /* On ecrit l'image entiere d'un seul coup : aucun scintillement. */
        printf("\x1b[H");
        for (int ligne = 0; ligne < lignes; ligne++)
            printf("%s\x1b[K\n", toile[ligne]);
        fflush(stdout);

        DORS(33);
        t += 0.033;
    }
    return 0;
}
