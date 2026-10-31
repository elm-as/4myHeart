# -*- coding: utf-8 -*-
"""
feuilles.py  --  Des feuilles qui tombent.

Une pierre tombe en ligne droite. Une feuille, elle, hesite.
Elle n'a pas de moteur mais elle plane : l'air sous elle la repousse,
elle s'incline, prend de la vitesse sur le cote, puis decroche et bascule
dans l'autre sens.

Cette oscillation pendulaire s'appelle le *fluttering*. Quand le vent
souffle plus fort, la feuille s'enroule sur elle-meme en toupie (*tumbling*)
ou se fait emporter dans un tourbillon ascendant.

Et au sol, les feuilles mortes restent : le tapis s'epaisit,
formant un parterre d'ambre et de cuivre sous la brume d'automne.

    python feuilles.py

    ESPACE : une bourrasque de vent     ECHAP : quitter
"""

import math
import sys
import random
import numpy as np
import pygame

# ---------------------------------------------------------------- reglages

LARGEUR, HAUTEUR = 720, 1280
FPS = 60

NB_FEUILLES = 180
SOL_BASE = 1140

# Palettes d'automne : ocre dore, rouille, pourpre, carmin, ambre, olive
COULEURS_FEUILLES = [
    (218, 124, 38),   # ocre flamboyant
    (196, 68, 34),    # carmin d'automne
    (168, 45, 42),    # pourpre sombre
    (235, 172, 54),   # jaune d'or
    (184, 92, 40),    # rouille cuivree
    (138, 52, 32),    # marron feuille morte
    (162, 138, 48),   # olive automnale
]

NERVURE = (45, 20, 12, 140)

CIEL_HAUT = (14, 18, 28)
CIEL_BAS = (42, 38, 42)
SOL_TERRE = (22, 18, 16)

# ---------------------------------------------------------------- fenetre

def ouvrir(titre="des feuilles"):
    """Ouvre la fenetre 9:16 adaptee a la hauteur d'ecran."""
    pygame.init()
    pygame.display.set_caption(titre)
    haut = HAUTEUR
    if "--plein" not in sys.argv:
        info = pygame.display.Info()
        haut = max(420, min(HAUTEUR, int(info.current_h * 0.88)))
    larg = max(2, round(haut * LARGEUR / HAUTEUR))
    return pygame.display.set_mode((larg, haut))

# ---------------------------------------------------------------- terrain

def relief_sol(x):
    """Courbe douce et vallonnee du sol."""
    return (SOL_BASE
            - 28.0 * math.sin(x / 140.0)
            - 14.0 * math.cos(x / 65.0 + 1.1)
            - 6.0 * math.sin(x / 24.0 + 2.5))

def fond_ciel():
    """Genere le ciel d'automne en degrade vertical avec brume au sol."""
    surf = pygame.Surface((LARGEUR, HAUTEUR))
    for y in range(HAUTEUR):
        ratio = y / HAUTEUR
        # Degrade exponentiel vers la terre brumeuse
        r = int(CIEL_HAUT[0] * (1 - ratio) + CIEL_BAS[0] * ratio)
        g = int(CIEL_HAUT[1] * (1 - ratio) + CIEL_BAS[1] * ratio)
        b = int(CIEL_HAUT[2] * (1 - ratio) + CIEL_BAS[2] * ratio)
        pygame.draw.line(surf, (r, g, b), (0, y), (LARGEUR, y))
    
    # Silhouettes vagues de collines et branches lointaines dans la brume
    points_sol = [(0, HAUTEUR)]
    for x in range(0, LARGEUR + 10, 10):
        points_sol.append((x, int(relief_sol(x))))
    points_sol.append((LARGEUR, HAUTEUR))
    pygame.draw.polygon(surf, SOL_TERRE, points_sol)
    return surf

# ---------------------------------------------------------------- modeles de feuilles

def forme_feuille(type_id, taille):
    """Genere les points du contour polygonal d'une feuille centree en (0,0)."""
    # 0 = hetre/bouleau (ovale effile), 1 = chene (lobes), 2 = erable (pointes)
    points = []
    t = taille
    if type_id == 0:
        # Forme hetre/bouleau : fuseau effile
        profil = [
            (0, -t * 1.3),
            (t * 0.35, -t * 0.8),
            (t * 0.55, -t * 0.1),
            (t * 0.5, t * 0.5),
            (t * 0.25, t * 0.9),
            (0, t * 1.1),
            (-t * 0.25, t * 0.9),
            (-t * 0.5, t * 0.5),
            (-t * 0.55, -t * 0.1),
            (-t * 0.35, -t * 0.8),
        ]
        return [(px, py) for px, py in profil]
    elif type_id == 1:
        # Forme chene : lobes arrondis
        profil = [
            (0, -t * 1.35),
            (t * 0.3, -t * 0.95), (t * 0.2, -t * 0.8),
            (t * 0.5, -t * 0.45), (t * 0.35, -t * 0.25),
            (t * 0.55, 0.1 * t),  (t * 0.35, 0.35 * t),
            (t * 0.45, 0.7 * t),  (0, t * 1.05),
            (-t * 0.45, 0.7 * t), (-t * 0.35, 0.35 * t),
            (-t * 0.55, 0.1 * t), (-t * 0.35, -t * 0.25),
            (-t * 0.5, -t * 0.45), (-t * 0.2, -t * 0.8),
            (-t * 0.3, -t * 0.95)
        ]
        return [(px, py) for px, py in profil]
    else:
        # Forme erable : etoile a trois branches
        profil = [
            (0, -t * 1.4),
            (t * 0.2, -t * 0.9),
            (t * 0.8, -t * 0.6),
            (t * 0.35, -t * 0.2),
            (t * 0.7, t * 0.3),
            (t * 0.3, t * 0.5),
            (0, t * 1.0),
            (-t * 0.3, t * 0.5),
            (-t * 0.7, t * 0.3),
            (-t * 0.35, -t * 0.2),
            (-t * 0.8, -t * 0.6),
            (-t * 0.2, -t * 0.9),
        ]
        return [(px, py) for px, py in profil]

# ---------------------------------------------------------------- particule feuille

class Feuille:
    def __init__(self, au_sol=False):
        self.reinitialiser(au_sol)

    def reinitialiser(self, au_sol=False):
        # Position 3D (z = profondeur, 0.3 loin, 1.0 tout pres)
        self.z = random.uniform(0.35, 1.0)
        self.taille = int(random.uniform(11, 22) * self.z)
        self.type_id = random.randint(0, 2)
        self.points_base = forme_feuille(self.type_id, self.taille)
        self.couleur = random.choice(COULEURS_FEUILLES)
        
        # Variation de luminosite selon la profondeur
        lum = 0.5 + 0.5 * self.z
        self.couleur_rendu = (
            int(self.couleur[0] * lum),
            int(self.couleur[1] * lum),
            int(self.couleur[2] * lum)
        )
        self.couleur_sombre = (
            int(self.couleur_rendu[0] * 0.65),
            int(self.couleur_rendu[1] * 0.65),
            int(self.couleur_rendu[2] * 0.65)
        )

        self.x = random.uniform(-40, LARGEUR + 40)
        if au_sol:
            sol_y = relief_sol(self.x)
            self.y = sol_y + random.uniform(-6, 25)
            self.posee = True
            self.vx, self.vy = 0.0, 0.0
            self.theta = random.uniform(-0.4, 0.4)
            self.phi = random.uniform(0, math.pi)
            self.psi = random.uniform(0, 2 * math.pi)
        else:
            self.y = random.uniform(-HAUTEUR * 0.4, -20)
            self.posee = False
            self.vx = random.uniform(-10, 10)
            self.vy = random.uniform(30, 75) * self.z
            self.theta = random.uniform(-math.pi / 3, math.pi / 3)   # oscillation laterale
            self.omega_theta = random.uniform(-1.5, 1.5)           # vitesse angulaire
            self.phi = random.uniform(0, math.pi)                  # retournement 3D
            self.omega_phi = random.uniform(1.2, 4.0)
            self.psi = random.uniform(-0.5, 0.5)                   # lacet

        self.phase_tourbillon = random.uniform(0, 2 * math.pi)
        self.sensibilite_vent = random.uniform(0.7, 1.3) / self.z

    def actualiser(self, dt, vent_global, rafale):
        if self.posee:
            # Si une forte rafale passe, les feuilles au sol fremissent
            if rafale > 35.0 and random.random() < 0.02:
                self.y -= random.uniform(2, 8)
                self.x += rafale * 0.08 * dt
                if self.y < relief_sol(self.x) - 15:
                    self.posee = False
                    self.vy = -15
            return

        # 1. Aerodynamique de chute : portance et decrochage
        # Une feuille inclinee a angle theta developpe de la portance perpendiculaire
        gravite = 85.0 * self.z
        vitesse_air_x = self.vx - (vent_global * self.sensibilite_vent)
        vitesse_air_y = self.vy

        # Force de portance (lift) : proportionnelle a sin(2*theta)
        portance_mag = 90.0 * math.sin(2.0 * self.theta)
        trainee_y = 1.4 * vitesse_air_y * abs(math.cos(self.theta))

        ax = -portance_mag * math.cos(self.theta) - 0.9 * vitesse_air_x
        ay = gravite - abs(portance_mag * math.sin(self.theta)) - trainee_y

        self.vx += ax * dt
        self.vy += ay * dt
        self.vy = max(18.0, min(140.0, self.vy))

        self.x += self.vx * dt
        self.y += self.vy * dt

        # 2. Oscillation angulaire (fluttering & tumbling)
        # Effet pendulaire qui tend a redresser la feuille, excite par la portance
        couple_rappel = -4.5 * math.sin(self.theta)
        couple_aerodynamique = 0.04 * (self.vx - vent_global) * math.cos(self.theta)
        self.omega_theta += (couple_rappel + couple_aerodynamique - 1.2 * self.omega_theta) * dt
        self.theta += self.omega_theta * dt

        # Rotation 3D (roulis) : la feuille tourne sur la tranche
        self.phi += self.omega_phi * dt
        self.psi += 0.3 * math.sin(self.theta) * dt

        # 3. Collision avec le sol
        sol_y = relief_sol(self.x)
        if self.y >= sol_y + random.uniform(-4, 18):
            self.y = sol_y + random.uniform(-3, 15)
            self.posee = True
            self.theta = random.uniform(-0.35, 0.35)
            self.phi = random.choice([0.1, math.pi * 0.9])

        # Recyclage si trop a droite/gauche ou sous l'ecran
        if self.y > HAUTEUR + 50 or self.x < -100 or self.x > LARGEUR + 100:
            if not self.posee:
                self.reinitialiser(au_sol=False)

    def dessiner(self, surface):
        # Projection 3D simulee : cos(phi) ecrase la largeur (flip 3D)
        cos_phi = math.cos(self.phi)
        cos_theta = math.cos(self.theta + self.psi)
        sin_theta = math.sin(self.theta + self.psi)

        # Matrice 2D : rotation theta + projection phi
        pts_proj = []
        for px, py in self.points_base:
            # Aplatissement 3D sur la largeur
            px_3d = px * cos_phi
            # Rotation dans le plan
            rx = px_3d * cos_theta - py * sin_theta
            ry = px_3d * sin_theta + py * cos_theta
            pts_proj.append((self.x + rx, self.y + ry))

        if len(pts_proj) < 3:
            return

        # Face recto ou verso selon le signe de cos(phi)
        coul = self.couleur_rendu if cos_phi >= 0 else self.couleur_sombre

        # Tracé du limbe de la feuille
        pygame.draw.polygon(surface, coul, pts_proj)
        pygame.draw.polygon(surface, (20, 10, 8), pts_proj, 1)

        # Nervure centrale
        sommet = pts_proj[0]
        base = pts_proj[len(pts_proj) // 2]
        pygame.draw.line(surface, NERVURE, base, sommet, 1)

# ---------------------------------------------------------------- boucle principale

def main():
    fenetre = ouvrir("des feuilles d'automne")
    toile = pygame.Surface((LARGEUR, HAUTEUR))
    horloge = pygame.time.Clock()

    decor = fond_ciel()

    # Initialisation du banc de feuilles : certaines deja au sol pour le tableau
    feuilles = []
    for _ in range(80):
        feuilles.append(Feuille(au_sol=True))
    for _ in range(NB_FEUILLES):
        feuilles.append(Feuille(au_sol=False))

    # Triage par profondeur Z pour le dessin de l'arriere vers l'avant
    feuilles.sort(key=lambda f: f.z)

    t = 0.0
    bourrasque_extra = 0.0

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE:
                    return
                if evt.key == pygame.K_SPACE:
                    bourrasque_extra = 110.0  # Rafale spectaculaire

        dt = min(horloge.tick(FPS) / 1000.0, 1.0 / 25.0)
        t += dt

        # Dynamique du vent : une onde lente + rafales stochastiques
        vent_base = 22.0 * math.sin(t * 0.45) + 14.0 * math.cos(t * 0.18 + 0.5)
        bourrasque_extra = max(0.0, bourrasque_extra - 35.0 * dt)
        vent_total = vent_base + bourrasque_extra

        # Dessin du ciel & sol
        toile.blit(decor, (0, 0))

        # Mise a jour et affichage des feuilles
        for f in feuilles:
            f.actualiser(dt, vent_total, bourrasque_extra)
            f.dessiner(toile)

        # Echelle douce 9:16 vers la fenetre utilisateur
        pygame.transform.smoothscale(toile, fenetre.get_size(), fenetre)
        pygame.display.flip()

if __name__ == "__main__":
    sys.exit(main())
