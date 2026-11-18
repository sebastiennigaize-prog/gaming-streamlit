# ============================================================
# 1. IMPORTATION DES BIBLIOTHÈQUES
# ============================================================

from pathlib import Path
import pandas as pd


# ============================================================
# 2. DÉFINITION DES CHEMINS
# ============================================================

# Répertoire principal du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# Fichier nettoyé que nous allons utiliser
FICHIER_SOURCE = BASE_DIR / "data" / "vgsales_clean.csv"


# ============================================================
# 3. CHARGEMENT DU DATASET
# ============================================================

df = pd.read_csv(FICHIER_SOURCE)

print("=== CHARGEMENT DU DATASET ===")
print(f"Nombre de lignes : {len(df)}")
print(f"Nombre de colonnes : {len(df.columns)}")

# ============================================================
# 3 BIS. APPLICATION DES ANNÉES CORRIGÉES
# ============================================================

# Fichier contenant les années vérifiées.
FICHIER_SUIVI = BASE_DIR / "data" / "annees_a_verifier.csv"

# Chargement des corrections.
suivi_annees = pd.read_csv(FICHIER_SUIVI)

# Sélection des corrections validées.
corrections_annees = suivi_annees.loc[
    (suivi_annees["Statut_Verification"] == "Verifie")
    & suivi_annees["Year_Corrected"].notna(),
    ["Rank", "Name", "Platform", "Year_Corrected"]
].copy()

# Vérification de l'unicité des identifiants.
if corrections_annees["Rank"].duplicated().any():
    raise ValueError(
        "Des Rank sont dupliqués dans les corrections d'années."
    )

# Association des corrections aux jeux du dataset.
df = df.merge(
    corrections_annees,
    on=["Rank", "Name", "Platform"],
    how="left",
    validate="one_to_one"
)

# Application des années corrigées lorsqu'elles existent.
nb_corrections = df["Year_Corrected"].notna().sum()

df["Year"] = df["Year_Corrected"].combine_first(df["Year"])

# Suppression de la colonne temporaire.
df = df.drop(columns=["Year_Corrected"])

print("\n=== APPLICATION DES ANNÉES CORRIGÉES ===")
print(f"Années corrigées appliquées : {nb_corrections}")

# ============================================================
# 4. VÉRIFICATIONS INITIALES
# ============================================================

# Vérification de l'unicité de Rank
print(f"Rank dupliqués : {df['Rank'].duplicated().sum()}")

# Nombre de titres distincts
print(f"Titres distincts : {df['Name'].nunique()}")

# Total des ventes mondiales avant regroupement
print(f"Ventes mondiales : {df['Global_Sales'].sum():.2f} M")

# ============================================================
# 5. PRÉPARATION DES COLONNES DE REGROUPEMENT
# ============================================================

# On conserve le nom original pour le moment.
df["Game_Title_Clean"] = df["Name"].copy()

# Les identifiants seront attribués après vérification
# des règles de regroupement.
df["Game_ID"] = pd.NA
df["Game_Version_ID"] = pd.NA


# ============================================================
# 6. VÉRIFICATION DES NOUVELLES COLONNES
# ============================================================

print("\n=== COLONNES DE REGROUPEMENT ===")

print(df[
    [
        "Rank",
        "Name",
        "Platform",
        "Year",
        "Game_Title_Clean",
        "Game_ID",
        "Game_Version_ID"
    ]
].head(10).to_string(index=False))

print(f"\nNombre de colonnes : {len(df.columns)}")

# ============================================================
# 7. GESTION DES JEUX HOMONYMES VALIDÉS
# ============================================================

# Need for Speed: Most Wanted
# Le jeu de 2012 possède également une version Wii U de 2013.

masque_nfs = df["Name"] == "Need for Speed: Most Wanted"

df.loc[
    masque_nfs & (df["Year"] == 2005),
    "Game_Title_Clean"
] = "Need for Speed: Most Wanted (2005)"

df.loc[
    masque_nfs & df["Year"].isin([2012, 2013]),
    "Game_Title_Clean"
] = "Need for Speed: Most Wanted (2012)"


# Mortal Kombat
# Les versions de 1992 et 1994 appartiennent au jeu original.
# Les versions de 2011 et 2012 appartiennent au reboot de 2011.

masque_mk = df["Name"] == "Mortal Kombat"

df.loc[
    masque_mk & df["Year"].isin([1992, 1994]),
    "Game_Title_Clean"
] = "Mortal Kombat (1992)"

df.loc[
    masque_mk & df["Year"].isin([2011, 2012]),
    "Game_Title_Clean"
] = "Mortal Kombat (2011)"


# Sonic the Hedgehog
# Nous distinguons le jeu original de 1991 et celui de 2006.

masque_sonic = df["Name"] == "Sonic the Hedgehog"

df.loc[
    masque_sonic & (df["Year"] == 1991),
    "Game_Title_Clean"
] = "Sonic the Hedgehog (1991)"

df.loc[
    masque_sonic & (df["Year"] == 2006),
    "Game_Title_Clean"
] = "Sonic the Hedgehog (2006)"

# ============================================================
# 7 BIS. SÉPARATION DES JEUX MEDAL OF HONOR
# ============================================================

# Sélectionner les lignes Medal of Honor
masque_medal = df["Name"] == "Medal of Honor"

# Premier jeu : version PlayStation
df.loc[
    masque_medal & (df["Year"] == 1998),
    "Game_Title_Clean"
] = "Medal of Honor (1998 - dataset)"

# Jeu de 2010 : PC, PS3 et Xbox 360
df.loc[
    masque_medal & (df["Year"] == 2010),
    "Game_Title_Clean"
] = "Medal of Honor (2010)"

# ============================================================
# 7 TER. SÉPARATION DES VERSIONS DE MONOPOLY
# ============================================================

masque_monopoly = df["Name"] == "Monopoly"

# Trois adaptations distinctes ; années d'origine du dataset conservées.
for plateforme, annee, titre in [
    ("PC", 1994, "Monopoly (PC - 1994 dataset)"),
    ("PS", 1997, "Monopoly (PS - 1997)"),
    ("N64", 1999, "Monopoly (N64 - 1999)"),
]:
    df.loc[
        masque_monopoly & (df["Platform"] == plateforme) & (df["Year"] == annee),
        "Game_Title_Clean"
    ] = titre

# Génération 2008-2010 : regroupement provisoire conservé.
df.loc[
    masque_monopoly & df["Year"].isin([2008, 2010]),
    "Game_Title_Clean"
] = "Monopoly (2008-2010)"


# ============================================================
# 7 TER BIS. SÉPARATION DES ÉDITIONS DE MYST
# ============================================================

# Sélection du jeu Myst uniquement.
# Les autres titres contenant "Myst" ne sont pas concernés.
masque_myst = df["Name"] == "Myst"

# Édition originale et portages classiques :
# PC 1994, Saturn 1994 et PlayStation 1995.
df.loc[
    masque_myst & df["Platform"].isin(["PC", "SAT", "PS"]),
    "Game_Title_Clean"
] = "Myst (Original)"

# Éditions portables enrichies :
# PSP 2006 et Nintendo DS 2007.
df.loc[
    masque_myst & df["Platform"].isin(["PSP", "DS"]),
    "Game_Title_Clean"
] = "Myst (Portable enrichi)"


# ============================================================
# 7 TER TER. SÉPARATION DES ÉDITIONS DE FINAL FANTASY V
# ============================================================

# Sélection exacte de Final Fantasy V.
masque_ff5 = df["Name"] == "Final Fantasy V"

# Version originale Super Nintendo (1992).
df.loc[
    masque_ff5
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1992),
    "Game_Title_Clean"
] = "Final Fantasy V (SNES 1992)"

# Réédition PlayStation (1998).
df.loc[
    masque_ff5
    & (df["Platform"] == "PS")
    & (df["Year"] == 1998),
    "Game_Title_Clean"
] = "Final Fantasy V (PS 1998)"


# ============================================================
# 7 TER QUATER. SÉPARATION DES ÉDITIONS DE DEAD RISING
# ============================================================

# Sélection exacte de Dead Rising.
# Ne concerne pas les autres jeux de la série.
masque_dead_rising = df["Name"] == "Dead Rising"

# Version originale Xbox 360 (2006).
df.loc[
    masque_dead_rising
    & (df["Platform"] == "X360")
    & (df["Year"] == 2006),
    "Game_Title_Clean"
] = "Dead Rising (2006)"

# Réédition remasterisée PlayStation 4 (2016).
df.loc[
    masque_dead_rising
    & (df["Platform"] == "PS4")
    & (df["Year"] == 2016),
    "Game_Title_Clean"
] = "Dead Rising (Remaster 2016)"


# ============================================================
# 7 TER QUINQUIES. SÉPARATION DES ÉDITIONS DE FINAL FANTASY IV
# ============================================================

# Version SNES de 1991 :
# Commercialisée sous le nom Final Fantasy II en Amérique du Nord.
masque_ff4_snes = (
    (df["Name"] == "Final Fantasy II")
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1991)
)

df.loc[masque_ff4_snes, "Game_Title_Clean"] = 'Final Fantasy IV (SNES 1991)'

# Réédition PlayStation de 1997.
masque_ff4_ps = (
    (df["Name"] == "Final Fantasy IV")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1997)
)

df.loc[masque_ff4_ps, "Game_Title_Clean"] = 'Final Fantasy IV (PS 1997)'



# ============================================================
# 7 QUATER. CORRECTION DU REGROUPEMENT FINAL FANTASY III
# ============================================================

# Sélectionner les lignes portant le nom Final Fantasy III
masque_ff3 = df["Name"] == "Final Fantasy III"

# Jeu original de 1990 et ses adaptations
df.loc[
    masque_ff3 & df["Platform"].isin(["NES", "DS", "PSP"]),
    "Game_Title_Clean"
] = "Final Fantasy III (1990)"

# Version SNES de 1994 : il s'agit de Final Fantasy VI
df.loc[
    masque_ff3 & (df["Platform"] == "SNES"),
    "Game_Title_Clean"
] = "Final Fantasy VI (1994 - SNES)"

# ============================================================
# 7 QUINQUIES. REGROUPEMENT DES VERSIONS FINAL FANTASY VI
# ============================================================

# Identifier les trois versions du même jeu
masque_ff6 = (
    ((df["Name"] == "Final Fantasy III") & (df["Platform"] == "SNES"))
    | (df["Name"] == "Final Fantasy VI")
    | (df["Name"] == "Final Fantasy VI Advance")
)

# Donner le même nom de regroupement aux trois versions
df.loc[masque_ff6, "Game_Title_Clean"] = 'Final Fantasy VI (1994)'

# ============================================================
# 7 SEXIES. REGROUPEMENT TEENAGE MUTANT NINJA TURTLES
# ============================================================

masque_tmnt = df["Name"] == "Teenage Mutant Ninja Turtles"

# Jeu NES de 1989
df.loc[
    masque_tmnt & (df["Platform"] == "NES") & (df["Year"] == 1989),
    "Game_Title_Clean"
] = "Teenage Mutant Ninja Turtles (1989)"

# Version GBA de 2003, isolée provisoirement
df.loc[
    masque_tmnt & (df["Platform"] == "GBA") & (df["Year"] == 2003),
    "Game_Title_Clean"
] = "Teenage Mutant Ninja Turtles (2003 - GBA)"

# Jeu multiplateforme de 2003
df.loc[
    masque_tmnt & df["Platform"].isin(["GC", "PS2", "XB"]) & (df["Year"] == 2003),
    "Game_Title_Clean"
] = "Teenage Mutant Ninja Turtles (2003 - Consoles)"

# Ligne Wii de 2007 à vérifier
df.loc[
    masque_tmnt & (df["Platform"] == "Wii") & (df["Year"] == 2007),
    "Game_Title_Clean"
] = "Teenage Mutant Ninja Turtles (2007 - Wii à vérifier)"

# ============================================================
# 7 SEPTIES. REGROUPEMENT RESIDENT EVIL REMAKE
# ============================================================

# Regroupement du remake GameCube et de son adaptation Wii
masque_re_remake = df["Name"].isin([
    "Resident Evil (Remake)",
    "Resident Evil Archives: Resident Evil"
])

df.loc[masque_re_remake, "Game_Title_Clean"] = 'Resident Evil (Remake 2002)'

# ============================================================
# 7 OCTIES. REGROUPEMENT RESIDENT EVIL 2
# ============================================================

# Regrouper les éditions du jeu original de 1998
masque_re2 = df["Name"].isin([
    "Resident Evil 2",
    "Resident Evil 2: Dual Shock Edition"
])

df.loc[masque_re2, "Game_Title_Clean"] = 'Resident Evil 2 (1998)'

# ============================================================
# 7 NONIES. SÉPARATION DES DEUX JEUX FROGGER
# ============================================================

# Frogger original sur Atari 2600
masque_frogger_1981 = (
    (df["Name"] == "Frogger")
    & (df["Platform"] == "2600")
    & (df["Year"] == 1981)
)

df.loc[masque_frogger_1981, "Game_Title_Clean"] = "Frogger (1981)"


# Nouvelle version de Frogger sur PlayStation
masque_frogger_1997 = (
    (df["Name"] == "Frogger")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1997)
)

df.loc[masque_frogger_1997, "Game_Title_Clean"] = "Frogger (1997)"

# ============================================================
# 7 DECIES. SÉPARATION DONKEY KONG GAME BOY 1994
# ============================================================

# Conserver les versions du jeu d'arcade original ensemble
masque_donkey_original = (
    (df["Name"] == "Donkey Kong")
    & (df["Platform"].isin(["2600", "NES"]))
)

df.loc[masque_donkey_original, "Game_Title_Clean"] = "Donkey Kong (1981)"

# Séparer le jeu Game Boy de 1994
masque_donkey_gb = (
    (df["Name"] == "Donkey Kong")
    & (df["Platform"] == "GB")
    & (df["Year"] == 1994)
)

df.loc[masque_donkey_gb, "Game_Title_Clean"] = "Donkey Kong (1994 - Game Boy)"

# ============================================================
# 7 UNDECIES. SÉPARATION SUPER MARIO BROS. DELUXE
# ============================================================

# Jeu original sur NES (1985)
masque_mario_nes = (
    (df["Name"] == "Super Mario Bros.")
    & (df["Platform"] == "NES")
    & (df["Year"] == 1985)
)

df.loc[masque_mario_nes, "Game_Title_Clean"] = "Super Mario Bros. (1985)"


# Édition Deluxe sur Game Boy Color (1999)
masque_mario_deluxe = (
    (df["Name"] == "Super Mario Bros.")
    & (df["Platform"] == "GB")
    & (df["Year"] == 1999)
)

df.loc[masque_mario_deluxe, "Game_Title_Clean"] = "Super Mario Bros. Deluxe (1999)"

# ============================================================
# 7 DUODECIES. SÉPARATION SUPER MARIO WORLD
# ============================================================

# Version originale sur Super Nintendo (1990)
masque_mario_world_snes = (
    (df["Name"] == "Super Mario World")
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1990)
)

df.loc[masque_mario_world_snes, "Game_Title_Clean"] = 'Super Mario World (1990)'


# Réédition améliorée sur Game Boy Advance (2001)
masque_mario_world_gba = (
    (df["Name"] == "Super Mario World")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2001)
)

df.loc[masque_mario_world_gba, "Game_Title_Clean"] = 'Super Mario Advance 2: Super Mario World (2001)'

# ============================================================
# 7 TREDECIES. SÉPARATION SUPER MARIO BROS. 3
# ============================================================

# Version originale NES (1988)
masque_mario_3_nes = (
    (df["Name"] == "Super Mario Bros. 3")
    & (df["Platform"] == "NES")
    & (df["Year"] == 1988)
)

df.loc[masque_mario_3_nes, "Game_Title_Clean"] = 'Super Mario Bros. 3 (1988)'


# Réédition améliorée GBA (2003)
masque_mario_advance_4 = (
    (df["Name"] == "Super Mario Bros. 3")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2003)
)

df.loc[masque_mario_advance_4, "Game_Title_Clean"] = 'Super Mario Advance 4: Super Mario Bros. 3 (2003)'

# ============================================================
# 7 QUATERDECIES. SÉPARATION SUPER MARIO 64
# ============================================================

# Version originale Nintendo 64 (1996)
masque_mario_64_n64 = (
    (df["Name"] == "Super Mario 64")
    & (df["Platform"] == "N64")
    & (df["Year"] == 1996)
)

df.loc[masque_mario_64_n64, "Game_Title_Clean"] = 'Super Mario 64 (1996)'


# Remake enrichi Nintendo DS (2004)
masque_mario_64_ds = (
    (df["Name"] == "Super Mario 64")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2004)
)

df.loc[masque_mario_64_ds, "Game_Title_Clean"] = 'Super Mario 64 DS (2004)'

# ============================================================
# 7 QUINDECIES. SÉPARATION DONKEY KONG COUNTRY
# ============================================================

# Version originale Super Nintendo (1994)
masque_dkc_snes = (
    (df["Name"] == "Donkey Kong Country")
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1994)
)

df.loc[masque_dkc_snes, "Game_Title_Clean"] = 'Donkey Kong Country (1994 - SNES)'


# Adaptation Game Boy Color (2000)
# La plateforme GB représente ici la Game Boy Color
masque_dkc_gbc = (
    (df["Name"] == "Donkey Kong Country")
    & (df["Platform"] == "GB")
    & (df["Year"] == 2000)
)

df.loc[masque_dkc_gbc, "Game_Title_Clean"] = 'Donkey Kong Country (2000 - GBC)'


# Réédition Game Boy Advance (2003)
masque_dkc_gba = (
    (df["Name"] == "Donkey Kong Country")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2003)
)

df.loc[masque_dkc_gba, "Game_Title_Clean"] = 'Donkey Kong Country (2003 - GBA)'

# ============================================================
# 7 SEXDECIES. SÉPARATION ZELDA OCARINA OF TIME
# ============================================================

# Version originale Nintendo 64 (1998)
masque_zelda_ocarina_n64 = (
    (df["Name"] == "The Legend of Zelda: Ocarina of Time")
    & (df["Platform"] == "N64")
    & (df["Year"] == 1998)
)

df.loc[masque_zelda_ocarina_n64, "Game_Title_Clean"] = 'The Legend of Zelda: Ocarina of Time (1998)'


# Remake Nintendo 3DS (2011)
masque_zelda_ocarina_3ds = (
    (df["Name"] == "The Legend of Zelda: Ocarina of Time")
    & (df["Platform"] == "3DS")
    & (df["Year"] == 2011)
)

df.loc[masque_zelda_ocarina_3ds, "Game_Title_Clean"] = 'The Legend of Zelda: Ocarina of Time 3D (2011)'

# ============================================================
# 7 SEPTDECIES. SÉPARATION KINGDOM HEARTS
# ============================================================

# Jeu original sur PlayStation 2 (2002)
masque_kh_ps2 = (
    (df["Name"] == "Kingdom Hearts")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2002)
)

df.loc[masque_kh_ps2, "Game_Title_Clean"] = 'Kingdom Hearts (2002)'


# Compilation HD sur PlayStation 3 (2013)
masque_kh_hd = (
    (df["Name"] == "Kingdom Hearts")
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2013)
)

df.loc[masque_kh_hd, "Game_Title_Clean"] = 'Kingdom Hearts HD 1.5 ReMIX (2013)'

# ============================================================
# 7 DUODEVICIES. SÉPARATION ZELDA A LINK TO THE PAST
# ============================================================

# Version originale Super Nintendo (1991)
masque_zelda_link_snes = (
    (df["Name"] == "The Legend of Zelda: A Link to the Past")
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1991)
)

df.loc[masque_zelda_link_snes, "Game_Title_Clean"] = 'The Legend of Zelda: A Link to the Past (1991)'


# Réédition Game Boy Advance (2002)
# Inclut également le jeu multijoueur Four Swords
masque_zelda_link_gba = (
    (df["Name"] == "The Legend of Zelda: A Link to the Past")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2002)
)

df.loc[masque_zelda_link_gba, "Game_Title_Clean"] = 'The Legend of Zelda: A Link to the Past & Four Swords (2002)'

# ============================================================
# 7 UNDEVICIES. SÉPARATION YOSHI'S ISLAND
# ============================================================

# Version originale Super Nintendo (1995)
masque_yoshi_snes = (
    (df["Name"] == "Super Mario World 2: Yoshi's Island")
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1995)
)

df.loc[masque_yoshi_snes, "Game_Title_Clean"] = "Super Mario World 2: Yoshi's Island (1995)"


# Réédition Game Boy Advance (2002)
# Commercialisée sous le titre Yoshi's Island: Super Mario Advance 3
masque_yoshi_gba = (
    (df["Name"] == "Super Mario World 2: Yoshi's Island")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2002)
)

df.loc[masque_yoshi_gba, "Game_Title_Clean"] = "Yoshi's Island: Super Mario Advance 3 (2002)"

# ============================================================
# 7 VICES. SÉPARATION RESIDENT EVIL 2
# ============================================================

# Version originale de Resident Evil 2 (1998)
# Les portages N64 et GameCube restent regroupés
# avec la version PlayStation originale.

masque_re2_original = (
    (df["Name"] == "Resident Evil 2")
    & (df["Platform"].isin(["PS", "N64", "GC"]))
)

df.loc[masque_re2_original, "Game_Title_Clean"] = 'Resident Evil 2 (1998)'


# Édition spécifique PlayStation : Dual Shock Edition
# Cette édition possède du contenu supplémentaire.

masque_re2_dual_shock = (
    (df["Name"] == "Resident Evil 2: Dual Shock Edition")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1998)
)

df.loc[masque_re2_dual_shock, "Game_Title_Clean"] = 'Resident Evil 2: Dual Shock Edition (1998)'

# ============================================================
# 7 UNVICES. SÉPARATION ZELDA THE WIND WAKER
# ============================================================

# Version originale GameCube (2002)
masque_zelda_wind_gc = (
    (df["Name"] == "The Legend of Zelda: The Wind Waker")
    & (df["Platform"] == "GC")
    & (df["Year"] == 2002)
)

df.loc[masque_zelda_wind_gc, "Game_Title_Clean"] = 'The Legend of Zelda: The Wind Waker (2002)'


# Remaster HD sur Wii U (2013)
masque_zelda_wind_wiiu = (
    (df["Name"] == "The Legend of Zelda: The Wind Waker")
    & (df["Platform"] == "WiiU")
    & (df["Year"] == 2013)
)

df.loc[masque_zelda_wind_wiiu, "Game_Title_Clean"] = 'The Legend of Zelda: The Wind Waker HD (2013)'

# ============================================================
# 7 DUOVICES. SÉPARATION GOLF
# ============================================================

# Version Nintendo Entertainment System (1984)
masque_golf_nes = (
    (df["Name"] == "Golf")
    & (df["Platform"] == "NES")
    & (df["Year"] == 1984)
)

df.loc[masque_golf_nes, "Game_Title_Clean"] = 'Golf (NES - 1984)'


# Version Game Boy (1989)
# Adaptation portable avec des différences de contenu
masque_golf_gb = (
    (df["Name"] == "Golf")
    & (df["Platform"] == "GB")
    & (df["Year"] == 1989)
)

df.loc[masque_golf_gb, "Game_Title_Clean"] = 'Golf (GB - 1989)'

# ============================================================
# 7 TERVICES. SÉPARATION DRAGON QUEST VIII
# ============================================================

# Version originale PlayStation 2 (2004)
masque_dq8_ps2 = (
    (df["Name"] == "Dragon Quest VIII: Journey of the Cursed King")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2004)
)

df.loc[masque_dq8_ps2, "Game_Title_Clean"] = 'Dragon Quest VIII: Journey of the Cursed King (2004)'


# Réédition enrichie Nintendo 3DS (2015)
# Contient des personnages et des quêtes supplémentaires
masque_dq8_3ds = (
    (df["Name"] == "Dragon Quest VIII: Journey of the Cursed King")
    & (df["Platform"] == "3DS")
    & (df["Year"] == 2015)
)

df.loc[masque_dq8_3ds, "Game_Title_Clean"] = 'Dragon Quest VIII: Journey of the Cursed King (3DS - 2015)'

# ============================================================
# 7 QUATERVICES. SÉPARATION DRAGON QUEST VII
# ============================================================

# Version originale PlayStation (2000)
masque_dq7_ps = (
    (df["Name"] == "Dragon Quest VII: Warriors of Eden")
    & (df["Platform"] == "PS")
    & (df["Year"] == 2000)
)

df.loc[masque_dq7_ps, "Game_Title_Clean"] = 'Dragon Quest VII: Warriors of Eden (2000)'


# Remake Nintendo 3DS (2013)
# Graphismes et gameplay retravaillés
masque_dq7_3ds = (
    (df["Name"] == "Dragon Quest VII: Warriors of Eden")
    & (df["Platform"] == "3DS")
    & (df["Year"] == 2013)
)

df.loc[masque_dq7_3ds, "Game_Title_Clean"] = 'Dragon Quest VII: Fragments of the Forgotten Past (3DS - 2013)'

# ============================================================
# 7 QUINVICES. SÉPARATION KINGDOM HEARTS II
# ============================================================

# Version originale PlayStation 2 (2005)
masque_kh2_ps2 = (
    (df["Name"] == "Kingdom Hearts II")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2005)
)

df.loc[masque_kh2_ps2, "Game_Title_Clean"] = 'Kingdom Hearts II (2005)'


# Compilation HD sur PlayStation 3 (2014)
# Contient plusieurs jeux et contenus remasterisés
masque_kh2_hd = (
    (df["Name"] == "Kingdom Hearts II")
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2014)
)

df.loc[masque_kh2_hd, "Game_Title_Clean"] = 'Kingdom Hearts HD 2.5 ReMIX (2014)'

# ============================================================
# 7 SEXVICES. SÉPARATION GOD OF WAR III
# ============================================================

# Version originale PlayStation 3 (2010)
masque_gow3_ps3 = (
    (df["Name"] == "God of War III")
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2010)
)

df.loc[masque_gow3_ps3, "Game_Title_Clean"] = 'God of War III (2010)'


# Version remasterisée PlayStation 4 (2015)
# Graphismes améliorés et fonctionnalités supplémentaires
masque_gow3_ps4 = (
    (df["Name"] == "God of War III")
    & (df["Platform"] == "PS4")
    & (df["Year"] == 2015)
)

df.loc[masque_gow3_ps4, "Game_Title_Clean"] = 'God of War III Remastered (2015)'

# ============================================================
# 7 SEPTVICES. SÉPARATION ASTEROIDS
# ============================================================

# Version Atari 2600 (1980)
# Adaptation du jeu d'arcade original
masque_asteroids_2600 = (
    (df["Name"] == "Asteroids")
    & (df["Platform"] == "2600")
    & (df["Year"] == 1980)
)

df.loc[masque_asteroids_2600, "Game_Title_Clean"] = 'Asteroids (Atari 2600 - 1980)'


# Nouvelle version PlayStation (1998)
# Réinterprétation avec des graphismes et du contenu modernisés
masque_asteroids_ps = (
    (df["Name"] == "Asteroids")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1998)
)

df.loc[masque_asteroids_ps, "Game_Title_Clean"] = 'Asteroids (PlayStation - 1998)'

# ============================================================
# 7.X.01 - CORRECTION NBA JAM : ÉDITIONS 1992, 2003 ET 2010
# ============================================================

# NBA Jam original : Genesis et Super Nintendo
# On conserve le nom NBA Jam pour ces versions.

# NBA Jam 2003 : nouvelle version sur PS2 et Xbox
masque_nba_2003 = (
    (df["Name"] == "NBA Jam")
    & (df["Platform"].isin(["PS2", "XB"]))
    & (df["Year"] == 2003)
)

df.loc[masque_nba_2003, "Game_Title_Clean"] = 'NBA Jam (2003)'

# NBA Jam 2010 : nouvelle version éditée par Electronic Arts
masque_nba_2010 = (
    (df["Name"] == "NBA Jam")
    & (df["Platform"].isin(["PS3", "Wii", "X360"]))
    & (df["Year"] == 2010)
)

df.loc[masque_nba_2010, "Game_Title_Clean"] = 'NBA Jam (2010)'

# ============================================================
# 7.X.02 - FINAL FANTASY III : ORIGINAL ET REMAKE 3D
# ============================================================

# Version originale sortie sur NES en 1990
masque_ff3_original = (
    (df["Name"] == "Final Fantasy III")
    & (df["Platform"] == "NES")
    & (df["Year"] == 1990)
)

df.loc[masque_ff3_original, "Game_Title_Clean"] = 'Final Fantasy III (1990)'

# Remake 3D sorti sur Nintendo DS en 2006
# et adapté sur PSP en 2012
masque_ff3_remake = (
    (df["Name"] == "Final Fantasy III")
    & (df["Platform"].isin(["DS", "PSP"]))
    & (df["Year"].isin([2006, 2012]))
)

df.loc[masque_ff3_remake, "Game_Title_Clean"] = 'Final Fantasy III (Remake 3D)'

# La version SNES de 1994 reste associée
# à Final Fantasy VI (1994).

# ============================================================
# 7.X.03 - FINAL FANTASY VI : ORIGINAL ET VERSION ADVANCE
# ============================================================

# Version originale de Final Fantasy VI :
# - SNES 1994 (commercialisée sous le nom Final Fantasy III)
# - PlayStation 1999 (portage du jeu original)
# On conserve le regroupement existant.

# Version Game Boy Advance de 2006 :
# édition enrichie avec du contenu supplémentaire.
masque_ff6_advance = (
    (df["Name"] == "Final Fantasy VI Advance")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2006)
)

df.loc[masque_ff6_advance, "Game_Title_Clean"] = 'Final Fantasy VI Advance (2006)'

# ============================================================
# 7.X.04 - BASEBALL : NES 1983 ET GAME BOY 1989
# ============================================================

# Baseball sur NES : version originale de 1983
masque_baseball_nes = (
    (df["Name"] == "Baseball")
    & (df["Platform"] == "NES")
    & (df["Year"] == 1983)
)

df.loc[masque_baseball_nes, "Game_Title_Clean"] = 'Baseball (NES - 1983)'

# Baseball sur Game Boy : adaptation de 1989
masque_baseball_gb = (
    (df["Name"] == "Baseball")
    & (df["Platform"] == "GB")
    & (df["Year"] == 1989)
)

df.loc[masque_baseball_gb, "Game_Title_Clean"] = 'Baseball (Game Boy - 1989)'

# ============================================================
# 7.X.05 - DRAGON WARRIOR III : ORIGINAL ET REMAKE GBC
# ============================================================

# Version originale sortie sur Famicom / NES en 1988
masque_dw3_nes = (
    (df["Name"] == "Dragon Warrior III")
    & (df["Platform"] == "NES")
    & (df["Year"] == 1988)
)

df.loc[masque_dw3_nes, "Game_Title_Clean"] = 'Dragon Warrior III (1988)'

# Version Game Boy Color sortie au Japon en 2000
# Adaptation enrichie du jeu original
masque_dw3_gbc = (
    (df["Name"] == "Dragon Warrior III")
    & (df["Platform"] == "GB")
    & (df["Year"] == 2000)
)

df.loc[masque_dw3_gbc, "Game_Title_Clean"] = 'Dragon Warrior III (GBC Remake - 2000)'

# ============================================================
# 7.X.06 - SPIDER-MAN : ATARI 2600 ET VERSION 2000
# ============================================================

# Spider-Man sur Atari 2600 :
# jeu distinct de celui sorti en 2000.
# L'année 1981 du dataset est conservée provisoirement.
masque_spiderman_2600 = (
    (df["Name"] == "Spider-Man")
    & (df["Platform"] == "2600")
    & (df["Year"] == 1981)
)

df.loc[masque_spiderman_2600, "Game_Title_Clean"] = 'Spider-Man (Atari 2600)'

# Spider-Man de 2000 :
# versions PlayStation et Nintendo 64 du même jeu.
masque_spiderman_2000 = (
    (df["Name"] == "Spider-Man")
    & (df["Platform"].isin(["PS", "N64"]))
    & (df["Year"] == 2000)
)

df.loc[masque_spiderman_2000, "Game_Title_Clean"] = 'Spider-Man (2000)'

# ============================================================
# 7.X.07 - DRAGON QUEST V : ORIGINAL SNES ET REMAKE PS2
# ============================================================

# Dragon Quest V original, sorti sur Super Famicom en 1992
masque_dq5_snes = (
    (df["Name"] == "Dragon Quest V: Tenkuu no Hanayome")
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1992)
)

df.loc[masque_dq5_snes, "Game_Title_Clean"] = 'Dragon Quest V (SNES - 1992)'

# Dragon Quest V : remake 3D sorti sur PlayStation 2 en 2004
masque_dq5_ps2 = (
    (df["Name"] == "Dragon Quest V: Tenkuu no Hanayome")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2004)
)

df.loc[masque_dq5_ps2, "Game_Title_Clean"] = 'Dragon Quest V (PS2 Remake - 2004)'

# La version Nintendo DS de 2008 possède déjà
# un titre distinct : Dragon Quest V: Hand of the Heavenly Bride.
# Aucune modification nécessaire.

# ============================================================
# 7.X.08 - SIMCITY 2000 : VERSIONS CLASSIQUES ET GBA
# ============================================================

# Versions PC, Saturn, SNES et PlayStation :
# adaptations du jeu SimCity 2000 original.
# On conserve leur regroupement actuel.

# Version Game Boy Advance de 2003 :
# adaptation spécifique à la console portable.
masque_simcity_gba = (
    (df["Name"] == "SimCity 2000")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2003)
)

df.loc[masque_simcity_gba, "Game_Title_Clean"] = 'SimCity 2000 (GBA - 2003)'

# ============================================================
# 7.X.09 - TENNIS : NES 1984 ET GAME BOY 1989
# ============================================================

# Version originale sur NES en 1984
masque_tennis_nes = (
    (df["Name"] == "Tennis")
    & (df["Platform"] == "NES")
    & (df["Year"] == 1984)
)

df.loc[masque_tennis_nes, "Game_Title_Clean"] = 'Tennis (NES - 1984)'

# Adaptation Game Boy sortie en 1989
masque_tennis_gb = (
    (df["Name"] == "Tennis")
    & (df["Platform"] == "GB")
    & (df["Year"] == 1989)
)

df.loc[masque_tennis_gb, "Game_Title_Clean"] = 'Tennis (Game Boy - 1989)'

# ============================================================
# 7.X.10 - GHOST RECON : JEU ORIGINAL ET VERSION WII 2010
# ============================================================

# Les versions PS2, Xbox et GameCube de 2002-2003
# restent regroupées sous le jeu original.

# La version Wii de 2010 est un jeu différent,
# conçu spécifiquement pour cette console.
masque_ghost_recon_wii = (
    (df["Name"] == "Tom Clancy's Ghost Recon")
    & (df["Platform"] == "Wii")
    & (df["Year"] == 2010)
)

df.loc[masque_ghost_recon_wii, "Game_Title_Clean"] = "Tom Clancy's Ghost Recon (Wii - 2010)"

# ============================================================
# 7.X.11 - WHEEL OF FORTUNE : DIFFERENTES EDITIONS
# ============================================================

# Editions N64 1997 et PlayStation 1998
# Regroupement provisoire, à vérifier ultérieurement
masque_wheel_1997 = (
    (df["Name"] == "Wheel of Fortune")
    & (
        ((df["Platform"] == "N64") & (df["Year"] == 1997))
        | ((df["Platform"] == "PS") & (df["Year"] == 1998))
    )
)

df.loc[masque_wheel_1997, "Game_Title_Clean"] = 'Wheel of Fortune (1997-1998)'

# Edition PlayStation 2 sortie en 2003
masque_wheel_2003 = (
    (df["Name"] == "Wheel of Fortune")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2003)
)

df.loc[masque_wheel_2003, "Game_Title_Clean"] = 'Wheel of Fortune (2003)'

# Editions Nintendo DS et Wii sorties en 2010
masque_wheel_2010 = (
    (df["Name"] == "Wheel of Fortune")
    & (df["Platform"].isin(["DS", "Wii"]))
    & (df["Year"] == 2010)
)

df.loc[masque_wheel_2010, "Game_Title_Clean"] = 'Wheel of Fortune (2010)'

# Wheel of Fortune: 2nd Edition conserve son nom distinct.

# ============================================================
# 7.X.12 - CHRONO TRIGGER : SNES 1995 ET DS 2008
# ============================================================

# Version originale sortie sur Super Nintendo en 1995
masque_chrono_snes = (
    (df["Name"] == "Chrono Trigger")
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1995)
)

df.loc[masque_chrono_snes, "Game_Title_Clean"] = 'Chrono Trigger (SNES - 1995)'


# Réédition enrichie sortie sur Nintendo DS en 2008
masque_chrono_ds = (
    (df["Name"] == "Chrono Trigger")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2008)
)

df.loc[masque_chrono_ds, "Game_Title_Clean"] = 'Chrono Trigger (DS - 2008)'
# ============================================================
# 7.X.13 - BANJO-KAZOOIE : N64 1998 ET XBOX 360 2008
# ============================================================

# Jeu original Nintendo 64 sorti en 1998
masque_banjo_n64 = (
    (df["Name"] == "Banjo-Kazooie")
    & (df["Platform"] == "N64")
    & (df["Year"] == 1998)
)

df.loc[masque_banjo_n64, "Game_Title_Clean"] = 'Banjo-Kazooie (N64 - 1998)'


# Réédition numérique améliorée sur Xbox 360 en 2008
masque_banjo_x360 = (
    (df["Name"] == "Banjo-Kazooie")
    & (df["Platform"] == "X360")
    & (df["Year"] == 2008)
)

df.loc[masque_banjo_x360, "Game_Title_Clean"] = 'Banjo-Kazooie (Xbox 360 - 2008)'

# ============================================================
# 7.X.14 - DOOM II : PC 1994 ET GAME BOY ADVANCE 2002
# ============================================================

# Version originale PC sortie en 1994
masque_doom_ii_pc = (
    (df["Name"] == "Doom II: Hell on Earth")
    & (df["Platform"] == "PC")
    & (df["Year"] == 1994)
)

df.loc[masque_doom_ii_pc, "Game_Title_Clean"] = 'Doom II: Hell on Earth (PC - 1994)'


# Adaptation Game Boy Advance sortie en 2002
masque_doom_ii_gba = (
    (df["Name"] == "Doom II: Hell on Earth")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2002)
)

df.loc[masque_doom_ii_gba, "Game_Title_Clean"] = 'Doom II: Hell on Earth (GBA - 2002)'

# ============================================================
# 7.X.15 - MARIO TENNIS : N64 ET GAME BOY COLOR (2000)
# ============================================================

# Version Nintendo 64 sortie en 2000
masque_mario_tennis_n64 = (
    (df["Name"] == "Mario Tennis")
    & (df["Platform"] == "N64")
    & (df["Year"] == 2000)
)

df.loc[masque_mario_tennis_n64, "Game_Title_Clean"] = 'Mario Tennis (Nintendo 64 - 2000)'


# Version Game Boy Color sortie en 2000
# Jeu distinct avec des mécaniques RPG
masque_mario_tennis_gbc = (
    (df["Name"] == "Mario Tennis")
    & (df["Platform"] == "GB")
    & (df["Year"] == 2000)
)

df.loc[masque_mario_tennis_gbc, "Game_Title_Clean"] = 'Mario Tennis (Game Boy Color - 2000)'

# ============================================================
# 7.X.16 - MARIO TENNIS : WII 2010 ET 3DS 2012
# ============================================================

# Version Wii enregistrée en 2010
# Identification exacte à confirmer.
masque_mario_tennis_wii = (
    (df["Name"] == "Mario Tennis")
    & (df["Platform"] == "Wii")
    & (df["Year"] == 2010)
)

df.loc[masque_mario_tennis_wii, "Game_Title_Clean"] = 'Mario Tennis (Wii - 2010 - à vérifier)'


# Version 3DS enregistrée en 2012
# Possible correspondance avec Mario Tennis Open.
masque_mario_tennis_3ds = (
    (df["Name"] == "Mario Tennis")
    & (df["Platform"] == "3DS")
    & (df["Year"] == 2012)
)

df.loc[masque_mario_tennis_3ds, "Game_Title_Clean"] = 'Mario Tennis (3DS - 2012 - à vérifier)'

# ============================================================
# 7.X.17 - SSX : JEU ORIGINAL 2000 ET NOUVEL EPISODE 2012
# ============================================================

# Premier SSX sorti sur PlayStation 2 en 2000
masque_ssx_2000 = (
    (df["Name"] == "SSX")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2000)
)

df.loc[masque_ssx_2000, "Game_Title_Clean"] = 'SSX (2000)'


# Nouvel épisode SSX sorti en 2012 sur PS3 et Xbox 360
masque_ssx_2012 = (
    (df["Name"] == "SSX")
    & (df["Platform"].isin(["PS3", "X360"]))
    & (df["Year"] == 2012)
)

df.loc[masque_ssx_2012, "Game_Title_Clean"] = 'SSX (2012)'

# ============================================================
# 7.X.18 - SPACE INVADERS : DIFFERENTES EDITIONS
# ============================================================

# Version Atari 2600 sortie en 1980
masque_space_2600 = (
    (df["Name"] == "Space Invaders")
    & (df["Platform"] == "2600")
    & (df["Year"] == 1980)
)

df.loc[masque_space_2600, "Game_Title_Clean"] = 'Space Invaders (Atari 2600 - 1980)'


# Version Super Nintendo sortie en 1994
masque_space_snes = (
    (df["Name"] == "Space Invaders")
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1994)
)

df.loc[masque_space_snes, "Game_Title_Clean"] = 'Space Invaders (SNES - 1994)'


# Version Nintendo 64 sortie en 1999
masque_space_n64 = (
    (df["Name"] == "Space Invaders")
    & (df["Platform"] == "N64")
    & (df["Year"] == 1999)
)

df.loc[masque_space_n64, "Game_Title_Clean"] = 'Space Invaders (N64 - 1999)'


# Version Game Boy Advance sortie en 2002
# Edition exacte à confirmer
masque_space_gba = (
    (df["Name"] == "Space Invaders")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2002)
)

df.loc[masque_space_gba, "Game_Title_Clean"] = 'Space Invaders (GBA - 2002)'

# ============================================================
# 7.X.19 - MISSILE COMMAND : ATARI 2600 ET PLAYSTATION
# ============================================================

# Version Atari 2600 sortie en 1980
masque_missile_2600 = (
    (df["Name"] == "Missile Command")
    & (df["Platform"] == "2600")
    & (df["Year"] == 1980)
)

df.loc[masque_missile_2600, "Game_Title_Clean"] = 'Missile Command (Atari 2600 - 1980)'


# Réinterprétation PlayStation sortie en 1999
masque_missile_ps = (
    (df["Name"] == "Missile Command")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1999)
)

df.loc[masque_missile_ps, "Game_Title_Clean"] = 'Missile Command (PlayStation - 1999)'

# ============================================================
# 7.X.20 - FABLE : ORIGINAL ET ANNIVERSARY
# ============================================================

# Jeu original sorti sur Xbox en 2004
masque_fable_original = (
    (df["Name"] == "Fable")
    & (df["Platform"] == "XB")
    & (df["Year"] == 2004)
)

df.loc[masque_fable_original, "Game_Title_Clean"] = 'Fable (2004)'


# Fable Anniversary : remaster sorti sur Xbox 360 en 2014
# Le dataset utilise simplement le nom "Fable".
masque_fable_anniversary = (
    (df["Name"] == "Fable")
    & (df["Platform"] == "X360")
    & (df["Year"] == 2014)
)

df.loc[masque_fable_anniversary, "Game_Title_Clean"] = 'Fable Anniversary (2014)'

# ============================================================
# 7.X.21 - DEVIL MAY CRY : EDITIONS ORIGINALES ET AMELIOREES
# ============================================================

# ------------------------------------------------------------
# DEVIL MAY CRY 4 - EDITION ORIGINALE (2008)
# ------------------------------------------------------------

# Les versions PC, PS3 et Xbox 360 correspondent
# au jeu original sorti en 2008.
masque_dmc4_original = (
    (df["Name"] == "Devil May Cry 4")
    & (df["Platform"].isin(["PC", "PS3", "X360"]))
    & (df["Year"] == 2008)
)

df.loc[masque_dmc4_original, "Game_Title_Clean"] = 'Devil May Cry 4 (2008)'


# ------------------------------------------------------------
# DEVIL MAY CRY 4 - SPECIAL EDITION (2015)
# ------------------------------------------------------------

# La version PS4 de 2015 est une édition enrichie.
masque_dmc4_special = (
    (df["Name"] == "Devil May Cry 4")
    & (df["Platform"] == "PS4")
    & (df["Year"] == 2015)
)

df.loc[masque_dmc4_special, "Game_Title_Clean"] = 'Devil May Cry 4: Special Edition (2015)'


# ------------------------------------------------------------
# DMC: DEVIL MAY CRY - EDITION ORIGINALE (2013)
# ------------------------------------------------------------

# Regrouper les versions PS3 et Xbox 360.
masque_dmc_original = (
    (df["Name"] == "DmC: Devil May Cry")
    & (df["Platform"].isin(["PS3", "X360"]))
    & (df["Year"] == 2013)
)

df.loc[masque_dmc_original, "Game_Title_Clean"] = 'DmC: Devil May Cry (2013)'


# ------------------------------------------------------------
# DMC: DEVIL MAY CRY - DEFINITIVE EDITION (2015)
# ------------------------------------------------------------

# Regrouper les versions PS4 et Xbox One,
# qui correspondent à la même édition améliorée.
masque_dmc_definitive = (
    (df["Name"] == "DmC: Devil May Cry")
    & (df["Platform"].isin(["PS4", "XOne"]))
    & (df["Year"] == 2015)
)

df.loc[masque_dmc_definitive, "Game_Title_Clean"] = 'DmC: Devil May Cry Definitive Edition (2015)'

# ============================================================
# 7.X.22 - ICE HOCKEY : ATARI 2600 ET NES
# ============================================================

# ------------------------------------------------------------
# ICE HOCKEY - ATARI 2600 (1980)
# ------------------------------------------------------------

# Jeu édité par Activision sur Atari 2600.
masque_ice_hockey_2600 = (
    (df["Name"] == "Ice Hockey")
    & (df["Platform"] == "2600")
    & (df["Year"] == 1980)
)

df.loc[masque_ice_hockey_2600, "Game_Title_Clean"] = 'Ice Hockey (Atari 2600 - 1980)'


# ------------------------------------------------------------
# ICE HOCKEY - NES (1988)
# ------------------------------------------------------------

# Jeu Nintendo distinct de la version Atari.
masque_ice_hockey_nes = (
    (df["Name"] == "Ice Hockey")
    & (df["Platform"] == "NES")
    & (df["Year"] == 1988)
)

df.loc[masque_ice_hockey_nes, "Game_Title_Clean"] = 'Ice Hockey (NES - 1988)'

# ============================================================
# 7.X.23 - FINAL FANTASY II : NUMEROTATION ET REEDITION
# ============================================================

# ------------------------------------------------------------
# FINAL FANTASY II - NES (1988)
# ------------------------------------------------------------

# Véritable deuxième épisode japonais de Final Fantasy.
masque_ff2_nes = (
    (df["Name"] == "Final Fantasy II")
    & (df["Platform"] == "NES")
    & (df["Year"] == 1988)
)

df.loc[masque_ff2_nes, "Game_Title_Clean"] = 'Final Fantasy II (1988)'


# ------------------------------------------------------------
# FINAL FANTASY IV - SNES (1991)
# ------------------------------------------------------------

# Final Fantasy IV a été commercialisé aux États-Unis
# sous le titre Final Fantasy II.
masque_ff4_snes = (
    (df["Name"] == "Final Fantasy II")
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1991)
)

df.loc[masque_ff4_snes, "Game_Title_Clean"] = 'Final Fantasy IV (1991)'


# ------------------------------------------------------------
# FINAL FANTASY II - WONDERSWAN (2001)
# ------------------------------------------------------------

# Réédition améliorée du Final Fantasy II original.
masque_ff2_ws = (
    (df["Name"] == "Final Fantasy II")
    & (df["Platform"] == "WS")
    & (df["Year"] == 2001)
)

df.loc[masque_ff2_ws, "Game_Title_Clean"] = 'Final Fantasy II (WonderSwan - 2001)'

# ============================================================
# 7.X.24 - FINAL FANTASY IV : ORIGINAL ET REMAKE 3D
# ============================================================

# ------------------------------------------------------------
# FINAL FANTASY IV - VERSION ORIGINALE
# ------------------------------------------------------------

# Le jeu SNES de 1991 est nommé Final Fantasy II
# dans le dataset à cause de la numérotation américaine.
# La version PlayStation de 1997 est un portage
# du même épisode.

masque_ff4_original = (
    (
        (df["Name"] == "Final Fantasy II")
        & (df["Platform"] == "SNES")
        & (df["Year"] == 1991)
    )
    |
    (
        (df["Name"] == "Final Fantasy IV")
        & (df["Platform"] == "PS")
        & (df["Year"] == 1997)
    )
)

df.loc[masque_ff4_original, "Game_Title_Clean"] = 'Final Fantasy IV (1991)'


# ------------------------------------------------------------
# FINAL FANTASY IV - REMAKE 3D (NINTENDO DS)
# ------------------------------------------------------------

# La version Nintendo DS est un remake avec
# des graphismes 3D et des mécaniques retravaillées.

masque_ff4_ds = (
    (df["Name"] == "Final Fantasy IV")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2007)
)

df.loc[masque_ff4_ds, "Game_Title_Clean"] = 'Final Fantasy IV (Remake 3D - 2007)'

# ============================================================
# 7.X.25 - FIFA STREET : EPISODES 2005 ET 2012
# ============================================================

# ------------------------------------------------------------
# FIFA STREET - PREMIER EPISODE (2005)
# ------------------------------------------------------------

# Regrouper les versions GameCube, PS2 et Xbox
# du premier FIFA Street.
masque_fifa_street_2005 = (
    (df["Name"] == "FIFA Street")
    & (df["Platform"].isin(["GC", "PS2", "XB"]))
    & (df["Year"] == 2005)
)

df.loc[masque_fifa_street_2005, "Game_Title_Clean"] = 'FIFA Street (2005)'


# ------------------------------------------------------------
# FIFA STREET - NOUVEL EPISODE (2012)
# ------------------------------------------------------------

# Le FIFA Street de 2012 est un nouveau jeu,
# et non un portage de l'episode de 2005.
masque_fifa_street_2012 = (
    (df["Name"] == "FIFA Street")
    & (df["Platform"].isin(["PS3", "X360"]))
    & (df["Year"] == 2012)
)

df.loc[masque_fifa_street_2012, "Game_Title_Clean"] = 'FIFA Street (2012)'

# ============================================================
# 7.X.26 - GRAND THEFT AUTO : 1997 ET GBA 2004
# ============================================================

# ------------------------------------------------------------
# GRAND THEFT AUTO - JEU ORIGINAL (1997)
# ------------------------------------------------------------

# Premier épisode de la série, sorti sur PlayStation.

masque_gta_1997 = (
    (df["Name"] == "Grand Theft Auto")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1997)
)

df.loc[masque_gta_1997, "Game_Title_Clean"] = 'Grand Theft Auto (1997)'


# ------------------------------------------------------------
# GRAND THEFT AUTO - GAME BOY ADVANCE (2004)
# ------------------------------------------------------------

# La version GBA de 2004 est un épisode distinct
# du Grand Theft Auto original.

masque_gta_gba = (
    (df["Name"] == "Grand Theft Auto")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2004)
)

df.loc[masque_gta_gba, "Game_Title_Clean"] = 'Grand Theft Auto Advance (2004)'

# ============================================================
# 7.X.27 - RIDGE RACER : EPISODES PS, PSP ET PSV
# ============================================================

# ------------------------------------------------------------
# RIDGE RACER - PLAYSTATION (1994)
# ------------------------------------------------------------

# Jeu original sorti sur PlayStation.

masque_ridge_ps = (
    (df["Name"] == "Ridge Racer")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1994)
)

df.loc[masque_ridge_ps, "Game_Title_Clean"] = 'Ridge Racer (1994)'


# ------------------------------------------------------------
# RIDGE RACER - PSP (2004)
# ------------------------------------------------------------

# Nouvel episode developpe pour la PSP.
# Il ne s'agit pas d'un simple portage du jeu de 1994.

masque_ridge_psp = (
    (df["Name"] == "Ridge Racer")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2004)
)

df.loc[masque_ridge_psp, "Game_Title_Clean"] = 'Ridge Racer (PSP - 2004)'


# ------------------------------------------------------------
# RIDGE RACER - PLAYSTATION VITA (2011)
# ------------------------------------------------------------

# Episode distinct sorti sur PlayStation Vita.

masque_ridge_psv = (
    (df["Name"] == "Ridge Racer")
    & (df["Platform"] == "PSV")
    & (df["Year"] == 2011)
)

df.loc[masque_ridge_psv, "Game_Title_Clean"] = 'Ridge Racer (PSV - 2011)'

# ============================================================
# 7.X.28 - DRAGON QUEST MONSTERS 2 : ORIGINAL ET REMAKE 3D
# ============================================================

# ------------------------------------------------------------
# DRAGON QUEST MONSTERS 2 - VERSION ORIGINALE (2001)
# ------------------------------------------------------------

# Jeu original sorti sur Game Boy Color.
# Le dataset utilise le code plateforme GB.

masque_dqm2_original = (
    (df["Name"] == "Dragon Quest Monsters 2")
    & (df["Platform"] == "GB")
    & (df["Year"] == 2001)
)

df.loc[masque_dqm2_original, "Game_Title_Clean"] = 'Dragon Quest Monsters 2 (2001)'


# ------------------------------------------------------------
# DRAGON QUEST MONSTERS 2 - REMAKE 3D (2014)
# ------------------------------------------------------------

# Remake Nintendo 3DS du jeu original,
# avec graphismes 3D et contenu enrichi.

masque_dqm2_remake = (
    (df["Name"] == "Dragon Quest Monsters 2")
    & (df["Platform"] == "3DS")
    & (df["Year"] == 2014)
)

df.loc[masque_dqm2_remake, "Game_Title_Clean"] = 'Dragon Quest Monsters 2 (Remake 3D - 2014)'

# ============================================================
# 7.X.29 - PRO YAKYUU FAMILY STADIUM : NES ET WII
# ============================================================

# ------------------------------------------------------------
# PRO YAKYUU FAMILY STADIUM - NES (1986)
# ------------------------------------------------------------

# Premier episode de la serie de baseball de Namco.

masque_family_stadium_nes = (
    (df["Name"] == "Pro Yakyuu Family Stadium")
    & (df["Platform"] == "NES")
    & (df["Year"] == 1986)
)

df.loc[masque_family_stadium_nes, "Game_Title_Clean"] = 'Pro Yakyuu Family Stadium (1986)'


# ------------------------------------------------------------
# PRO YAKYUU FAMILY STADIUM - WII (2008)
# ------------------------------------------------------------

# Jeu distinct sorti sur Wii en 2008.
# Il ne doit pas etre regroupe avec le jeu NES.

masque_family_stadium_wii = (
    (df["Name"] == "Pro Yakyuu Family Stadium")
    & (df["Platform"] == "Wii")
    & (df["Year"] == 2008)
)

df.loc[masque_family_stadium_wii, "Game_Title_Clean"] = 'Pro Yakyuu Family Stadium (Wii - 2008)'

# ============================================================
# 7.X.30 - JEOPARDY! : DIFFERENTES EDITIONS
# ============================================================

# ------------------------------------------------------------
# JEOPARDY! - PLAYSTATION ET NINTENDO 64 (1997-1998)
# ------------------------------------------------------------

# Editions de la meme generation.
# Regroupement provisoire PS et N64.

masque_jeopardy_1997 = (
    (df["Name"] == "Jeopardy!")
    & (
        (
            (df["Platform"] == "PS")
            & (df["Year"] == 1997)
        )
        |
        (
            (df["Platform"] == "N64")
            & (df["Year"] == 1998)
        )
    )
)

df.loc[masque_jeopardy_1997, "Game_Title_Clean"] = 'Jeopardy! (1997-1998)'


# ------------------------------------------------------------
# JEOPARDY! - PLAYSTATION 2 (2003)
# ------------------------------------------------------------

# Nouvelle edition sortie sur PlayStation 2.

masque_jeopardy_ps2 = (
    (df["Name"] == "Jeopardy!")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2003)
)

df.loc[masque_jeopardy_ps2, "Game_Title_Clean"] = 'Jeopardy! (PS2 - 2003)'


# ------------------------------------------------------------
# JEOPARDY! - NINTENDO DS ET WII (2010)
# ------------------------------------------------------------

# Editions contemporaines publiees par THQ.
# Regroupement par generation et edition.

masque_jeopardy_2010 = (
    (df["Name"] == "Jeopardy!")
    & (df["Platform"].isin(["DS", "Wii"]))
    & (df["Year"] == 2010)
)

df.loc[masque_jeopardy_2010, "Game_Title_Clean"] = 'Jeopardy! (2010)'

# ============================================================
# 7.X.31 - THE INCREDIBLE HULK : 2003 ET 2008
# ============================================================

# ------------------------------------------------------------
# THE INCREDIBLE HULK - GAME BOY ADVANCE (2003)
# ------------------------------------------------------------

# Jeu GBA lie au film Hulk de 2003.
# Il est distinct des adaptations sorties en 2008.

masque_hulk_gba_2003 = (
    (df["Name"] == "The Incredible Hulk")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2003)
)

df.loc[masque_hulk_gba_2003, "Game_Title_Clean"] = 'The Incredible Hulk (GBA - 2003)'


# ------------------------------------------------------------
# THE INCREDIBLE HULK - ADAPTATIONS DE 2008
# ------------------------------------------------------------

# Jeux publies par Sega en 2008.
# Regroupement provisoire des cinq plateformes.

masque_hulk_2008 = (
    (df["Name"] == "The Incredible Hulk")
    & (df["Platform"].isin(["DS", "PS2", "PS3", "Wii", "X360"]))
    & (df["Year"] == 2008)
)

df.loc[masque_hulk_2008, "Game_Title_Clean"] = 'The Incredible Hulk (2008)'

# ============================================================
# 7.X.32 - CENTIPEDE : VERSION ORIGINALE ET REINTERPRETATION
# ============================================================

# ------------------------------------------------------------
# CENTIPEDE - ATARI 2600 (1981)
# ------------------------------------------------------------

# Adaptation du jeu d'arcade original.
# Gameplay classique en 2D.

masque_centipede_1981 = (
    (df["Name"] == "Centipede")
    & (df["Platform"] == "2600")
    & (df["Year"] == 1981)
)

df.loc[masque_centipede_1981, "Game_Title_Clean"] = 'Centipede (1981)'


# ------------------------------------------------------------
# CENTIPEDE - PLAYSTATION (1998)
# ------------------------------------------------------------

# Nouvelle interpretation du jeu avec environnements 3D.
# Distincte de la version originale.

masque_centipede_1998 = (
    (df["Name"] == "Centipede")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1998)
)

df.loc[masque_centipede_1998, "Game_Title_Clean"] = 'Centipede (1998)'

# ============================================================
# 7.X.33 - CASTLEVANIA : NES 1986 ET N64 1999
# ============================================================

# ------------------------------------------------------------
# CASTLEVANIA - NES (1986)
# ------------------------------------------------------------

# Premier episode de la serie Castlevania.
# Jeu de plateformes en 2D avec Simon Belmont.

masque_castlevania_1986 = (
    (df["Name"] == "Castlevania")
    & (df["Platform"] == "NES")
    & (df["Year"] == 1986)
)

df.loc[masque_castlevania_1986, "Game_Title_Clean"] = 'Castlevania (1986)'


# ------------------------------------------------------------
# CASTLEVANIA - NINTENDO 64 (1999)
# ------------------------------------------------------------

# Nouvel episode de la serie en 3D.
# Ce n'est pas un portage du jeu NES de 1986.

masque_castlevania_1999 = (
    (df["Name"] == "Castlevania")
    & (df["Platform"] == "N64")
    & (df["Year"] == 1999)
)

df.loc[masque_castlevania_1999, "Game_Title_Clean"] = 'Castlevania (N64 - 1999)'

# ============================================================
# 7.X.34 - APE ESCAPE : PLAYSTATION 1999 ET PS3 2010
# ============================================================

# ------------------------------------------------------------
# APE ESCAPE - PLAYSTATION (1999)
# ------------------------------------------------------------

# Premier episode de la serie.
# Jeu de plateformes utilisant les deux sticks analogiques.

masque_ape_escape_1999 = (
    (df["Name"] == "Ape Escape")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1999)
)

df.loc[masque_ape_escape_1999, "Game_Title_Clean"] = 'Ape Escape (1999)'


# ------------------------------------------------------------
# APE ESCAPE - PLAYSTATION 3 (2010)
# ------------------------------------------------------------

# Jeu distinct concu pour le PlayStation Move.
# Ce n'est pas un portage du jeu de 1999.

masque_ape_escape_2010 = (
    (df["Name"] == "Ape Escape")
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2010)
)

df.loc[masque_ape_escape_2010, "Game_Title_Clean"] = 'Ape Escape (PS3 - 2010)'

# ============================================================
# 7.X.35 - DEFENDER : JEU ORIGINAL ET REINTERPRETATION 3D
# ============================================================

# ------------------------------------------------------------
# DEFENDER - ATARI 2600 (1980)
# ------------------------------------------------------------

# Version du jeu d'arcade classique de Williams.
# Gameplay en 2D avec defilement horizontal.
# A separer de la reinterpretation sortie en 2002.

masque_defender_1980 = (
    (df["Name"] == "Defender")
    & (df["Platform"] == "2600")
    & (df["Year"] == 1980)
)

df.loc[masque_defender_1980, "Game_Title_Clean"] = 'Defender (1980)'


# ------------------------------------------------------------
# DEFENDER - GAMECUBE, PS2 ET XBOX (2002)
# ------------------------------------------------------------

# Reinterpretation en 3D du jeu original.
# Les trois plateformes correspondent au meme jeu.
# Elles doivent donc conserver un Game_ID commun.

masque_defender_2002 = (
    (df["Name"] == "Defender")
    & (df["Platform"].isin(["GC", "PS2", "XB"]))
    & (df["Year"] == 2002)
)

df.loc[masque_defender_2002, "Game_Title_Clean"] = 'Defender (2002)'

# ============================================================
# 7.X.36 - TALES OF DESTINY : ORIGINAL ET REMAKE
# ============================================================

# ------------------------------------------------------------
# TALES OF DESTINY - PLAYSTATION (1997)
# ------------------------------------------------------------

# Jeu original sorti sur PlayStation en 1997.
# A distinguer du remake PlayStation 2 de 2006.

masque_tales_destiny_1997 = (
    (df["Name"] == "Tales of Destiny")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1997)
)

df.loc[masque_tales_destiny_1997, "Game_Title_Clean"] = 'Tales of Destiny (1997)'


# ------------------------------------------------------------
# TALES OF DESTINY - PLAYSTATION 2 (2006)
# ------------------------------------------------------------

# Remake du jeu original avec un nouveau moteur graphique,
# un systeme de combat modernise et du contenu retravaille.
# Il doit posseder son propre Game_ID.

masque_tales_destiny_2006 = (
    (df["Name"] == "Tales of Destiny")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2006)
)

df.loc[masque_tales_destiny_2006, "Game_Title_Clean"] = 'Tales of Destiny (Remake 2006)'

# ============================================================
# 7.X.37 - ROMANCING SAGA : ORIGINAL ET REMAKE
# ============================================================

# ------------------------------------------------------------
# ROMANCING SAGA - SUPER NINTENDO (1992)
# ------------------------------------------------------------

# Jeu original sorti sur Super Nintendo.
# A distinguer du remake PlayStation 2 de 2005.

masque_romancing_saga_1992 = (
    (df["Name"] == "Romancing SaGa")
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1992)
)

df.loc[masque_romancing_saga_1992, "Game_Title_Clean"] = 'Romancing SaGa (1992)'


# ------------------------------------------------------------
# ROMANCING SAGA - PLAYSTATION 2 (2005)
# ------------------------------------------------------------

# Remake connu sous le nom Romancing SaGa: Minstrel Song.
# Nouvelle realisation en 3D et gameplay retravaille.
# Doit posseder un Game_ID distinct du jeu de 1992.

masque_romancing_saga_2005 = (
    (df["Name"] == "Romancing SaGa")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2005)
)

df.loc[masque_romancing_saga_2005, "Game_Title_Clean"] = 'Romancing SaGa (Minstrel Song - 2005)'

# ============================================================
# 7.X.38 - WARHAWK : JEU ORIGINAL ET REINTERPRETATION
# ============================================================

# ------------------------------------------------------------
# WARHAWK - PLAYSTATION (1995)
# ------------------------------------------------------------

# Jeu original de combat aerien sorti sur PlayStation.
# A distinguer du jeu multijoueur PS3 de 2007.

masque_warhawk_1995 = (
    (df["Name"] == "Warhawk")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1995)
)

df.loc[masque_warhawk_1995, "Game_Title_Clean"] = 'Warhawk (1995)'


# ------------------------------------------------------------
# WARHAWK - PLAYSTATION 3 (2007)
# ------------------------------------------------------------

# Reinterpretation multijoueur de la licence.
# Gameplay different du jeu PlayStation original.
# Doit posseder son propre Game_ID.

masque_warhawk_2007 = (
    (df["Name"] == "Warhawk")
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2007)
)

df.loc[masque_warhawk_2007, "Game_Title_Clean"] = 'Warhawk (2007)'

# ============================================================
# 7.X.39 - AREA 51 : JEU ORIGINAL ET FPS DE 2005
# ============================================================

# ------------------------------------------------------------
# AREA 51 - PLAYSTATION (1996)
# ------------------------------------------------------------

# Adaptation du jeu d'arcade original.
# Jeu de tir sur rails, different du FPS de 2005.

masque_area51_1996 = (
    (df["Name"] == "Area 51")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1996)
)

df.loc[masque_area51_1996, "Game_Title_Clean"] = 'Area 51 (1996)'


# ------------------------------------------------------------
# AREA 51 - PLAYSTATION 2 ET XBOX (2005)
# ------------------------------------------------------------

# Nouveau FPS developpe par Midway Austin.
# Les versions PS2 et Xbox correspondent au meme jeu.
# Elles doivent donc conserver un Game_ID commun.

masque_area51_2005 = (
    (df["Name"] == "Area 51")
    & (df["Platform"].isin(["PS2", "XB"]))
    & (df["Year"] == 2005)
)

df.loc[masque_area51_2005, "Game_Title_Clean"] = 'Area 51 (2005)'

# ============================================================
# 7.X.40 - Q*BERT : JEU ORIGINAL ET REINTERPRETATION DE 1999
# ============================================================

# ------------------------------------------------------------
# Q*BERT - ATARI 2600 (1982)
# ------------------------------------------------------------

# Adaptation du jeu d'arcade original.
# A distinguer de la nouvelle version PlayStation de 1999.

masque_qbert_1982 = (
    (df["Name"] == "Q*bert")
    & (df["Platform"] == "2600")
    & (df["Year"] == 1982)
)

df.loc[masque_qbert_1982, "Game_Title_Clean"] = 'Q*bert (1982)'


# ------------------------------------------------------------
# Q*BERT - PLAYSTATION (1999)
# ------------------------------------------------------------

# Reinterpretation du jeu original avec de nouveaux niveaux
# et des mecanismes de jeu supplementaires.
# Doit posseder son propre Game_ID.

masque_qbert_1999 = (
    (df["Name"] == "Q*bert")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1999)
)

df.loc[masque_qbert_1999, "Game_Title_Clean"] = 'Q*bert (1999)'

# ============================================================
# 7.X.41 - BOMBERMAN : SEPARATION DES JEUX DISTINCTS
# ============================================================

# Plusieurs jeux portent exactement le nom "Bomberman".
# Ils correspondent cependant a des productions differentes.
#
# On utilise la plateforme et l'annee pour les distinguer.
# Les autres jeux de la licence ne sont pas modifies.


# ------------------------------------------------------------
# BOMBERMAN - NES (1985)
# ------------------------------------------------------------

# Jeu original sur NES.

masque_bomberman_1985 = (
    (df["Name"] == "Bomberman")
    & (df["Platform"] == "NES")
    & (df["Year"] == 1985)
)

df.loc[masque_bomberman_1985, "Game_Title_Clean"] = 'Bomberman (1985)'


# ------------------------------------------------------------
# BOMBERMAN - NINTENDO DS (2005)
# ------------------------------------------------------------

# Episode distinct concu pour Nintendo DS.
# Ne correspond pas a un simple portage NES.

masque_bomberman_2005 = (
    (df["Name"] == "Bomberman")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2005)
)

df.loc[masque_bomberman_2005, "Game_Title_Clean"] = 'Bomberman (DS - 2005)'


# ------------------------------------------------------------
# BOMBERMAN - PSP (2006)
# ------------------------------------------------------------

# Episode PSP avec ses propres modes de jeu.
# A distinguer de la version Nintendo DS.

masque_bomberman_2006 = (
    (df["Name"] == "Bomberman")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2006)
)

df.loc[masque_bomberman_2006, "Game_Title_Clean"] = 'Bomberman (PSP - 2006)'


# ------------------------------------------------------------
# BOMBERMAN - WII (2008)
# ------------------------------------------------------------

# Episode Wii distinct des versions precedentes.

masque_bomberman_2008 = (
    (df["Name"] == "Bomberman")
    & (df["Platform"] == "Wii")
    & (df["Year"] == 2008)
)

df.loc[masque_bomberman_2008, "Game_Title_Clean"] = 'Bomberman (Wii - 2008)'


# ============================================================
# 7.X.42 - FINAL FANTASY : SEPARATION DES VERSIONS
# ============================================================

# Final Fantasy NES (1987) est le jeu original.
# Final Fantasy WonderSwan (2000) est une reed ition
# amelioree avec des graphismes retravailles.
#
# Ces deux versions doivent avoir des Game_ID differents.


# ------------------------------------------------------------
# FINAL FANTASY - NES (1987)
# ------------------------------------------------------------

masque_ff_nes = (
    (df["Name"] == "Final Fantasy")
    & (df["Platform"] == "NES")
    & (df["Year"] == 1987)
)

df.loc[masque_ff_nes, "Game_Title_Clean"] = 'Final Fantasy (1987)'


# ------------------------------------------------------------
# FINAL FANTASY - WONDERSWAN (2000)
# ------------------------------------------------------------

masque_ff_ws = (
    (df["Name"] == "Final Fantasy")
    & (df["Platform"] == "WS")
    & (df["Year"] == 2000)
)

df.loc[masque_ff_ws, "Game_Title_Clean"] = 'Final Fantasy (WonderSwan 2000)'


# ============================================================
# 7.X.43 - TALES OF PHANTASIA : SEPARATION DES VERSIONS
# ============================================================

# Trois editions distinctes du meme jeu :
#
# - SNES (1995) : version originale
# - PS (1998) : remake enrichi
# - GBA (2003) : adaptation portable modifiee
#
# Chaque edition doit posseder son propre Game_ID.
# Les ventes et les autres jeux ne sont pas modifies.


# ------------------------------------------------------------
# TALES OF PHANTASIA - SNES (1995)
# ------------------------------------------------------------

masque_tales_snes = (
    (df["Name"] == "Tales of Phantasia")
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1995)
)

df.loc[masque_tales_snes, "Game_Title_Clean"] = 'Tales of Phantasia (1995)'


# ------------------------------------------------------------
# TALES OF PHANTASIA - PLAYSTATION (1998)
# ------------------------------------------------------------

masque_tales_ps = (
    (df["Name"] == "Tales of Phantasia")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1998)
)

df.loc[masque_tales_ps, "Game_Title_Clean"] = 'Tales of Phantasia (PS 1998)'


# ------------------------------------------------------------
# TALES OF PHANTASIA - GAME BOY ADVANCE (2003)
# ------------------------------------------------------------

masque_tales_gba = (
    (df["Name"] == "Tales of Phantasia")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2003)
)

df.loc[masque_tales_gba, "Game_Title_Clean"] = 'Tales of Phantasia (GBA 2003)'


# ============================================================
# 7.X.44 - SUPER GHOULS 'N GHOSTS : SEPARATION DES VERSIONS
# ============================================================

# Deux editions distinctes :
#
# - SNES (1991) : version originale
# - GBA (2002) : adaptation enrichie avec mode Arrange
#
# Chaque edition doit posseder son propre Game_ID.
# Les ventes et les autres jeux ne sont pas modifies.


# ------------------------------------------------------------
# SUPER GHOULS 'N GHOSTS - SNES (1991)
# ------------------------------------------------------------

# Identifier uniquement la version originale SNES.

masque_ghouls_snes = (
    (df["Name"] == "Super Ghouls 'n Ghosts")
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1991)
)

# Attribuer un titre nettoye specifique.

df.loc[masque_ghouls_snes, "Game_Title_Clean"] = "Super Ghouls 'n Ghosts (1991)"


# ------------------------------------------------------------
# SUPER GHOULS 'N GHOSTS - GBA (2002)
# ------------------------------------------------------------

# Identifier uniquement la version Game Boy Advance.

masque_ghouls_gba = (
    (df["Name"] == "Super Ghouls 'n Ghosts")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2002)
)

# Distinguer l'adaptation enrichie de l'original.

df.loc[masque_ghouls_gba, "Game_Title_Clean"] = "Super Ghouls 'n Ghosts (GBA 2002)"


# ============================================================
# 7.X.45 - NEED FOR SPEED: PORSCHE UNLEASHED
# SEPARATION DES VERSIONS
# ============================================================

# Deux editions distinctes :
#
# - PS (1999) : version PlayStation
# - GBA (2004) : adaptation portable specifique
#
# Chaque edition doit posseder son propre Game_ID.
# Les ventes et les autres jeux ne sont pas modifies.


# ------------------------------------------------------------
# NEED FOR SPEED: PORSCHE UNLEASHED - PS (1999)
# ------------------------------------------------------------

# Identifier uniquement la version PlayStation.

masque_nfs_ps = (
    (df["Name"] == "Need for Speed: Porsche Unleashed")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1999)
)

# Attribuer un titre nettoye specifique.

df.loc[masque_nfs_ps, "Game_Title_Clean"] = 'Need for Speed: Porsche Unleashed (PS 1999)'


# ------------------------------------------------------------
# NEED FOR SPEED: PORSCHE UNLEASHED - GBA (2004)
# ------------------------------------------------------------

# Identifier uniquement la version Game Boy Advance.

masque_nfs_gba = (
    (df["Name"] == "Need for Speed: Porsche Unleashed")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2004)
)

# Distinguer l'adaptation portable de la version PS.

df.loc[masque_nfs_gba, "Game_Title_Clean"] = 'Need for Speed: Porsche Unleashed (GBA 2004)'


# ============================================================
# 7.X.46 - TACTICS OGRE : SEPARATION DES VERSIONS
# ============================================================

# Deux editions distinctes :
#
# - SNES (1995) : version originale
# - PSP (2010) : remake avec graphismes et gameplay
#                retravailles
#
# Chaque edition doit posseder son propre Game_ID.
# Les ventes et les autres jeux ne sont pas modifies.


# ------------------------------------------------------------
# TACTICS OGRE - SNES (1995)
# ------------------------------------------------------------

# Identifier uniquement la version originale SNES.

masque_tactics_snes = (
    (df["Name"] == "Tactics Ogre: Let Us Cling Together")
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1995)
)

# Attribuer un titre nettoye specifique.

df.loc[masque_tactics_snes, "Game_Title_Clean"] = 'Tactics Ogre: Let Us Cling Together (1995)'


# ------------------------------------------------------------
# TACTICS OGRE - PSP (2010)
# ------------------------------------------------------------

# Identifier uniquement le remake PSP.

masque_tactics_psp = (
    (df["Name"] == "Tactics Ogre: Let Us Cling Together")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2010)
)

# Distinguer le remake de la version originale.

df.loc[masque_tactics_psp, "Game_Title_Clean"] = 'Tactics Ogre: Let Us Cling Together (PSP 2010)'


# ============================================================
# 7.X.47 - SHINOBI : SEPARATION DES JEUX DISTINCTS
# ============================================================

# Deux jeux differents portent le meme nom :
#
# - PS2 (2002) : jeu d'action 3D avec Hotsuma
# - 3DS (2011) : nouvel episode avec Jiro Musashi
#
# Il ne s'agit pas de simples portages.
# Chaque jeu doit posseder son propre Game_ID.
#
# Les ventes et les autres jeux ne sont pas modifies.


# ------------------------------------------------------------
# SHINOBI - PLAYSTATION 2 (2002)
# ------------------------------------------------------------

# Identifier uniquement le jeu PS2 de 2002.

masque_shinobi_ps2 = (
    (df["Name"] == "Shinobi")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2002)
)

# Attribuer un titre nettoye specifique.

df.loc[masque_shinobi_ps2, "Game_Title_Clean"] = 'Shinobi (PS2 2002)'


# ------------------------------------------------------------
# SHINOBI - NINTENDO 3DS (2011)
# ------------------------------------------------------------

# Identifier uniquement le jeu 3DS de 2011.

masque_shinobi_3ds = (
    (df["Name"] == "Shinobi")
    & (df["Platform"] == "3DS")
    & (df["Year"] == 2011)
)

# Distinguer le jeu 3DS du jeu PS2.

df.loc[masque_shinobi_3ds, "Game_Title_Clean"] = 'Shinobi (3DS 2011)'




# ============================================================
# 8. CONTRÔLE DES REGROUPEMENTS
# ============================================================

print("\n=== CONTRÔLE DES JEUX HOMONYMES ===")

jeux_controles = [
    "Need for Speed: Most Wanted",
    "Mortal Kombat",
    "Sonic the Hedgehog"
]

controle = df[df["Name"].isin(jeux_controles)]

resultat = (
    controle.groupby("Game_Title_Clean")
    .agg(
        Nombre_Lignes=("Rank", "size"),
        Nombre_Plateformes=("Platform", "nunique"),
        Ventes_Mondiales=("Global_Sales", "sum")
    )
    .round(2)
)

print(resultat.to_string())

# Vérification des lignes qui n'auraient pas été classées
non_classes = controle[
    controle["Game_Title_Clean"] == controle["Name"]
]

print(f"\nLignes non classées : {len(non_classes)}")


# ============================================================
# 8 BIS. CORRECTION FINALE DES ÉDITIONS DE FINAL FANTASY IV
# ============================================================

# Final Fantasy II sur SNES (1991) correspond à
# Final Fantasy IV, commercialisé sous ce nom aux États-Unis.
df.loc[
    (df["Name"] == "Final Fantasy II")
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1991),
    "Game_Title_Clean"
] = "Final Fantasy IV (SNES 1991)"

# Réédition PlayStation de Final Fantasy IV (1997).
df.loc[
    (df["Name"] == "Final Fantasy IV")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1997),
    "Game_Title_Clean"
] = "Final Fantasy IV (PS 1997)"


# ============================================================
# 8 TER. SÉPARATION DES ÉDITIONS DE PARAPPA THE RAPPER
# ============================================================

# Sélection exacte du jeu.
masque_parappa = df["Name"] == "PaRappa The Rapper"

# Version originale PlayStation (1996).
df.loc[
    masque_parappa
    & (df["Platform"] == "PS")
    & (df["Year"] == 1996),
    "Game_Title_Clean"
] = "PaRappa The Rapper (PS 1996)"

# Réédition enrichie PSP (2006).
df.loc[
    masque_parappa
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2006),
    "Game_Title_Clean"
] = "PaRappa The Rapper (PSP 2006)"


# ============================================================
# 8 QUATER. SÉPARATION DES ÉDITIONS DE SLY 2
# ============================================================

# Sélection exacte de Sly 2: Band of Thieves.
masque_sly2 = df["Name"] == "Sly 2: Band of Thieves"

# Version originale PlayStation 2 (2004).
df.loc[
    masque_sly2
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2004),
    "Game_Title_Clean"
] = "Sly 2: Band of Thieves (PS2 2004)"

# Réédition HD PlayStation 3 (2010).
df.loc[
    masque_sly2
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2010),
    "Game_Title_Clean"
] = "Sly 2: Band of Thieves (HD PS3 2010)"


# ============================================================
# 8 QUINQUIES. SÉPARATION DES ÉDITIONS DE DISNEY'S ALADDIN
# ============================================================

# Sélection exacte du jeu Disney's Aladdin.
masque_aladdin = df["Name"] == "Disney's Aladdin"

# Version originale Super Nintendo (1993).
df.loc[
    masque_aladdin
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1993),
    "Game_Title_Clean"
] = "Disney's Aladdin (SNES 1993)"

# Réédition Game Boy Advance (2003).
df.loc[
    masque_aladdin
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2003),
    "Game_Title_Clean"
] = "Disney's Aladdin (GBA 2003)"


# ============================================================
# 8 SEXIES. SÉPARATION DES ÉDITIONS DE RESIDENT EVIL ZERO
# ============================================================

# Sélection exacte du jeu Resident Evil Zero.
masque_re_zero = df["Name"] == "Resident Evil Zero"

# Version originale GameCube (2002).
df.loc[
    masque_re_zero
    & (df["Platform"] == "GC")
    & (df["Year"] == 2002),
    "Game_Title_Clean"
] = "Resident Evil Zero (GC 2002)"

# Remaster HD de 2016 :
# Les versions PC, PS4 et Xbox One partagent le même Game_ID.
df.loc[
    masque_re_zero
    & df["Platform"].isin(["PC", "PS4", "XOne"])
    & (df["Year"] == 2016),
    "Game_Title_Clean"
] = "Resident Evil Zero (HD Remaster 2016)"


# ============================================================
# 8 SEPTIES. SÉPARATION DES ÉDITIONS DE TALES OF SYMPHONIA
# ============================================================

# Sélection exacte de Tales of Symphonia.
masque_symphonia = df["Name"] == "Tales of Symphonia"

# Version originale GameCube (2003).
df.loc[
    masque_symphonia
    & (df["Platform"] == "GC")
    & (df["Year"] == 2003),
    "Game_Title_Clean"
] = "Tales of Symphonia (GC 2003)"

# Réédition HD PlayStation 3 (2013).
df.loc[
    masque_symphonia
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2013),
    "Game_Title_Clean"
] = "Tales of Symphonia (HD PS3 2013)"


# ============================================================
# 8 OCTIES. SÉPARATION DES ÉDITIONS DE VALKYRIA CHRONICLES
# ============================================================

# Sélection exacte de Valkyria Chronicles.
masque_valkyria = df["Name"] == "Valkyria Chronicles"

# Version originale PlayStation 3 (2008).
df.loc[
    masque_valkyria
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2008),
    "Game_Title_Clean"
] = "Valkyria Chronicles (PS3 2008)"

# Version remasterisée PlayStation 4 (2016).
df.loc[
    masque_valkyria
    & (df["Platform"] == "PS4")
    & (df["Year"] == 2016),
    "Game_Title_Clean"
] = "Valkyria Chronicles (Remastered PS4 2016)"


# ============================================================
# 8 NONIES. SÉPARATION DES ÉDITIONS DE NINJA GAIDEN SIGMA
# ============================================================

# Sélection exacte de Ninja Gaiden Sigma.
masque_sigma = df["Name"] == "Ninja Gaiden Sigma"

# Version originale PlayStation 3 (2007).
df.loc[
    masque_sigma
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2007),
    "Game_Title_Clean"
] = "Ninja Gaiden Sigma (PS3 2007)"

# Édition enrichie Sigma Plus sur PS Vita (2012).
df.loc[
    masque_sigma
    & (df["Platform"] == "PSV")
    & (df["Year"] == 2012),
    "Game_Title_Clean"
] = "Ninja Gaiden Sigma Plus (PSV 2012)"


# ============================================================
# 8 DECIES. SÉPARATION DES ÉDITIONS D'OKAMI
# ============================================================

# Sélection exacte du jeu Okami.
masque_okami = df["Name"] == "Okami"

# Version originale PS2 (2006) et portage Wii (2008).
# Les deux plateformes partagent le même Game_ID.
df.loc[
    masque_okami
    & (
        ((df["Platform"] == "PS2") & (df["Year"] == 2006))
        | ((df["Platform"] == "Wii") & (df["Year"] == 2008))
    ),
    "Game_Title_Clean"
] = "Okami (Original 2006)"

# Remaster HD PlayStation 3 (2012).
# Cette édition possède un Game_ID distinct.
df.loc[
    masque_okami
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2012),
    "Game_Title_Clean"
] = "Okami (HD PS3 2012)"


# ============================================================
# 8 UNDECIES. SÉPARATION DES ÉDITIONS DE SHADOW OF THE COLOSSUS
# ============================================================

# Sélection exacte de Shadow of the Colossus.
masque_shadow = df["Name"] == "Shadow of the Colossus"

# Version originale PlayStation 2 (2005).
df.loc[
    masque_shadow
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2005),
    "Game_Title_Clean"
] = "Shadow of the Colossus (PS2 2005)"

# Remaster HD PlayStation 3 (2011).
df.loc[
    masque_shadow
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2011),
    "Game_Title_Clean"
] = "Shadow of the Colossus (HD PS3 2011)"


# ============================================================
# 8 DUODECIES. SÉPARATION DES ÉDITIONS DE BEATMANIA
# ============================================================

# Sélection exacte des jeux BeatMania.
masque_beatmania = df["Name"] == "BeatMania"

# Version originale PlayStation (1998).
df.loc[
    masque_beatmania
    & (df["Platform"] == "PS")
    & (df["Year"] == 1998),
    "Game_Title_Clean"
] = "BeatMania (PS 1998)"

# Version BeatMania IIDX sur PlayStation 2 (2006).
df.loc[
    masque_beatmania
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2006),
    "Game_Title_Clean"
] = "BeatMania (IIDX PS2 2006)"


# ============================================================
# 8 TREDECIES. SÉPARATION DES ÉDITIONS DE LODE RUNNER
# ============================================================

# Sélection exacte des jeux Lode Runner.
masque_lode_runner = df["Name"] == "Lode Runner"

# Version NES (1984).
df.loc[
    masque_lode_runner
    & (df["Platform"] == "NES")
    & (df["Year"] == 1984),
    "Game_Title_Clean"
] = "Lode Runner (NES 1984)"

# Version Nintendo DS (2006).
df.loc[
    masque_lode_runner
    & (df["Platform"] == "DS")
    & (df["Year"] == 2006),
    "Game_Title_Clean"
] = "Lode Runner (DS 2006)"


# ============================================================
# 8 QUATERDECIES. SÉPARATION DES ÉDITIONS DE KARAOKE REVOLUTION
# ============================================================

# Sélection exacte des jeux Karaoke Revolution.
masque_karaoke = df["Name"] == "Karaoke Revolution"

# Version originale PS2 (2003) et portage Xbox (2004).
df.loc[
    masque_karaoke
    & (
        ((df["Platform"] == "PS2") & (df["Year"] == 2003))
        | ((df["Platform"] == "XB") & (df["Year"] == 2004))
    ),
    "Game_Title_Clean"
] = "Karaoke Revolution (Original 2003)"

# Nouvelle édition de 2009 sur PS3, Wii et Xbox 360.
df.loc[
    masque_karaoke
    & (df["Platform"].isin(["PS3", "Wii", "X360"]))
    & (df["Year"] == 2009),
    "Game_Title_Clean"
] = "Karaoke Revolution (2009)"


# ============================================================
# 8 QUINDECIES. SÉPARATION DES ÉDITIONS DE YOU DON'T KNOW JACK
# ============================================================

# Sélection exacte des jeux You Don't Know Jack.
masque_jack = df["Name"] == "You Don't Know Jack"

# Version originale PC (1995).
df.loc[
    masque_jack
    & (df["Platform"] == "PC")
    & (df["Year"] == 1995),
    "Game_Title_Clean"
] = "You Don't Know Jack (PC 1995)"

# Édition PlayStation (1999).
df.loc[
    masque_jack
    & (df["Platform"] == "PS")
    & (df["Year"] == 1999),
    "Game_Title_Clean"
] = "You Don't Know Jack (PS 1999)"

# Nouvelle édition de 2011 sur quatre plateformes.
df.loc[
    masque_jack
    & (df["Platform"].isin(["DS", "PS3", "Wii", "X360"]))
    & (df["Year"] == 2011),
    "Game_Title_Clean"
] = "You Don't Know Jack (2011)"

# ============================================================
# 8 SEXDECIES. SÉPARATION DES ÉDITIONS DE DOOM
# ============================================================

# Sélection exacte du jeu Doom.
masque_doom = df["Name"] == "Doom"

# Version originale PC et portage Game Boy Advance.
df.loc[
    masque_doom
    & (
        ((df["Platform"] == "PC") & (df["Year"].isin([1992, 1993])))
        | ((df["Platform"] == "GBA") & (df["Year"] == 2001))
    ),
    "Game_Title_Clean"
] = "Doom (Original 1993)"

# Adaptation PlayStation.
df.loc[
    masque_doom
    & (df["Platform"] == "PS")
    & (df["Year"].isin([1994, 1995])),
    "Game_Title_Clean"
] = "Doom (PS 1995)"

# ============================================================
# 8 SEPTDECIES. SÉPARATION DES ÉDITIONS DE SHIREN THE WANDERER
# ============================================================

# Sélection exacte du jeu.
masque_shiren = (
    df["Name"] == "Mystery Dungeon: Shiren the Wanderer"
)

# Version originale Super Nintendo de 1995.
df.loc[
    masque_shiren
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1995),
    "Game_Title_Clean"
] = "Mystery Dungeon: Shiren the Wanderer (1995)"

# Remake Nintendo DS de 2006.
df.loc[
    masque_shiren
    & (df["Platform"] == "DS")
    & (df["Year"] == 2006),
    "Game_Title_Clean"
] = "Mystery Dungeon: Shiren the Wanderer (DS 2006)"

# ============================================================
# 8 OCTODECIES. SÉPARATION DES ÉDITIONS DE RESIDENT EVIL
# ============================================================

# Sélection exacte du jeu Resident Evil.
masque_resident_evil = df["Name"] == "Resident Evil"

# Jeu original PlayStation 1996 et portage Saturn 1997.
df.loc[
    masque_resident_evil
    & (
        ((df["Platform"] == "PS") & (df["Year"] == 1996))
        | ((df["Platform"] == "SAT") & (df["Year"] == 1997))
    ),
    "Game_Title_Clean"
] = "Resident Evil (1996)"

# Réédition numérique PS3 de 2006,
# probablement basée sur Resident Evil: Director's Cut.
df.loc[
    masque_resident_evil
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2006),
    "Game_Title_Clean"
] = "Resident Evil: Director's Cut (PSN 2006)"

# ============================================================
# 8 OCTODECIES. REGROUPEMENT DES ÉDITIONS DE RESIDENT EVIL
# ============================================================

# Jeu original PlayStation 1996 et portage Saturn 1997.
masque_resident_original = (
    (df["Name"] == "Resident Evil")
    & (
        ((df["Platform"] == "PS") & (df["Year"] == 1996))
        | ((df["Platform"] == "SAT") & (df["Year"] == 1997))
    )
)

df.loc[masque_resident_original, "Game_Title_Clean"] = 'Resident Evil (1996)'


# Édition Director's Cut :
# - PlayStation (Rank 326)
# - PlayStation 3 (Rank 13533)
# - PlayStation 3, nom générique Resident Evil (Rank 9673)
#
# La ligne 9673 est rattachée provisoirement à Director's Cut.
# Les deux lignes PS3 sont conservées pour vérification
# d'un éventuel chevauchement commercial.

ranks_directors_cut = [326, 13533, 9673]

masque_directors_cut = (
    df["Rank"].isin(ranks_directors_cut)
)

# Sécurité : vérifier les trois enregistrements attendus.
assert masque_directors_cut.sum() == 3, (
    "Resident Evil Director's Cut : lignes manquantes !"
)

df.loc[
    masque_directors_cut,
    "Game_Title_Clean"
] = "Resident Evil Director's Cut"

# ============================================================
# 8 NOVODECIES. SÉPARATION DES VERSIONS DE FINAL FANTASY VI
# ============================================================

# Final Fantasy VI est sorti sur SNES en 1994.
# En Amérique du Nord, il était commercialisé
# sous le nom Final Fantasy III.
#
# La version PlayStation de 1999 est une réédition
# enrichie, notamment avec des cinématiques.
#
# Selon notre règle de classification :
# une réédition enrichie possède son propre Game_ID.


# ------------------------------------------------------------
# 1. VERSION ORIGINALE SNES (1994)
# ------------------------------------------------------------

masque_ffvi_snes = (
    (df["Rank"] == 390)
    & (df["Name"] == "Final Fantasy III")
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1994)
)

df.loc[masque_ffvi_snes, "Game_Title_Clean"] = 'Final Fantasy VI (1994)'


# ------------------------------------------------------------
# 2. RÉÉDITION PLAYSTATION (1999)
# ------------------------------------------------------------

masque_ffvi_ps = (
    (df["Rank"] == 11455)
    & (df["Name"] == "Final Fantasy VI")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1999)
)

df.loc[masque_ffvi_ps, "Game_Title_Clean"] = 'Final Fantasy VI (PS 1999)'


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

assert masque_ffvi_snes.sum() == 1, (
    "Final Fantasy VI : version SNES introuvable !"
)

assert masque_ffvi_ps.sum() == 1, (
    "Final Fantasy VI : version PS introuvable !"
)

assert round(
    df.loc[
        masque_ffvi_snes | masque_ffvi_ps,
        "Global_Sales"
    ].sum(), 2
) == 3.50, (
    "Final Fantasy VI : total des ventes incorrect !"
)
# ============================================================
# 8 VIGESIES. SÉPARATION DES VERSIONS DE TALES OF DESTINY 2
# ============================================================

# Version originale PlayStation 2 sortie en 2002.
# Réédition PSP sortie en 2007 avec des adaptations
# et du contenu supplémentaire.
#
# Selon notre règle de classification :
# une réédition enrichie possède son propre Game_ID.


# ------------------------------------------------------------
# 1. VERSION ORIGINALE PS2 (2002)
# ------------------------------------------------------------

masque_tod2_ps2 = (
    (df["Rank"] == 2593)
    & (df["Name"] == "Tales of Destiny 2")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2002)
)

df.loc[masque_tod2_ps2, "Game_Title_Clean"] = 'Tales of Destiny 2 (2002)'


# ------------------------------------------------------------
# 2. RÉÉDITION PSP (2007)
# ------------------------------------------------------------

masque_tod2_psp = (
    (df["Rank"] == 9950)
    & (df["Name"] == "Tales of Destiny 2")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2007)
)

df.loc[masque_tod2_psp, "Game_Title_Clean"] = 'Tales of Destiny 2 (PSP 2007)'


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

assert masque_tod2_ps2.sum() == 1, (
    "Tales of Destiny 2 : version PS2 introuvable !"
)

assert masque_tod2_psp.sum() == 1, (
    "Tales of Destiny 2 : version PSP introuvable !"
)

assert round(
    df.loc[
        masque_tod2_ps2 | masque_tod2_psp,
        "Global_Sales"
    ].sum(), 2
) == 0.92, (
    "Tales of Destiny 2 : total des ventes incorrect !"
)


# ============================================================
# 8 UNVIGESIES. SÉPARATION DES VERSIONS DE YAKUZA
# ============================================================

# Version originale PlayStation 2 sortie en 2005.
#
# La ligne PS3 de 2012 est provisoirement considérée
# comme une réédition HD du premier Yakuza.
#
# Selon notre règle de classification :
# un remaster possède son propre Game_ID.


# ------------------------------------------------------------
# 1. VERSION ORIGINALE PS2 (2005)
# ------------------------------------------------------------

masque_yakuza_ps2 = (
    (df["Rank"] == 2567)
    & (df["Name"] == "Yakuza")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2005)
)

df.loc[masque_yakuza_ps2, "Game_Title_Clean"] = 'Yakuza (2005)'


# ------------------------------------------------------------
# 2. RÉÉDITION HD PS3 (2012)
# ------------------------------------------------------------

masque_yakuza_ps3 = (
    (df["Rank"] == 10000)
    & (df["Name"] == "Yakuza")
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2012)
)

df.loc[masque_yakuza_ps3, "Game_Title_Clean"] = 'Yakuza (PS3 HD 2012)'


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

assert masque_yakuza_ps2.sum() == 1, (
    "Yakuza : version PS2 introuvable !"
)

assert masque_yakuza_ps3.sum() == 1, (
    "Yakuza : version PS3 introuvable !"
)

assert round(
    df.loc[
        masque_yakuza_ps2 | masque_yakuza_ps3,
        "Global_Sales"
    ].sum(), 2
) == 0.91, (
    "Yakuza : total des ventes incorrect !"
)

# ============================================================
# 8 DUOVIGESIES. SÉPARATION DES ÉDITIONS DE BACKYARD FOOTBALL
# ============================================================

# Les jeux de 2002 et de 2007 correspondent à deux
# générations différentes de Backyard Football.
#
# Regroupement provisoire :
# - GBA et GameCube : édition 2002
# - Nintendo DS et Wii : édition 2007
#
# Les différences entre plateformes pourront être
# examinées ultérieurement si nécessaire.


# ------------------------------------------------------------
# 1. ÉDITION 2002 : GBA ET GAMECUBE
# ------------------------------------------------------------

masque_backyard_2002 = (
    (df["Name"] == "Backyard NFL Football")
    & (df["Rank"].isin([3586, 6592]))
    & (df["Year"] == 2002)
    & (df["Platform"].isin(["GBA", "GC"]))
)

assert masque_backyard_2002.sum() == 2, (
    "Backyard Football 2002 : lignes manquantes !"
)

df.loc[
    masque_backyard_2002,
    "Game_Title_Clean"
] = "Backyard Football (2002)"


# ------------------------------------------------------------
# 2. ÉDITION 2007 : NINTENDO DS ET WII
# ------------------------------------------------------------

masque_backyard_2007 = (
    (df["Name"] == "Backyard NFL Football")
    & (df["Rank"].isin([15031, 14825]))
    & (df["Year"] == 2007)
    & (df["Platform"].isin(["DS", "Wii"]))
)

assert masque_backyard_2007.sum() == 2, (
    "Backyard Football 2007 : lignes manquantes !"
)

df.loc[
    masque_backyard_2007,
    "Game_Title_Clean"
] = "Backyard Football '08 (2007)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES QUATRE LIGNES
# ------------------------------------------------------------

masque_backyard_total = (
    masque_backyard_2002 | masque_backyard_2007
)

assert masque_backyard_total.sum() == 4, (
    "Backyard Football : nombre de lignes incorrect !"
)

assert round(
    df.loc[
        masque_backyard_total,
        "Global_Sales"
    ].sum(), 2
) == 0.87, (
    "Backyard Football : total des ventes incorrect !"
)

# ============================================================
# 8 TRESVIGESIES. SÉPARATION DES JEUX HOMONYMES BOXING
# ============================================================

# Deux jeux distincts portent le nom "Boxing" :
#
# - Atari 2600 (1980), édité par Activision
# - PlayStation (2000), édité par Midas Interactive
#
# Ces jeux ne doivent pas partager le même Game_ID.


# ------------------------------------------------------------
# 1. BOXING - ATARI 2600 (1980)
# ------------------------------------------------------------

masque_boxing_2600 = (
    (df["Rank"] == 2671)
    & (df["Name"] == "Boxing")
    & (df["Platform"] == "2600")
    & (df["Year"] == 1980)
)

assert masque_boxing_2600.sum() == 1, (
    "Boxing Atari 2600 : ligne introuvable !"
)

df.loc[
    masque_boxing_2600,
    "Game_Title_Clean"
] = "Boxing (Atari 2600 1980)"


# ------------------------------------------------------------
# 2. BOXING - PLAYSTATION (2000)
# ------------------------------------------------------------

masque_boxing_ps = (
    (df["Rank"] == 11770)
    & (df["Name"] == "Boxing")
    & (df["Platform"] == "PS")
    & (df["Year"] == 2000)
)

assert masque_boxing_ps.sum() == 1, (
    "Boxing PlayStation : ligne introuvable !"
)

df.loc[
    masque_boxing_ps,
    "Game_Title_Clean"
] = "Boxing (PS 2000)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX JEUX
# ------------------------------------------------------------

masque_boxing_total = (
    masque_boxing_2600 | masque_boxing_ps
)

assert masque_boxing_total.sum() == 2, (
    "Boxing : nombre de lignes incorrect !"
)

assert round(
    df.loc[
        masque_boxing_total,
        "Global_Sales"
    ].sum(), 2
) == 0.84, (
    "Boxing : total des ventes incorrect !"
)

# ============================================================
# 8 QUATTUORVIGESIES. SÉPARATION DES VERSIONS DE CASPER
# ============================================================

# Deux jeux portant le nom "Casper" :
#
# - PlayStation (1996), édité par Interplay
# - Game Boy Advance (2002), édité par Microids
#
# Ces deux adaptations sont classées séparément
# conformément à notre décision.
#
# Chaque jeu doit posséder son propre Game_ID.


# ------------------------------------------------------------
# 1. CASPER - PLAYSTATION (1996)
# ------------------------------------------------------------

masque_casper_ps = (
    (df["Rank"] == 2504)
    & (df["Name"] == "Casper")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1996)
)

assert masque_casper_ps.sum() == 1, (
    "Casper PlayStation : ligne introuvable !"
)

df.loc[
    masque_casper_ps,
    "Game_Title_Clean"
] = "Casper (PS 1996)"


# ------------------------------------------------------------
# 2. CASPER - GAME BOY ADVANCE (2002)
# ------------------------------------------------------------

masque_casper_gba = (
    (df["Rank"] == 16202)
    & (df["Name"] == "Casper")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2002)
)

assert masque_casper_gba.sum() == 1, (
    "Casper Game Boy Advance : ligne introuvable !"
)

df.loc[
    masque_casper_gba,
    "Game_Title_Clean"
] = "Casper (GBA 2002)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX JEUX
# ------------------------------------------------------------

masque_casper_total = (
    masque_casper_ps | masque_casper_gba
)

assert masque_casper_total.sum() == 2, (
    "Casper : nombre de lignes incorrect !"
)

assert round(
    df.loc[
        masque_casper_total,
        "Global_Sales"
    ].sum(), 2
) == 0.84, (
    "Casper : total des ventes incorrect !"
)

# ============================================================
# 8 QUINVIGESIES. SÉPARATION DES JEUX DYNASTY WARRIORS
# ============================================================

# Deux jeux différents portent le nom "Dynasty Warriors" :
#
# - PlayStation (1997) : jeu de combat en 3D
# - PSP (2004) : jeu d'action de type musou
#
# Il ne s'agit pas d'un simple portage.
# Chaque jeu doit donc posséder son propre Game_ID.


# ------------------------------------------------------------
# 1. DYNASTY WARRIORS - PLAYSTATION (1997)
# ------------------------------------------------------------

masque_dynasty_ps = (
    (df["Rank"] == 6277)
    & (df["Name"] == "Dynasty Warriors")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1997)
)

assert masque_dynasty_ps.sum() == 1, (
    "Dynasty Warriors PlayStation : ligne introuvable !"
)

df.loc[
    masque_dynasty_ps,
    "Game_Title_Clean"
] = "Dynasty Warriors (PS 1997)"


# ------------------------------------------------------------
# 2. DYNASTY WARRIORS - PSP (2004)
# ------------------------------------------------------------

masque_dynasty_psp = (
    (df["Rank"] == 3905)
    & (df["Name"] == "Dynasty Warriors")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2004)
)

assert masque_dynasty_psp.sum() == 1, (
    "Dynasty Warriors PSP : ligne introuvable !"
)

df.loc[
    masque_dynasty_psp,
    "Game_Title_Clean"
] = "Dynasty Warriors (PSP 2004)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX JEUX
# ------------------------------------------------------------

masque_dynasty_total = (
    masque_dynasty_ps | masque_dynasty_psp
)

assert masque_dynasty_total.sum() == 2, (
    "Dynasty Warriors : nombre de lignes incorrect !"
)

assert round(
    df.loc[
        masque_dynasty_total,
        "Global_Sales"
    ].sum(), 2
) == 0.78, (
    "Dynasty Warriors : total des ventes incorrect !"
)

# ============================================================
# 8 SEXVIGESIES. REGROUPEMENT DES VERSIONS DE SOUL HACKERS
# ============================================================

# Shin Megami Tensei: Devil Summoner - Soul Hackers
#
# - Saturn 1997 : version originale
# - PlayStation 1999 : portage de la version originale
# - Nintendo 3DS 2012 : réédition enrichie
#
# Décision :
# Saturn + PlayStation partagent un Game_ID.
# Nintendo 3DS possède un Game_ID distinct.


# ------------------------------------------------------------
# 1. VERSION ORIGINALE : SATURN ET PLAYSTATION
# ------------------------------------------------------------

masque_soul_hackers_original = (
    (df["Name"] == "Shin Megami Tensei: Devil Summoner - Soul Hackers")
    & (
        (
            (df["Rank"] == 5780)
            & (df["Platform"] == "SAT")
            & (df["Year"] == 1997)
        )
        |
        (
            (df["Rank"] == 8960)
            & (df["Platform"] == "PS")
            & (df["Year"] == 1999)
        )
    )
)

assert masque_soul_hackers_original.sum() == 2, (
    "Soul Hackers : versions Saturn/PS introuvables !"
)

df.loc[
    masque_soul_hackers_original,
    "Game_Title_Clean"
] = "Soul Hackers (1997)"


# ------------------------------------------------------------
# 2. RÉÉDITION NINTENDO 3DS (2012)
# ------------------------------------------------------------

masque_soul_hackers_3ds = (
    (df["Rank"] == 5909)
    & (df["Name"] == "Shin Megami Tensei: Devil Summoner - Soul Hackers")
    & (df["Platform"] == "3DS")
    & (df["Year"] == 2012)
)

assert masque_soul_hackers_3ds.sum() == 1, (
    "Soul Hackers : version 3DS introuvable !"
)

df.loc[
    masque_soul_hackers_3ds,
    "Game_Title_Clean"
] = "Soul Hackers (3DS 2012)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES TROIS VERSIONS
# ------------------------------------------------------------

masque_soul_hackers_total = (
    masque_soul_hackers_original | masque_soul_hackers_3ds
)

assert masque_soul_hackers_total.sum() == 3, (
    "Soul Hackers : nombre de lignes incorrect !"
)

assert round(
    df.loc[
        masque_soul_hackers_total,
        "Global_Sales"
    ].sum(), 2
) == 0.76, (
    "Soul Hackers : total des ventes incorrect !"
)


# ============================================================
# 8 SEPTEMVIGESIES. SÉPARATION DES JEUX FIFA SOCCER
# ============================================================

# Deux éditions différentes portent le nom "FIFA Soccer" :
#
# - PSP (2005) : première génération de FIFA sur PSP
# - PS Vita (2012) : édition destinée à la PS Vita
#
# Il ne s'agit pas d'un simple portage.
# Chaque édition doit posséder son propre Game_ID.


# ------------------------------------------------------------
# 1. FIFA SOCCER - PSP (2005)
# ------------------------------------------------------------

masque_fifa_soccer_psp = (
    (df["Rank"] == 9994)
    & (df["Name"] == "FIFA Soccer")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2005)
)

assert masque_fifa_soccer_psp.sum() == 1, (
    "FIFA Soccer PSP : ligne introuvable !"
)

df.loc[
    masque_fifa_soccer_psp,
    "Game_Title_Clean"
] = "FIFA Soccer (PSP 2005)"


# ------------------------------------------------------------
# 2. FIFA SOCCER - PS VITA (2012)
# ------------------------------------------------------------

masque_fifa_soccer_psv = (
    (df["Rank"] == 3262)
    & (df["Name"] == "FIFA Soccer")
    & (df["Platform"] == "PSV")
    & (df["Year"] == 2012)
)

assert masque_fifa_soccer_psv.sum() == 1, (
    "FIFA Soccer PS Vita : ligne introuvable !"
)

df.loc[
    masque_fifa_soccer_psv,
    "Game_Title_Clean"
] = "FIFA Soccer (PSV 2012)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX ÉDITIONS
# ------------------------------------------------------------

masque_fifa_soccer_total = (
    masque_fifa_soccer_psp | masque_fifa_soccer_psv
)

assert masque_fifa_soccer_total.sum() == 2, (
    "FIFA Soccer : nombre de lignes incorrect !"
)

assert round(
    df.loc[
        masque_fifa_soccer_total,
        "Global_Sales"
    ].sum(), 2
) == 0.74, (
    "FIFA Soccer : total des ventes incorrect !"
)

# ============================================================
# 8 OCTOVIGESIES. REGROUPEMENT DES VERSIONS DE THEME PARK
# ============================================================

# Theme Park, développé initialement par Bullfrog :
#
# - PlayStation (1995) : adaptation du jeu original
# - Saturn (1995) : adaptation du jeu original
# - Nintendo DS (2007) : réédition enrichie
#
# Décision :
# PS + Saturn partagent un Game_ID.
# Nintendo DS possède un Game_ID distinct.
#
# Les corrections d'années PS/SAT sont appliquées en section 3 BIS.


# ------------------------------------------------------------
# 1. VERSION ORIGINALE : PLAYSTATION ET SATURN
# ------------------------------------------------------------


# REGROUPEMENT ORIGINAL
masque_theme_park_original = (
    (df["Name"] == "Theme Park")
    & (
        (
            (df["Rank"] == 3507)
            & (df["Platform"] == "PS")
            & (df["Year"] == 1995)
        )
        |
        (
            (df["Rank"] == 11283)
            & (df["Platform"] == "SAT")
            & (df["Year"] == 1995)
        )
    )
)

assert masque_theme_park_original.sum() == 2, (
    "Theme Park : versions PS/Saturn introuvables !"
)

df.loc[
    masque_theme_park_original,
    "Game_Title_Clean"
] = "Theme Park (1994)"


# ------------------------------------------------------------
# 2. RÉÉDITION NINTENDO DS (2007)
# ------------------------------------------------------------

masque_theme_park_ds = (
    (df["Rank"] == 11971)
    & (df["Name"] == "Theme Park")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2007)
)

assert masque_theme_park_ds.sum() == 1, (
    "Theme Park : version Nintendo DS introuvable !"
)

df.loc[
    masque_theme_park_ds,
    "Game_Title_Clean"
] = "Theme Park (DS 2007)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES TROIS VERSIONS
# ------------------------------------------------------------

masque_theme_park_total = (
    masque_theme_park_original | masque_theme_park_ds
)

assert masque_theme_park_total.sum() == 3, (
    "Theme Park : nombre de lignes incorrect !"
)

assert round(
    df.loc[
        masque_theme_park_total,
        "Global_Sales"
    ].sum(), 2
) == 0.72, (
    "Theme Park : total des ventes incorrect !"
)

# ============================================================
# 8 NOVEMVIGESIES. SÉPARATION DES VERSIONS DE SAMURAI WARRIORS 2
# ============================================================

# Samurai Warriors 2 :
#
# - PlayStation 2 (2006) : jeu original
# - Xbox 360 (2006) : version du jeu original
# - PlayStation 3 (2013) : réédition HD probable
#
# Décision :
# PS2 + Xbox 360 partagent un Game_ID.
# PS3 possède un Game_ID distinct.
#
# L'identification exacte de l'édition PS3 reste à confirmer.


# ------------------------------------------------------------
# 1. VERSION ORIGINALE : PS2 ET XBOX 360
# ------------------------------------------------------------

masque_samurai_2_original = (
    (df["Name"] == "Samurai Warriors 2")
    & (
        (
            (df["Rank"] == 3291)
            & (df["Platform"] == "PS2")
            & (df["Year"] == 2006)
        )
        |
        (
            (df["Rank"] == 11594)
            & (df["Platform"] == "X360")
            & (df["Year"] == 2006)
        )
    )
)

assert masque_samurai_2_original.sum() == 2, (
    "Samurai Warriors 2 : versions PS2/X360 introuvables !"
)

df.loc[
    masque_samurai_2_original,
    "Game_Title_Clean"
] = "Samurai Warriors 2 (2006)"


# ------------------------------------------------------------
# 2. RÉÉDITION PLAYSTATION 3 (2013)
# ------------------------------------------------------------

masque_samurai_2_ps3 = (
    (df["Rank"] == 14690)
    & (df["Name"] == "Samurai Warriors 2")
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2013)
)

assert masque_samurai_2_ps3.sum() == 1, (
    "Samurai Warriors 2 : version PS3 introuvable !"
)

df.loc[
    masque_samurai_2_ps3,
    "Game_Title_Clean"
] = "Samurai Warriors 2 (PS3 HD 2013)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES TROIS VERSIONS
# ------------------------------------------------------------

masque_samurai_2_total = (
    masque_samurai_2_original | masque_samurai_2_ps3
)

assert masque_samurai_2_total.sum() == 3, (
    "Samurai Warriors 2 : nombre de lignes incorrect !"
)

assert round(
    df.loc[
        masque_samurai_2_total,
        "Global_Sales"
    ].sum(), 2
) == 0.72, (
    "Samurai Warriors 2 : total des ventes incorrect !"
)

# ============================================================
# 8 TRIGESIES. SÉPARATION DES JEUX CUSTOM ROBO
# ============================================================

# Deux épisodes différents portent le nom "Custom Robo" :
#
# - Nintendo 64 (1999) : premier épisode de la franchise
# - GameCube (2004) : épisode distinct, également connu
#   sous le nom Custom Robo: Battle Revolution
#
# Il ne s'agit pas d'un simple portage.
# Chaque épisode doit posséder son propre Game_ID.


# ------------------------------------------------------------
# 1. CUSTOM ROBO - NINTENDO 64 (1999)
# ------------------------------------------------------------

masque_custom_robo_n64 = (
    (df["Rank"] == 5510)
    & (df["Name"] == "Custom Robo")
    & (df["Platform"] == "N64")
    & (df["Year"] == 1999)
)

assert masque_custom_robo_n64.sum() == 1, (
    "Custom Robo Nintendo 64 : ligne introuvable !"
)

df.loc[
    masque_custom_robo_n64,
    "Game_Title_Clean"
] = "Custom Robo (N64 1999)"


# ------------------------------------------------------------
# 2. CUSTOM ROBO - GAMECUBE (2004)
# ------------------------------------------------------------

masque_custom_robo_gc = (
    (df["Rank"] == 5130)
    & (df["Name"] == "Custom Robo")
    & (df["Platform"] == "GC")
    & (df["Year"] == 2004)
)

assert masque_custom_robo_gc.sum() == 1, (
    "Custom Robo GameCube : ligne introuvable !"
)

df.loc[
    masque_custom_robo_gc,
    "Game_Title_Clean"
] = "Custom Robo (GC 2004)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX JEUX
# ------------------------------------------------------------

masque_custom_robo_total = (
    masque_custom_robo_n64 | masque_custom_robo_gc
)

assert masque_custom_robo_total.sum() == 2, (
    "Custom Robo : nombre de lignes incorrect !"
)

assert round(
    df.loc[
        masque_custom_robo_total,
        "Global_Sales"
    ].sum(), 2
) == 0.70, (
    "Custom Robo : total des ventes incorrect !"
)

# ============================================================
# 8 UNTRIGESIES. SÉPARATION DES VERSIONS DE TALES OF HEARTS
# ============================================================

# Tales of Hearts existe sous deux versions distinctes :
#
# - Nintendo DS (2008) : jeu original
# - PlayStation Vita (2013) : remake intitulé Tales of Hearts R
#
# Le remake PS Vita possède des graphismes 3D,
# un système de combat retravaillé et du contenu supplémentaire.
#
# Décision :
# Chaque version doit posséder son propre Game_ID.


# ------------------------------------------------------------
# 1. TALES OF HEARTS - NINTENDO DS (2008)
# ------------------------------------------------------------

masque_tales_hearts_ds = (
    (df["Rank"] == 6773)
    & (df["Name"] == "Tales of Hearts")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2008)
)

assert masque_tales_hearts_ds.sum() == 1, (
    "Tales of Hearts : version Nintendo DS introuvable !"
)

df.loc[
    masque_tales_hearts_ds,
    "Game_Title_Clean"
] = "Tales of Hearts (2008)"


# ------------------------------------------------------------
# 2. TALES OF HEARTS R - PLAYSTATION VITA (2013)
# ------------------------------------------------------------

masque_tales_hearts_psv = (
    (df["Rank"] == 4314)
    & (df["Name"] == "Tales of Hearts")
    & (df["Platform"] == "PSV")
    & (df["Year"] == 2013)
)

assert masque_tales_hearts_psv.sum() == 1, (
    "Tales of Hearts R : version PS Vita introuvable !"
)

df.loc[
    masque_tales_hearts_psv,
    "Game_Title_Clean"
] = "Tales of Hearts R (2013)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_tales_hearts_total = (
    masque_tales_hearts_ds | masque_tales_hearts_psv
)

# Vérification du nombre de lignes
assert masque_tales_hearts_total.sum() == 2, (
    "Tales of Hearts : nombre de lignes incorrect !"
)

# Vérification des titres normalisés
assert df.loc[
    masque_tales_hearts_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Tales of Hearts : les deux versions ne sont pas séparées !"
)

# Vérification du total des ventes
assert round(
    df.loc[
        masque_tales_hearts_total,
        "Global_Sales"
    ].sum(), 2
) == 0.69, (
    "Tales of Hearts : total des ventes incorrect !"
)

# ============================================================
# 8 DUOTRIGESIES. SÉPARATION DES JEUX PRO YAKYUU TEAM O TSUKUROU!
# ============================================================

# Trois épisodes distincts de la série de gestion de baseball :
#
# - Saturn (1998) : Pro Yakyuu Team mo Tsukurou!
# - Dreamcast (1999) : Pro Yakyuu Team o Tsukurou!
# - Nintendo DS (2008) : Pro Yakyuu Team o Tsukurou!
#
# La version Dreamcast est une suite du jeu Saturn.
# La version DS est un épisode ultérieur.
#
# Décision :
# Chaque jeu possède son propre Game_ID.
#
# Le titre Saturn utilise "mo" au lieu de "o".
# Nous corrigeons uniquement Game_Title_Clean.
# La colonne Name d'origine reste inchangée.


# ------------------------------------------------------------
# 1. VERSION SATURN (1998)
# ------------------------------------------------------------

masque_yakyuu_sat = (
    (df["Rank"] == 6706)
    & (df["Name"] == "Pro Yakyuu Team o Tsukurou!")
    & (df["Platform"] == "SAT")
    & (df["Year"] == 1998)
)

assert masque_yakyuu_sat.sum() == 1, (
    "Pro Yakyuu Team : version Saturn introuvable !"
)

df.loc[
    masque_yakyuu_sat,
    "Game_Title_Clean"
] = "Pro Yakyuu Team mo Tsukurou! (1998)"


# ------------------------------------------------------------
# 2. VERSION DREAMCAST (1999)
# ------------------------------------------------------------

masque_yakyuu_dc = (
    (df["Rank"] == 6986)
    & (df["Name"] == "Pro Yakyuu Team o Tsukurou!")
    & (df["Platform"] == "DC")
    & (df["Year"] == 1999)
)

assert masque_yakyuu_dc.sum() == 1, (
    "Pro Yakyuu Team : version Dreamcast introuvable !"
)

df.loc[
    masque_yakyuu_dc,
    "Game_Title_Clean"
] = "Pro Yakyuu Team o Tsukurou! (1999)"


# ------------------------------------------------------------
# 3. VERSION NINTENDO DS (2008)
# ------------------------------------------------------------

masque_yakyuu_ds = (
    (df["Rank"] == 7882)
    & (df["Name"] == "Pro Yakyuu Team o Tsukurou!")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2008)
)

assert masque_yakyuu_ds.sum() == 1, (
    "Pro Yakyuu Team : version Nintendo DS introuvable !"
)

df.loc[
    masque_yakyuu_ds,
    "Game_Title_Clean"
] = "Pro Yakyuu Team o Tsukurou! (DS 2008)"


# ------------------------------------------------------------
# 4. CONTRÔLE DES TROIS JEUX
# ------------------------------------------------------------

masque_yakyuu_total = (
    masque_yakyuu_sat
    | masque_yakyuu_dc
    | masque_yakyuu_ds
)

# Vérifier que les trois lignes sont présentes
assert masque_yakyuu_total.sum() == 3, (
    "Pro Yakyuu Team : nombre de lignes incorrect !"
)

# Vérifier que les trois titres sont distincts
assert df.loc[
    masque_yakyuu_total,
    "Game_Title_Clean"
].nunique() == 3, (
    "Pro Yakyuu Team : les trois jeux ne sont pas séparés !"
)

# Vérifier que les ventes restent inchangées
assert round(
    df.loc[
        masque_yakyuu_total,
        "Global_Sales"
    ].sum(), 2
) == 0.67, (
    "Pro Yakyuu Team : total des ventes incorrect !"
)

# ============================================================
# 8 TRITRIGESIES. SÉPARATION DES VERSIONS DE BATTLEZONE
# ============================================================

# Battlezone :
#
# - Atari 2600 (1983) : adaptation du jeu d'arcade original
# - PSP (2006) : nouvelle interprétation du jeu
#
# La version PSP n'est pas un simple portage.
#
# Décision :
# Chaque version possède son propre Game_ID.
#
# L'année Atari 2600 a été corrigée de 1982 à 1983
# dans annees_a_verifier.csv, appliqué en section 3 BIS.


# ------------------------------------------------------------
# 1. BATTLEZONE - ATARI 2600 (1983)
# ------------------------------------------------------------

masque_battlezone_2600 = (
    (df["Rank"] == 3250)
    & (df["Name"] == "Battlezone")
    & (df["Platform"] == "2600")
    & (df["Year"] == 1983)
)

assert masque_battlezone_2600.sum() == 1, (
    "Battlezone Atari 2600 : ligne introuvable ou année incorrecte !"
)

df.loc[
    masque_battlezone_2600,
    "Game_Title_Clean"
] = "Battlezone (Atari 2600 1983)"


# ------------------------------------------------------------
# 2. BATTLEZONE - PSP (2006)
# ------------------------------------------------------------

masque_battlezone_psp = (
    (df["Rank"] == 14803)
    & (df["Name"] == "Battlezone")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2006)
)

assert masque_battlezone_psp.sum() == 1, (
    "Battlezone PSP : ligne introuvable !"
)

df.loc[
    masque_battlezone_psp,
    "Game_Title_Clean"
] = "Battlezone (PSP 2006)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_battlezone_total = (
    masque_battlezone_2600 | masque_battlezone_psp
)

# Vérifier le nombre de lignes
assert masque_battlezone_total.sum() == 2, (
    "Battlezone : nombre de lignes incorrect !"
)

# Vérifier que les deux versions ont des titres distincts
assert df.loc[
    masque_battlezone_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Battlezone : les deux versions ne sont pas séparées !"
)

# Vérifier le total des ventes
assert round(
    df.loc[
        masque_battlezone_total,
        "Global_Sales"
    ].sum(), 2
) == 0.65, (
    "Battlezone : total des ventes incorrect !"
)

# ============================================================
# 8 QUATTUORTRIGESIES. SÉPARATION DU PACK SONIC / MONKEY BALL
# ============================================================

# Compilation :
# 2 in 1 Combo Pack: Sonic Heroes / Super Monkey Ball Deluxe
#
# - Xbox (2005) : compilation identifiée
# - Xbox 360 (2013) : édition non confirmée
#
# L'année Xbox a été corrigée de 2004 à 2005
# dans annees_a_verifier.csv (section 3 BIS).
#
# Décision :
# Séparer les deux lignes pour éviter de regrouper
# des ventes dont l'identité commerciale est incertaine.
#
# La ligne Xbox 360 reste conservée dans le dataset.
# Son identification devra faire l'objet d'une vérification.


# ------------------------------------------------------------
# 1. NOM ORIGINAL DU JEU
# ------------------------------------------------------------

nom_pack_sonic = (
    "2 in 1 Combo Pack: Sonic Heroes / "
    "Super Monkey Ball Deluxe"
)


# ------------------------------------------------------------
# 2. VERSION XBOX (2005)
# ------------------------------------------------------------

masque_pack_sonic_xb = (
    (df["Rank"] == 3772)
    & (df["Name"] == nom_pack_sonic)
    & (df["Platform"] == "XB")
    & (df["Year"] == 2005)
)

assert masque_pack_sonic_xb.sum() == 1, (
    "Pack Sonic / Monkey Ball : version Xbox introuvable !"
)

df.loc[
    masque_pack_sonic_xb,
    "Game_Title_Clean"
] = (
    "2 in 1 Combo Pack: Sonic Heroes / "
    "Super Monkey Ball Deluxe (XB 2005)"
)


# ------------------------------------------------------------
# 3. VERSION XBOX 360 (2013) - À VÉRIFIER
# ------------------------------------------------------------

masque_pack_sonic_x360 = (
    (df["Rank"] == 9973)
    & (df["Name"] == nom_pack_sonic)
    & (df["Platform"] == "X360")
    & (df["Year"] == 2013)
)

assert masque_pack_sonic_x360.sum() == 1, (
    "Pack Sonic / Monkey Ball : ligne Xbox 360 introuvable !"
)

df.loc[
    masque_pack_sonic_x360,
    "Game_Title_Clean"
] = (
    "2 in 1 Combo Pack: Sonic Heroes / "
    "Super Monkey Ball Deluxe (X360 2013 - A verifier)"
)


# ------------------------------------------------------------
# 4. CONTRÔLE DES DEUX LIGNES
# ------------------------------------------------------------

masque_pack_sonic_total = (
    masque_pack_sonic_xb | masque_pack_sonic_x360
)

# Vérifier que les deux lignes sont présentes
assert masque_pack_sonic_total.sum() == 2, (
    "Pack Sonic / Monkey Ball : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_pack_sonic_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Pack Sonic / Monkey Ball : les lignes ne sont pas séparées !"
)

# Vérifier que les ventes sont conservées
assert round(
    df.loc[
        masque_pack_sonic_total,
        "Global_Sales"
    ].sum(), 2
) == 0.65, (
    "Pack Sonic / Monkey Ball : total des ventes incorrect !"
)

# ============================================================
# 8 QUINTRIGESIES. SÉPARATION DES VERSIONS DE FRONT MISSION
# ============================================================

# Front Mission existe sous plusieurs éditions :
#
# - SNES (1995) : jeu original
# - Nintendo DS (2007) : réédition enrichie du jeu original,
#   issue de Front Mission 1st
#
# La version DS propose notamment du contenu supplémentaire
# et une campagne jouable du point de vue de l'USN.
#
# Décision :
# Chaque version possède son propre Game_ID.
#
# Les années et les ventes restent inchangées.


# ------------------------------------------------------------
# 1. FRONT MISSION - SUPER NINTENDO (1995)
# ------------------------------------------------------------

masque_front_mission_snes = (
    (df["Rank"] == 3374)
    & (df["Name"] == "Front Mission")
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1995)
)

assert masque_front_mission_snes.sum() == 1, (
    "Front Mission : version SNES introuvable !"
)

df.loc[
    masque_front_mission_snes,
    "Game_Title_Clean"
] = "Front Mission (1995)"


# ------------------------------------------------------------
# 2. FRONT MISSION 1ST - NINTENDO DS (2007)
# ------------------------------------------------------------

masque_front_mission_ds = (
    (df["Rank"] == 13491)
    & (df["Name"] == "Front Mission")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2007)
)

assert masque_front_mission_ds.sum() == 1, (
    "Front Mission 1st : version Nintendo DS introuvable !"
)

df.loc[
    masque_front_mission_ds,
    "Game_Title_Clean"
] = "Front Mission 1st (DS 2007)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_front_mission_total = (
    masque_front_mission_snes | masque_front_mission_ds
)

# Vérifier que les deux lignes sont présentes
assert masque_front_mission_total.sum() == 2, (
    "Front Mission : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_front_mission_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Front Mission : les deux versions ne sont pas séparées !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_front_mission_total,
        "Global_Sales"
    ].sum(), 2
) == 0.64, (
    "Front Mission : total des ventes incorrect !"
)

# ============================================================
# 8 SEXTRIGESIES. SÉPARATION DES CINQ VERSIONS DE MOTOGP
# ============================================================

# Cinq éditions distinctes sont présentes dans notre dataset :
#
# - PS2 (2000) : MotoGP de Namco
# - GBA (2002) : adaptation portable développée par Visual Impact
# - Xbox (2002) : MotoGP: Ultimate Racing Technology (Climax)
# - PSP (2006) : MotoGP de Namco Bandai
# - Wii (2009) : MotoGP 08, développé par Milestone
#
# Décision validée :
# Les cinq éditions possèdent chacune leur propre Game_ID.
#
# Les versions GBA et Xbox de 2002 sont volontairement
# séparées, car leurs adaptations sont suffisamment différentes.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, les plateformes et les ventes sont conservées.


# ------------------------------------------------------------
# 1. MOTOGP - PLAYSTATION 2 (2000)
# ------------------------------------------------------------

masque_motogp_ps2 = (
    (df["Rank"] == 6359)
    & (df["Name"] == "MotoGP")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2000)
)

assert masque_motogp_ps2.sum() == 1, (
    "MotoGP : version PS2 2000 introuvable !"
)

df.loc[
    masque_motogp_ps2,
    "Game_Title_Clean"
] = "MotoGP (PS2 2000)"


# ------------------------------------------------------------
# 2. MOTOGP - GAME BOY ADVANCE (2002)
# ------------------------------------------------------------

masque_motogp_gba = (
    (df["Rank"] == 12775)
    & (df["Name"] == "MotoGP")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2002)
)

assert masque_motogp_gba.sum() == 1, (
    "MotoGP : version GBA 2002 introuvable !"
)

df.loc[
    masque_motogp_gba,
    "Game_Title_Clean"
] = "MotoGP (GBA 2002)"


# ------------------------------------------------------------
# 3. MOTOGP: ULTIMATE RACING TECHNOLOGY - XBOX (2002)
# ------------------------------------------------------------

masque_motogp_xb = (
    (df["Rank"] == 10874)
    & (df["Name"] == "MotoGP")
    & (df["Platform"] == "XB")
    & (df["Year"] == 2002)
)

assert masque_motogp_xb.sum() == 1, (
    "MotoGP : version Xbox 2002 introuvable !"
)

df.loc[
    masque_motogp_xb,
    "Game_Title_Clean"
] = "MotoGP: Ultimate Racing Technology (XB 2002)"


# ------------------------------------------------------------
# 4. MOTOGP - PLAYSTATION PORTABLE (2006)
# ------------------------------------------------------------

masque_motogp_psp = (
    (df["Rank"] == 14168)
    & (df["Name"] == "MotoGP")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2006)
)

assert masque_motogp_psp.sum() == 1, (
    "MotoGP : version PSP 2006 introuvable !"
)

df.loc[
    masque_motogp_psp,
    "Game_Title_Clean"
] = "MotoGP (PSP 2006)"


# ------------------------------------------------------------
# 5. MOTOGP 08 - NINTENDO WII (2009)
# ------------------------------------------------------------

masque_motogp_wii = (
    (df["Rank"] == 7967)
    & (df["Name"] == "MotoGP")
    & (df["Platform"] == "Wii")
    & (df["Year"] == 2009)
)

assert masque_motogp_wii.sum() == 1, (
    "MotoGP : version Wii 2009 introuvable !"
)

df.loc[
    masque_motogp_wii,
    "Game_Title_Clean"
] = "MotoGP 08 (Wii 2009)"


# ------------------------------------------------------------
# 6. CONTRÔLE DES CINQ VERSIONS
# ------------------------------------------------------------

masque_motogp_total = (
    masque_motogp_ps2
    | masque_motogp_gba
    | masque_motogp_xb
    | masque_motogp_psp
    | masque_motogp_wii
)

# Vérifier que les cinq lignes sont présentes
assert masque_motogp_total.sum() == 5, (
    "MotoGP : nombre de lignes incorrect !"
)

# Vérifier que les cinq titres normalisés sont distincts
assert df.loc[
    masque_motogp_total,
    "Game_Title_Clean"
].nunique() == 5, (
    "MotoGP : les cinq versions ne sont pas séparées !"
)

# Vérifier que les ventes mondiales restent inchangées
assert round(
    df.loc[
        masque_motogp_total,
        "Global_Sales"
    ].sum(), 2
) == 0.64, (
    "MotoGP : total des ventes incorrect !"
)

# ============================================================
# 8 SEPTENTRIGESIES. SÉPARATION DES VERSIONS DE SEGA BASS FISHING
# ============================================================

# Sega Bass Fishing existe sous deux éditions dans notre dataset :
#
# - Dreamcast (1999) : adaptation du jeu d'arcade original
# - Wii (2008) : réédition enrichie avec commandes Wiimote,
#   nouveaux lieux de pêche et contenu supplémentaire
#
# Décision validée :
# Chaque édition possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années et les ventes restent inchangées.


# ------------------------------------------------------------
# 1. SEGA BASS FISHING - DREAMCAST (1999)
# ------------------------------------------------------------

masque_sega_bass_dc = (
    (df["Rank"] == 11234)
    & (df["Name"] == "Sega Bass Fishing")
    & (df["Platform"] == "DC")
    & (df["Year"] == 1999)
)

assert masque_sega_bass_dc.sum() == 1, (
    "Sega Bass Fishing : version Dreamcast introuvable !"
)

df.loc[
    masque_sega_bass_dc,
    "Game_Title_Clean"
] = "Sega Bass Fishing (DC 1999)"


# ------------------------------------------------------------
# 2. SEGA BASS FISHING - NINTENDO WII (2008)
# ------------------------------------------------------------

masque_sega_bass_wii = (
    (df["Rank"] == 3903)
    & (df["Name"] == "Sega Bass Fishing")
    & (df["Platform"] == "Wii")
    & (df["Year"] == 2008)
)

assert masque_sega_bass_wii.sum() == 1, (
    "Sega Bass Fishing : version Wii introuvable !"
)

df.loc[
    masque_sega_bass_wii,
    "Game_Title_Clean"
] = "Sega Bass Fishing (Wii 2008)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_sega_bass_total = (
    masque_sega_bass_dc | masque_sega_bass_wii
)

# Vérifier que les deux lignes sont présentes
assert masque_sega_bass_total.sum() == 2, (
    "Sega Bass Fishing : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_sega_bass_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Sega Bass Fishing : les deux versions ne sont pas séparées !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_sega_bass_total,
        "Global_Sales"
    ].sum(), 2
) == 0.60, (
    "Sega Bass Fishing : total des ventes incorrect !"
)

# ============================================================
# 8 OCTOTRIGESIES. SÉPARATION DES TROIS VERSIONS DE SCRABBLE
# ============================================================

# Trois éditions distinctes sont présentes dans notre dataset :
#
# - PlayStation (1999) : version développée par Runecraft
# - Nintendo DS (2009) : Scrabble 2009 Edition, par Wizarbox
# - PSP (2009) : version Electronic Arts, par Stainless Games
#
# Décision validée :
# Chaque édition possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, les plateformes et les ventes sont conservées.


# ------------------------------------------------------------
# 1. SCRABBLE - PLAYSTATION (1999)
# ------------------------------------------------------------

masque_scrabble_ps = (
    (df["Rank"] == 6645)
    & (df["Name"] == "Scrabble")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1999)
)

assert masque_scrabble_ps.sum() == 1, (
    "Scrabble : version PlayStation 1999 introuvable !"
)

df.loc[
    masque_scrabble_ps,
    "Game_Title_Clean"
] = "Scrabble (PS 1999)"


# ------------------------------------------------------------
# 2. SCRABBLE 2009 EDITION - NINTENDO DS
# ------------------------------------------------------------

masque_scrabble_ds = (
    (df["Rank"] == 6639)
    & (df["Name"] == "Scrabble")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2009)
)

assert masque_scrabble_ds.sum() == 1, (
    "Scrabble : version Nintendo DS 2009 introuvable !"
)

df.loc[
    masque_scrabble_ds,
    "Game_Title_Clean"
] = "Scrabble 2009 Edition (DS)"


# ------------------------------------------------------------
# 3. SCRABBLE - PLAYSTATION PORTABLE (2009)
# ------------------------------------------------------------

masque_scrabble_psp = (
    (df["Rank"] == 11076)
    & (df["Name"] == "Scrabble")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2009)
)

assert masque_scrabble_psp.sum() == 1, (
    "Scrabble : version PSP 2009 introuvable !"
)

df.loc[
    masque_scrabble_psp,
    "Game_Title_Clean"
] = "Scrabble (EA PSP 2009)"


# ------------------------------------------------------------
# 4. CONTRÔLE DES TROIS VERSIONS
# ------------------------------------------------------------

masque_scrabble_total = (
    masque_scrabble_ps
    | masque_scrabble_ds
    | masque_scrabble_psp
)

# Vérifier que les trois lignes sont présentes
assert masque_scrabble_total.sum() == 3, (
    "Scrabble : nombre de lignes incorrect !"
)

# Vérifier que les trois titres normalisés sont distincts
assert df.loc[
    masque_scrabble_total,
    "Game_Title_Clean"
].nunique() == 3, (
    "Scrabble : les trois versions ne sont pas séparées !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_scrabble_total,
        "Global_Sales"
    ].sum(), 2
) == 0.59, (
    "Scrabble : total des ventes incorrect !"
)

# ============================================================
# 8 NOVEMTRIGESIES. SÉPARATION DES VERSIONS DE BREATH OF FIRE II
# ============================================================

# Breath of Fire II existe sous deux éditions dans notre dataset :
#
# - SNES (1994) : version originale développée par Capcom
# - GBA (2001) : réédition enrichie avec plusieurs adaptations,
#   ajustements et fonctionnalités supplémentaires
#
# Décision validée :
# Chaque édition possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, les plateformes et les ventes restent inchangées.


# ------------------------------------------------------------
# 1. BREATH OF FIRE II - SUPER NINTENDO (1994)
# ------------------------------------------------------------

masque_bof2_snes = (
    (df["Rank"] == 5219)
    & (df["Name"] == "Breath of Fire II")
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1994)
)

assert masque_bof2_snes.sum() == 1, (
    "Breath of Fire II : version SNES 1994 introuvable !"
)

df.loc[
    masque_bof2_snes,
    "Game_Title_Clean"
] = "Breath of Fire II (SNES 1994)"


# ------------------------------------------------------------
# 2. BREATH OF FIRE II - GAME BOY ADVANCE (2001)
# ------------------------------------------------------------

masque_bof2_gba = (
    (df["Rank"] == 7760)
    & (df["Name"] == "Breath of Fire II")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2001)
)

assert masque_bof2_gba.sum() == 1, (
    "Breath of Fire II : version GBA 2001 introuvable !"
)

df.loc[
    masque_bof2_gba,
    "Game_Title_Clean"
] = "Breath of Fire II (GBA 2001)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_bof2_total = (
    masque_bof2_snes | masque_bof2_gba
)

# Vérifier que les deux lignes sont présentes
assert masque_bof2_total.sum() == 2, (
    "Breath of Fire II : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_bof2_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Breath of Fire II : les deux versions ne sont pas séparées !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_bof2_total,
        "Global_Sales"
    ].sum(), 2
) == 0.55, (
    "Breath of Fire II : total des ventes incorrect !"
)

# ============================================================
# 8 QUADRAGESIES. SÉPARATION DES VERSIONS DE ICO
# ============================================================

# ICO existe sous deux éditions dans notre dataset :
#
# - PS2 (2001) : version originale développée par Team Ico
# - PS3 (2011) : remastérisation HD du jeu original
#
# La version PS3 propose notamment :
# - Une résolution haute définition
# - Une meilleure fluidité
# - La prise en charge de la 3D stéréoscopique
# - Des trophées PlayStation
#
# Décision validée :
# Chaque édition possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, les plateformes et les ventes restent inchangées.


# ------------------------------------------------------------
# 1. ICO - PLAYSTATION 2 (2001)
# ------------------------------------------------------------

masque_ico_ps2 = (
    (df["Rank"] == 4168)
    & (df["Name"] == "ICO")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2001)
)

assert masque_ico_ps2.sum() == 1, (
    "ICO : version PS2 2001 introuvable !"
)

df.loc[
    masque_ico_ps2,
    "Game_Title_Clean"
] = "ICO (PS2 2001)"


# ------------------------------------------------------------
# 2. ICO HD - PLAYSTATION 3 (2011)
# ------------------------------------------------------------

masque_ico_ps3 = (
    (df["Rank"] == 12499)
    & (df["Name"] == "ICO")
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2011)
)

assert masque_ico_ps3.sum() == 1, (
    "ICO HD : version PS3 2011 introuvable !"
)

df.loc[
    masque_ico_ps3,
    "Game_Title_Clean"
] = "ICO HD (PS3 2011)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_ico_total = (
    masque_ico_ps2 | masque_ico_ps3
)

# Vérifier que les deux lignes sont présentes
assert masque_ico_total.sum() == 2, (
    "ICO : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_ico_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "ICO : les deux versions ne sont pas séparées !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_ico_total,
        "Global_Sales"
    ].sum(), 2
) == 0.53, (
    "ICO : total des ventes incorrect !"
)

# ============================================================
# 8 UNQUADRAGESIES. SÉPARATION DES VERSIONS DE SID MEIER'S PIRATES!
# ============================================================

# Sid Meier's Pirates! existe sous trois éditions dans notre dataset :
#
# - Xbox (2005) : adaptation enrichie du remake PC de 2004
# - PSP (2007) : adaptation portable avec du contenu supplémentaire
# - Wii (2010) : adaptation avec commandes à mouvements et mini-jeux
#
# Décision validée :
# Chaque édition possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, les plateformes et les ventes restent inchangées.


# ------------------------------------------------------------
# 1. SID MEIER'S PIRATES! - XBOX (2005)
# ------------------------------------------------------------

masque_pirates_xb = (
    (df["Rank"] == 9190)
    & (df["Name"] == "Sid Meier's Pirates!")
    & (df["Platform"] == "XB")
    & (df["Year"] == 2005)
)

assert masque_pirates_xb.sum() == 1, (
    "Sid Meier's Pirates! : version Xbox 2005 introuvable !"
)

df.loc[
    masque_pirates_xb,
    "Game_Title_Clean"
] = "Sid Meier's Pirates! (XB 2005)"


# ------------------------------------------------------------
# 2. SID MEIER'S PIRATES! - PSP (2007)
# ------------------------------------------------------------

masque_pirates_psp = (
    (df["Rank"] == 7678)
    & (df["Name"] == "Sid Meier's Pirates!")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2007)
)

assert masque_pirates_psp.sum() == 1, (
    "Sid Meier's Pirates! : version PSP 2007 introuvable !"
)

df.loc[
    masque_pirates_psp,
    "Game_Title_Clean"
] = "Sid Meier's Pirates! (PSP 2007)"


# ------------------------------------------------------------
# 3. SID MEIER'S PIRATES! - NINTENDO WII (2010)
# ------------------------------------------------------------

masque_pirates_wii = (
    (df["Rank"] == 8467)
    & (df["Name"] == "Sid Meier's Pirates!")
    & (df["Platform"] == "Wii")
    & (df["Year"] == 2010)
)

assert masque_pirates_wii.sum() == 1, (
    "Sid Meier's Pirates! : version Wii 2010 introuvable !"
)

df.loc[
    masque_pirates_wii,
    "Game_Title_Clean"
] = "Sid Meier's Pirates! (Wii 2010)"


# ------------------------------------------------------------
# 4. CONTRÔLE DES TROIS VERSIONS
# ------------------------------------------------------------

masque_pirates_total = (
    masque_pirates_xb
    | masque_pirates_psp
    | masque_pirates_wii
)

# Vérifier que les trois lignes sont présentes
assert masque_pirates_total.sum() == 3, (
    "Sid Meier's Pirates! : nombre de lignes incorrect !"
)

# Vérifier que les trois titres normalisés sont distincts
assert df.loc[
    masque_pirates_total,
    "Game_Title_Clean"
].nunique() == 3, (
    "Sid Meier's Pirates! : les trois versions ne sont pas séparées !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_pirates_total,
        "Global_Sales"
    ].sum(), 2
) == 0.50, (
    "Sid Meier's Pirates! : total des ventes incorrect !"
)

# ============================================================
# 8 DUOQUADRAGESIES. SÉPARATION DES VERSIONS DE TOP GEAR RALLY
# ============================================================

# Top Gear Rally existe sous deux productions dans notre dataset :
#
# - N64 (1997) : jeu original développé par Boss Game Studios
# - GBA (2003) : nouvelle adaptation développée par Tantalus,
#   également connue au Japon sous le nom Top Gear Rally SP
#
# La version GBA n'est pas un simple portage du jeu N64.
#
# Décision validée :
# Chaque production possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, les plateformes et les ventes restent inchangées.


# ------------------------------------------------------------
# 1. TOP GEAR RALLY - NINTENDO 64 (1997)
# ------------------------------------------------------------

masque_top_gear_n64 = (
    (df["Rank"] == 4829)
    & (df["Name"] == "Top Gear Rally")
    & (df["Platform"] == "N64")
    & (df["Year"] == 1997)
)

assert masque_top_gear_n64.sum() == 1, (
    "Top Gear Rally : version N64 1997 introuvable !"
)

df.loc[
    masque_top_gear_n64,
    "Game_Title_Clean"
] = "Top Gear Rally (N64 1997)"


# ------------------------------------------------------------
# 2. TOP GEAR RALLY SP - GAME BOY ADVANCE (2003)
# ------------------------------------------------------------

masque_top_gear_gba = (
    (df["Rank"] == 11208)
    & (df["Name"] == "Top Gear Rally")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2003)
)

assert masque_top_gear_gba.sum() == 1, (
    "Top Gear Rally : version GBA 2003 introuvable !"
)

df.loc[
    masque_top_gear_gba,
    "Game_Title_Clean"
] = "Top Gear Rally SP (GBA 2003)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_top_gear_total = (
    masque_top_gear_n64 | masque_top_gear_gba
)

# Vérifier que les deux lignes sont présentes
assert masque_top_gear_total.sum() == 2, (
    "Top Gear Rally : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_top_gear_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Top Gear Rally : les deux versions ne sont pas séparées !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_top_gear_total,
        "Global_Sales"
    ].sum(), 2
) == 0.49, (
    "Top Gear Rally : total des ventes incorrect !"
)

# ============================================================
# 8 TRIQUADRAGESIES. SÉPARATION DES VERSIONS DE THE SMURFS
# ============================================================

# Trois jeux différents portent le nom The Smurfs :
#
# - PlayStation (1999) : jeu de plateformes Infogrames
# - Nintendo DS (2011) : jeu Ubisoft
# - Nintendo 3DS (2015) : nouvelle aventure Ubisoft
#
# Décision validée :
# Chaque version doit posséder son propre Game_ID.
#
# L'année PlayStation a déjà été corrigée de 1998 à 1999
# dans notre fichier de suivi des années.


# ------------------------------------------------------------
# 1. THE SMURFS - PLAYSTATION (1999)
# ------------------------------------------------------------

masque_smurfs_ps = (
    (df["Rank"] == 13572)
    & (df["Name"] == "The Smurfs")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1999)
)

assert masque_smurfs_ps.sum() == 1, (
    "The Smurfs : version PlayStation 1999 introuvable !"
)

df.loc[
    masque_smurfs_ps,
    "Game_Title_Clean"
] = "The Smurfs (PS 1999)"


# ------------------------------------------------------------
# 2. THE SMURFS - NINTENDO DS (2011)
# ------------------------------------------------------------

masque_smurfs_ds = (
    (df["Rank"] == 4561)
    & (df["Name"] == "The Smurfs")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2011)
)

assert masque_smurfs_ds.sum() == 1, (
    "The Smurfs : version Nintendo DS 2011 introuvable !"
)

df.loc[
    masque_smurfs_ds,
    "Game_Title_Clean"
] = "The Smurfs (DS 2011)"


# ------------------------------------------------------------
# 3. THE SMURFS - NINTENDO 3DS (2015)
# ------------------------------------------------------------

masque_smurfs_3ds = (
    (df["Rank"] == 16496)
    & (df["Name"] == "The Smurfs")
    & (df["Platform"] == "3DS")
    & (df["Year"] == 2015)
)

assert masque_smurfs_3ds.sum() == 1, (
    "The Smurfs : version Nintendo 3DS 2015 introuvable !"
)

df.loc[
    masque_smurfs_3ds,
    "Game_Title_Clean"
] = "The Smurfs (3DS 2015)"


# ------------------------------------------------------------
# 4. CONTRÔLE DES TROIS VERSIONS
# ------------------------------------------------------------

masque_smurfs_total = (
    masque_smurfs_ps
    | masque_smurfs_ds
    | masque_smurfs_3ds
)

# Vérifier que les trois lignes sont présentes
assert masque_smurfs_total.sum() == 3, (
    "The Smurfs : nombre de lignes incorrect !"
)

# Vérifier que les trois titres sont différents
assert df.loc[
    masque_smurfs_total,
    "Game_Title_Clean"
].nunique() == 3, (
    "The Smurfs : les trois versions ne sont pas séparées !"
)

# Vérifier que les ventes sont conservées
assert round(
    df.loc[
        masque_smurfs_total,
        "Global_Sales"
    ].sum(), 2
) == 0.48, (
    "The Smurfs : total des ventes incorrect !"
)

# ============================================================
# 8 QUATTUORQUADRAGESIES. SÉPARATION DES VERSIONS DE NIGHTS
# ============================================================

# NiGHTS into dreams... possède deux éditions :
#
# - Sega Saturn (1996) : version originale de Sonic Team
# - PlayStation 2 (2008) : réédition avec graphismes améliorés
#
# Décision validée :
# La version PS2 est un remaster distinct de l'original.
# Chaque édition doit donc posséder son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes et ventes restent inchangées.


# ------------------------------------------------------------
# 1. NIGHTS INTO DREAMS... - SEGA SATURN (1996)
# ------------------------------------------------------------

masque_nights_sat = (
    (df["Rank"] == 4509)
    & (df["Name"] == "NiGHTS into dreams...")
    & (df["Platform"] == "SAT")
    & (df["Year"] == 1996)
)

assert masque_nights_sat.sum() == 1, (
    "NiGHTS : version Saturn 1996 introuvable !"
)

df.loc[
    masque_nights_sat,
    "Game_Title_Clean"
] = "NiGHTS into dreams... (SAT 1996)"


# ------------------------------------------------------------
# 2. NIGHTS INTO DREAMS... - PLAYSTATION 2 (2008)
# ------------------------------------------------------------

masque_nights_ps2 = (
    (df["Rank"] == 16036)
    & (df["Name"] == "NiGHTS into dreams...")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2008)
)

assert masque_nights_ps2.sum() == 1, (
    "NiGHTS : version PS2 2008 introuvable !"
)

df.loc[
    masque_nights_ps2,
    "Game_Title_Clean"
] = "NiGHTS into dreams... (PS2 Remaster 2008)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_nights_total = (
    masque_nights_sat | masque_nights_ps2
)

# Vérifier que les deux lignes sont présentes
assert masque_nights_total.sum() == 2, (
    "NiGHTS : nombre de lignes incorrect !"
)

# Vérifier que les titres normalisés sont distincts
assert df.loc[
    masque_nights_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "NiGHTS : les deux éditions ne sont pas séparées !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_nights_total,
        "Global_Sales"
    ].sum(), 2
) == 0.44, (
    "NiGHTS : total des ventes incorrect !"
)

# ============================================================
# 8 QUINQUADRAGESIES. SÉPARATION DES VERSIONS DE PERSONA 2
# ============================================================

# Persona 2: Eternal Punishment possède deux éditions :
#
# - PlayStation (2000) : version originale d'Atlus
# - PSP (2012) : remaster avec améliorations graphiques,
#   interface retravaillée et scénario supplémentaire
#
# Décision validée :
# La version PSP constitue une réédition améliorée.
# Chaque édition doit donc posséder son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes et ventes restent inchangées.


# ------------------------------------------------------------
# 1. PERSONA 2: ETERNAL PUNISHMENT - PLAYSTATION (2000)
# ------------------------------------------------------------

masque_persona2_ps = (
    (df["Rank"] == 5296)
    & (df["Name"] == "Persona 2: Eternal Punishment")
    & (df["Platform"] == "PS")
    & (df["Year"] == 2000)
)

assert masque_persona2_ps.sum() == 1, (
    "Persona 2 : version PlayStation 2000 introuvable !"
)

df.loc[
    masque_persona2_ps,
    "Game_Title_Clean"
] = "Persona 2: Eternal Punishment (PS 2000)"


# ------------------------------------------------------------
# 2. PERSONA 2: ETERNAL PUNISHMENT - PSP (2012)
# ------------------------------------------------------------

masque_persona2_psp = (
    (df["Rank"] == 12951)
    & (df["Name"] == "Persona 2: Eternal Punishment")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2012)
)

assert masque_persona2_psp.sum() == 1, (
    "Persona 2 : version PSP 2012 introuvable !"
)

df.loc[
    masque_persona2_psp,
    "Game_Title_Clean"
] = "Persona 2: Eternal Punishment (PSP Remaster 2012)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_persona2_total = (
    masque_persona2_ps | masque_persona2_psp
)

# Vérifier que les deux lignes sont présentes
assert masque_persona2_total.sum() == 2, (
    "Persona 2 : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_persona2_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Persona 2 : les deux éditions ne sont pas séparées !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_persona2_total,
        "Global_Sales"
    ].sum(), 2
) == 0.40, (
    "Persona 2 : total des ventes incorrect !"
)

# ============================================================
# 8 SEXQUADRAGESIES. SÉPARATION DES VERSIONS DE SYNDICATE
# ============================================================

# Syndicate regroupe deux jeux différents :
#
# - PC (1993) : jeu original de stratégie de Bullfrog
# - PS3 / Xbox 360 (2012) : reboot FPS de Starbreeze
#
# Correction historique :
# L'année PC a été corrigée de 1992 à 1993
# dans notre fichier de suivi.
#
# Décision validée :
# Le jeu original et le reboot possèdent deux Game_ID distincts.
# Les versions PS3 et Xbox 360 partagent le même Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée ici.


# ------------------------------------------------------------
# 1. SYNDICATE - PC ORIGINAL (1993)
# ------------------------------------------------------------

masque_syndicate_pc = (
    (df["Rank"] == 12528)
    & (df["Name"] == "Syndicate")
    & (df["Platform"] == "PC")
    & (df["Year"] == 1993)
)

assert masque_syndicate_pc.sum() == 1, (
    "Syndicate : version PC 1993 introuvable !"
)

df.loc[
    masque_syndicate_pc,
    "Game_Title_Clean"
] = "Syndicate (Original 1993)"


# ------------------------------------------------------------
# 2. SYNDICATE - REBOOT PS3 (2012)
# ------------------------------------------------------------

masque_syndicate_ps3 = (
    (df["Rank"] == 8841)
    & (df["Name"] == "Syndicate")
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2012)
)

assert masque_syndicate_ps3.sum() == 1, (
    "Syndicate : version PS3 2012 introuvable !"
)

df.loc[
    masque_syndicate_ps3,
    "Game_Title_Clean"
] = "Syndicate (Reboot 2012)"


# ------------------------------------------------------------
# 3. SYNDICATE - REBOOT XBOX 360 (2012)
# ------------------------------------------------------------

masque_syndicate_x360 = (
    (df["Rank"] == 8002)
    & (df["Name"] == "Syndicate")
    & (df["Platform"] == "X360")
    & (df["Year"] == 2012)
)

assert masque_syndicate_x360.sum() == 1, (
    "Syndicate : version Xbox 360 2012 introuvable !"
)

df.loc[
    masque_syndicate_x360,
    "Game_Title_Clean"
] = "Syndicate (Reboot 2012)"


# ------------------------------------------------------------
# 4. CONTRÔLE DES TROIS LIGNES
# ------------------------------------------------------------

masque_syndicate_total = (
    masque_syndicate_pc
    | masque_syndicate_ps3
    | masque_syndicate_x360
)

# Vérifier que les trois lignes sont présentes
assert masque_syndicate_total.sum() == 3, (
    "Syndicate : nombre de lignes incorrect !"
)

# Vérifier qu'il existe exactement deux titres distincts
assert df.loc[
    masque_syndicate_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Syndicate : les deux jeux ne sont pas séparés correctement !"
)

# Vérifier que les versions PS3 et Xbox 360 sont regroupées
assert df.loc[
    masque_syndicate_ps3 | masque_syndicate_x360,
    "Game_Title_Clean"
].nunique() == 1, (
    "Syndicate : les versions PS3 et Xbox 360 doivent être regroupées !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_syndicate_total,
        "Global_Sales"
    ].sum(), 2
) == 0.39, (
    "Syndicate : total des ventes incorrect !"
)

# ============================================================
# 8 SEPTENQUADRAGESIES. SÉPARATION DES VERSIONS DE BOMBERMAN LAND
# ============================================================

# Bomberman Land possède trois productions dans notre dataset :
#
# - PlayStation (2000) : jeu original de Hudson Soft
# - PSP (2007) : Bomberman Land Portable
# - Wii (2007) : adaptation spécifique à la Wii
#
# Décision validée :
# Les trois productions sont considérées comme distinctes.
# Chaque version doit donc posséder son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes et ventes restent inchangées.


# ------------------------------------------------------------
# 1. BOMBERMAN LAND - PLAYSTATION (2000)
# ------------------------------------------------------------

masque_bomberman_land_ps = (
    (df["Rank"] == 8498)
    & (df["Name"] == "Bomberman Land")
    & (df["Platform"] == "PS")
    & (df["Year"] == 2000)
)

assert masque_bomberman_land_ps.sum() == 1, (
    "Bomberman Land : version PlayStation 2000 introuvable !"
)

df.loc[
    masque_bomberman_land_ps,
    "Game_Title_Clean"
] = "Bomberman Land (PS 2000)"


# ------------------------------------------------------------
# 2. BOMBERMAN LAND PORTABLE - PSP (2007)
# ------------------------------------------------------------

masque_bomberman_land_psp = (
    (df["Rank"] == 12331)
    & (df["Name"] == "Bomberman Land")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2007)
)

assert masque_bomberman_land_psp.sum() == 1, (
    "Bomberman Land : version PSP 2007 introuvable !"
)

df.loc[
    masque_bomberman_land_psp,
    "Game_Title_Clean"
] = "Bomberman Land Portable (PSP 2007)"


# ------------------------------------------------------------
# 3. BOMBERMAN LAND - WII (2007)
# ------------------------------------------------------------

masque_bomberman_land_wii = (
    (df["Rank"] == 8372)
    & (df["Name"] == "Bomberman Land")
    & (df["Platform"] == "Wii")
    & (df["Year"] == 2007)
)

assert masque_bomberman_land_wii.sum() == 1, (
    "Bomberman Land : version Wii 2007 introuvable !"
)

df.loc[
    masque_bomberman_land_wii,
    "Game_Title_Clean"
] = "Bomberman Land (Wii 2007)"


# ------------------------------------------------------------
# 4. CONTRÔLE DES TROIS VERSIONS
# ------------------------------------------------------------

masque_bomberman_land_total = (
    masque_bomberman_land_ps
    | masque_bomberman_land_psp
    | masque_bomberman_land_wii
)

# Vérifier que les trois lignes sont présentes
assert masque_bomberman_land_total.sum() == 3, (
    "Bomberman Land : nombre de lignes incorrect !"
)

# Vérifier que les trois titres normalisés sont distincts
assert df.loc[
    masque_bomberman_land_total,
    "Game_Title_Clean"
].nunique() == 3, (
    "Bomberman Land : les trois versions ne sont pas séparées !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_bomberman_land_total,
        "Global_Sales"
    ].sum(), 2
) == 0.39, (
    "Bomberman Land : total des ventes incorrect !"
)

# ============================================================
# 8 OCTOQUADRAGESIES. SÉPARATION DES VERSIONS DE WRC
# ============================================================

# WRC: FIA World Rally Championship regroupe deux jeux :
#
# - PSP (2005) : jeu développé par Traveller's Tales,
#   édité par Sony Computer Entertainment.
#
# - PC / PS3 / Xbox 360 (2010) : jeu développé par Milestone,
#   édité par Black Bean Games.
#
# Décision validée :
# Le jeu PSP possède son propre Game_ID.
# Les versions PC, PS3 et Xbox 360 de 2010 partagent
# un deuxième Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes et ventes restent inchangées.


# ------------------------------------------------------------
# 1. WRC - PSP (2005)
# ------------------------------------------------------------

masque_wrc_psp = (
    (df["Rank"] == 13895)
    & (df["Name"] == "WRC: FIA World Rally Championship")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2005)
)

assert masque_wrc_psp.sum() == 1, (
    "WRC : version PSP 2005 introuvable !"
)

df.loc[
    masque_wrc_psp,
    "Game_Title_Clean"
] = "WRC: FIA World Rally Championship (PSP 2005)"


# ------------------------------------------------------------
# 2. WRC - PC (2010)
# ------------------------------------------------------------

masque_wrc_pc = (
    (df["Rank"] == 16061)
    & (df["Name"] == "WRC: FIA World Rally Championship")
    & (df["Platform"] == "PC")
    & (df["Year"] == 2010)
)

assert masque_wrc_pc.sum() == 1, (
    "WRC : version PC 2010 introuvable !"
)

df.loc[
    masque_wrc_pc,
    "Game_Title_Clean"
] = "WRC: FIA World Rally Championship (2010)"


# ------------------------------------------------------------
# 3. WRC - PS3 (2010)
# ------------------------------------------------------------

masque_wrc_ps3 = (
    (df["Rank"] == 7425)
    & (df["Name"] == "WRC: FIA World Rally Championship")
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2010)
)

assert masque_wrc_ps3.sum() == 1, (
    "WRC : version PS3 2010 introuvable !"
)

df.loc[
    masque_wrc_ps3,
    "Game_Title_Clean"
] = "WRC: FIA World Rally Championship (2010)"


# ------------------------------------------------------------
# 4. WRC - XBOX 360 (2010)
# ------------------------------------------------------------

masque_wrc_x360 = (
    (df["Rank"] == 9694)
    & (df["Name"] == "WRC: FIA World Rally Championship")
    & (df["Platform"] == "X360")
    & (df["Year"] == 2010)
)

assert masque_wrc_x360.sum() == 1, (
    "WRC : version Xbox 360 2010 introuvable !"
)

df.loc[
    masque_wrc_x360,
    "Game_Title_Clean"
] = "WRC: FIA World Rally Championship (2010)"


# ------------------------------------------------------------
# 5. CONTRÔLE DES QUATRE LIGNES
# ------------------------------------------------------------

masque_wrc_total = (
    masque_wrc_psp
    | masque_wrc_pc
    | masque_wrc_ps3
    | masque_wrc_x360
)

# Vérifier que les quatre lignes sont présentes
assert masque_wrc_total.sum() == 4, (
    "WRC : nombre de lignes incorrect !"
)

# Vérifier qu'il existe exactement deux titres distincts
assert df.loc[
    masque_wrc_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "WRC : les deux jeux ne sont pas séparés correctement !"
)

# Vérifier que les versions de 2010 sont regroupées
assert df.loc[
    masque_wrc_pc | masque_wrc_ps3 | masque_wrc_x360,
    "Game_Title_Clean"
].nunique() == 1, (
    "WRC : les versions de 2010 doivent être regroupées !"
)

# Vérifier que la PSP est séparée des versions de 2010
assert (
    df.loc[masque_wrc_psp, "Game_Title_Clean"].iloc[0]
    != df.loc[masque_wrc_pc, "Game_Title_Clean"].iloc[0]
), (
    "WRC : la version PSP doit être séparée !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_wrc_total,
        "Global_Sales"
    ].sum(), 2
) == 0.38, (
    "WRC : total des ventes incorrect !"
)
# ============================================================
# 8 NOVEMQUADRAGESIES. SÉPARATION DES VERSIONS DE ETRIAN ODYSSEY II
# ============================================================

# Etrian Odyssey II regroupe deux productions différentes :
#
# - Nintendo DS (2008) :
#   Etrian Odyssey II: Heroes of Lagaard, jeu original.
#
# - Nintendo 3DS (2014) :
#   Etrian Odyssey 2 Untold: The Fafnir Knight, remake.
#
# Décision validée :
# Le jeu original et son remake doivent posséder
# deux Game_ID distincts.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes et ventes restent inchangées.


# ------------------------------------------------------------
# 1. ETRIAN ODYSSEY II - NINTENDO DS (2008)
# ------------------------------------------------------------

masque_etrian_ii_ds = (
    (df["Rank"] == 6363)
    & (df["Name"] == "Etrian Odyssey II: Heroes of Lagaard")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2008)
)

assert masque_etrian_ii_ds.sum() == 1, (
    "Etrian Odyssey II : version DS 2008 introuvable !"
)

df.loc[
    masque_etrian_ii_ds,
    "Game_Title_Clean"
] = "Etrian Odyssey II: Heroes of Lagaard (DS 2008)"


# ------------------------------------------------------------
# 2. ETRIAN ODYSSEY 2 UNTOLD - NINTENDO 3DS (2014)
# ------------------------------------------------------------

masque_etrian_ii_3ds = (
    (df["Rank"] == 10483)
    & (df["Name"] == "Etrian Odyssey II: Heroes of Lagaard")
    & (df["Platform"] == "3DS")
    & (df["Year"] == 2014)
)

assert masque_etrian_ii_3ds.sum() == 1, (
    "Etrian Odyssey II : version 3DS 2014 introuvable !"
)

df.loc[
    masque_etrian_ii_3ds,
    "Game_Title_Clean"
] = "Etrian Odyssey 2 Untold: The Fafnir Knight (3DS 2014)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_etrian_ii_total = (
    masque_etrian_ii_ds
    | masque_etrian_ii_3ds
)

# Vérifier que les deux lignes sont présentes
assert masque_etrian_ii_total.sum() == 2, (
    "Etrian Odyssey II : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_etrian_ii_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Etrian Odyssey II : original et remake non séparés !"
)

# Vérifier que les années restent correctes
assert df.loc[
    masque_etrian_ii_ds,
    "Year"
].iloc[0] == 2008, (
    "Etrian Odyssey II : année DS incorrecte !"
)

assert df.loc[
    masque_etrian_ii_3ds,
    "Year"
].iloc[0] == 2014, (
    "Etrian Odyssey II : année 3DS incorrecte !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_etrian_ii_total,
        "Global_Sales"
    ].sum(), 2
) == 0.37, (
    "Etrian Odyssey II : total des ventes incorrect !"
)

# ============================================================
# 8 QUINQUAGÉSIES. SÉPARATION DES VERSIONS DE SUMMON NIGHT 3
# ============================================================

# Summon Night 3 possède deux versions distinctes :
#
# - PS2 (2003) : jeu original développé par Flight-Plan.
#
# - PSP (2012) : réédition améliorée développée par
#   Felistella, avec de nouvelles fonctionnalités.
#
# Décision validée :
# Chaque version possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes et ventes restent inchangées.


# ------------------------------------------------------------
# 1. SUMMON NIGHT 3 - PLAYSTATION 2 (2003)
# ------------------------------------------------------------

masque_summon_night_3_ps2 = (
    (df["Rank"] == 6843)
    & (df["Name"] == "Summon Night 3")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2003)
)

assert masque_summon_night_3_ps2.sum() == 1, (
    "Summon Night 3 : version PS2 2003 introuvable !"
)

df.loc[
    masque_summon_night_3_ps2,
    "Game_Title_Clean"
] = "Summon Night 3 (PS2 2003)"


# ------------------------------------------------------------
# 2. SUMMON NIGHT 3 - PSP (2012)
# ------------------------------------------------------------

masque_summon_night_3_psp = (
    (df["Rank"] == 9739)
    & (df["Name"] == "Summon Night 3")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2012)
)

assert masque_summon_night_3_psp.sum() == 1, (
    "Summon Night 3 : version PSP 2012 introuvable !"
)

df.loc[
    masque_summon_night_3_psp,
    "Game_Title_Clean"
] = "Summon Night 3 (PSP Enhanced 2012)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_summon_night_3_total = (
    masque_summon_night_3_ps2
    | masque_summon_night_3_psp
)

# Vérifier que les deux lignes sont présentes
assert masque_summon_night_3_total.sum() == 2, (
    "Summon Night 3 : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_summon_night_3_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Summon Night 3 : les deux versions ne sont pas séparées !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_summon_night_3_ps2,
    "Year"
].iloc[0] == 2003, (
    "Summon Night 3 : année PS2 incorrecte !"
)

assert df.loc[
    masque_summon_night_3_psp,
    "Year"
].iloc[0] == 2012, (
    "Summon Night 3 : année PSP incorrecte !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_summon_night_3_total,
        "Global_Sales"
    ].sum(), 2
) == 0.36, (
    "Summon Night 3 : total des ventes incorrect !"
)

# ============================================================
# 8 UNQUINQUAGÉSIES. SÉPARATION DES VERSIONS DE PRO YAKYUU TEAM
# ============================================================

# Pro Yakyuu Team o Tsukurou! 2 regroupe deux jeux distincts :
#
# - PS2 (2003) : deuxième épisode de la série sur PS2.
#
# - Nintendo DS (2009) : suite de l'épisode DS de 2008.
#
# Décision validée :
# Chaque jeu doit posséder son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes et ventes restent inchangées.


# ------------------------------------------------------------
# 1. PRO YAKYUU TEAM O TSUKUROU! 2 - PS2 (2003)
# ------------------------------------------------------------

masque_pro_yakyuu_2_ps2 = (
    (df["Rank"] == 7068)
    & (df["Name"] == "Pro Yakyuu Team o Tsukurou! 2")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2003)
)

assert masque_pro_yakyuu_2_ps2.sum() == 1, (
    "Pro Yakyuu Team 2 : version PS2 2003 introuvable !"
)

df.loc[
    masque_pro_yakyuu_2_ps2,
    "Game_Title_Clean"
] = "Pro Yakyuu Team o Tsukurou! 2 (PS2 2003)"


# ------------------------------------------------------------
# 2. PRO YAKYUU TEAM O TSUKUROU! 2 - DS (2009)
# ------------------------------------------------------------

masque_pro_yakyuu_2_ds = (
    (df["Rank"] == 10373)
    & (df["Name"] == "Pro Yakyuu Team o Tsukurou! 2")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2009)
)

assert masque_pro_yakyuu_2_ds.sum() == 1, (
    "Pro Yakyuu Team 2 : version DS 2009 introuvable !"
)

df.loc[
    masque_pro_yakyuu_2_ds,
    "Game_Title_Clean"
] = "Pro Yakyuu Team o Tsukurou! 2 (DS 2009)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_pro_yakyuu_2_total = (
    masque_pro_yakyuu_2_ps2
    | masque_pro_yakyuu_2_ds
)

# Vérifier que les deux lignes sont présentes
assert masque_pro_yakyuu_2_total.sum() == 2, (
    "Pro Yakyuu Team 2 : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_pro_yakyuu_2_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Pro Yakyuu Team 2 : les deux jeux ne sont pas séparés !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_pro_yakyuu_2_ps2,
    "Year"
].iloc[0] == 2003, (
    "Pro Yakyuu Team 2 : année PS2 incorrecte !"
)

assert df.loc[
    masque_pro_yakyuu_2_ds,
    "Year"
].iloc[0] == 2009, (
    "Pro Yakyuu Team 2 : année DS incorrecte !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_pro_yakyuu_2_total,
        "Global_Sales"
    ].sum(), 2
) == 0.34, (
    "Pro Yakyuu Team 2 : total des ventes incorrect !"
)

# ============================================================
# 8 DUOQUINQUAGÉSIES. SÉPARATION DES VERSIONS DE ARCANIA
# ============================================================

# Arcania: Gothic 4 possède deux éditions distinctes :
#
# - PC / Xbox 360 (2010) : jeu original.
#
# - PS4 (2015) : Arcania: The Complete Tale,
#   édition complète incluant l'extension Fall of Setarrif.
#
# Décision validée :
# Les versions PC et Xbox 360 partagent le même Game_ID.
# L'édition complète PS4 possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes et ventes restent inchangées.


# ------------------------------------------------------------
# 1. ARCANIA: GOTHIC 4 - PC (2010)
# ------------------------------------------------------------

masque_arcania_pc = (
    (df["Rank"] == 7923)
    & (df["Name"] == "Arcania: Gothic 4")
    & (df["Platform"] == "PC")
    & (df["Year"] == 2010)
)

assert masque_arcania_pc.sum() == 1, (
    "Arcania : version PC 2010 introuvable !"
)

df.loc[
    masque_arcania_pc,
    "Game_Title_Clean"
] = "Arcania: Gothic 4 (2010)"


# ------------------------------------------------------------
# 2. ARCANIA: GOTHIC 4 - XBOX 360 (2010)
# ------------------------------------------------------------

masque_arcania_x360 = (
    (df["Rank"] == 10711)
    & (df["Name"] == "Arcania: Gothic 4")
    & (df["Platform"] == "X360")
    & (df["Year"] == 2010)
)

assert masque_arcania_x360.sum() == 1, (
    "Arcania : version Xbox 360 2010 introuvable !"
)

df.loc[
    masque_arcania_x360,
    "Game_Title_Clean"
] = "Arcania: Gothic 4 (2010)"


# ------------------------------------------------------------
# 3. ARCANIA: THE COMPLETE TALE - PS4 (2015)
# ------------------------------------------------------------

masque_arcania_ps4 = (
    (df["Rank"] == 12950)
    & (df["Name"] == "Arcania: Gothic 4")
    & (df["Platform"] == "PS4")
    & (df["Year"] == 2015)
)

assert masque_arcania_ps4.sum() == 1, (
    "Arcania : version PS4 2015 introuvable !"
)

df.loc[
    masque_arcania_ps4,
    "Game_Title_Clean"
] = "Arcania: The Complete Tale (2015)"


# ------------------------------------------------------------
# 4. CONTRÔLE DES TROIS LIGNES
# ------------------------------------------------------------

masque_arcania_total = (
    masque_arcania_pc
    | masque_arcania_x360
    | masque_arcania_ps4
)

# Vérifier que les trois lignes sont présentes
assert masque_arcania_total.sum() == 3, (
    "Arcania : nombre de lignes incorrect !"
)

# Vérifier qu'il existe exactement deux titres distincts
assert df.loc[
    masque_arcania_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Arcania : les deux éditions ne sont pas séparées !"
)

# Vérifier que les versions PC et Xbox 360 sont regroupées
assert df.loc[
    masque_arcania_pc | masque_arcania_x360,
    "Game_Title_Clean"
].nunique() == 1, (
    "Arcania : les versions de 2010 doivent être regroupées !"
)

# Vérifier que l'édition complète PS4 est séparée
assert (
    df.loc[masque_arcania_ps4, "Game_Title_Clean"].iloc[0]
    != df.loc[masque_arcania_pc, "Game_Title_Clean"].iloc[0]
), (
    "Arcania : l'édition complète doit être séparée !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_arcania_total,
        "Global_Sales"
    ].sum(), 2
) == 0.34, (
    "Arcania : total des ventes incorrect !"
)

# ============================================================
# 8 TRIQUINQUAGÉSIES. SÉPARATION DES VERSIONS DE TRAILS IN THE SKY
# ============================================================

# The Legend of Heroes: Trails in the Sky First Chapter
# possède trois éditions distinctes :
#
# - PSP (2006) : portage du jeu original.
#
# - PS3 (2012) : FC Kai HD Edition, remaster HD.
#
# - PS Vita (2015) : FC Evolution, réédition enrichie
#   avec doublages, musiques réarrangées et améliorations.
#
# Décision validée :
# Chaque édition possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes et ventes restent inchangées.


# ------------------------------------------------------------
# 1. TRAILS IN THE SKY FIRST CHAPTER - PSP (2006)
# ------------------------------------------------------------

masque_trails_sky_psp = (
    (df["Rank"] == 7318)
    & (df["Name"] == "The Legend of Heroes: Trails in the Sky First Chapter")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2006)
)

assert masque_trails_sky_psp.sum() == 1, (
    "Trails in the Sky : version PSP 2006 introuvable !"
)

df.loc[
    masque_trails_sky_psp,
    "Game_Title_Clean"
] = "The Legend of Heroes: Trails in the Sky First Chapter"


# ------------------------------------------------------------
# 2. TRAILS IN THE SKY FC KAI HD EDITION - PS3 (2012)
# ------------------------------------------------------------

masque_trails_sky_ps3 = (
    (df["Rank"] == 13777)
    & (df["Name"] == "The Legend of Heroes: Trails in the Sky First Chapter")
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2012)
)

assert masque_trails_sky_ps3.sum() == 1, (
    "Trails in the Sky : version PS3 2012 introuvable !"
)

df.loc[
    masque_trails_sky_ps3,
    "Game_Title_Clean"
] = "The Legend of Heroes: Trails in the Sky FC Kai HD Edition (2012)"


# ------------------------------------------------------------
# 3. TRAILS IN THE SKY FC EVOLUTION - PS VITA (2015)
# ------------------------------------------------------------

masque_trails_sky_psv = (
    (df["Rank"] == 12022)
    & (df["Name"] == "The Legend of Heroes: Trails in the Sky First Chapter")
    & (df["Platform"] == "PSV")
    & (df["Year"] == 2015)
)

assert masque_trails_sky_psv.sum() == 1, (
    "Trails in the Sky : version PS Vita 2015 introuvable !"
)

df.loc[
    masque_trails_sky_psv,
    "Game_Title_Clean"
] = "The Legend of Heroes: Trails in the Sky FC Evolution (2015)"


# ------------------------------------------------------------
# 4. CONTRÔLE DES TROIS VERSIONS
# ------------------------------------------------------------

masque_trails_sky_total = (
    masque_trails_sky_psp
    | masque_trails_sky_ps3
    | masque_trails_sky_psv
)

# Vérifier que les trois lignes sont présentes
assert masque_trails_sky_total.sum() == 3, (
    "Trails in the Sky : nombre de lignes incorrect !"
)

# Vérifier que les trois titres normalisés sont distincts
assert df.loc[
    masque_trails_sky_total,
    "Game_Title_Clean"
].nunique() == 3, (
    "Trails in the Sky : les trois éditions ne sont pas séparées !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_trails_sky_psp,
    "Year"
].iloc[0] == 2006, (
    "Trails in the Sky : année PSP incorrecte !"
)

assert df.loc[
    masque_trails_sky_ps3,
    "Year"
].iloc[0] == 2012, (
    "Trails in the Sky : année PS3 incorrecte !"
)

assert df.loc[
    masque_trails_sky_psv,
    "Year"
].iloc[0] == 2015, (
    "Trails in the Sky : année PS Vita incorrecte !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_trails_sky_total,
        "Global_Sales"
    ].sum(), 2
) == 0.32, (
    "Trails in the Sky : total des ventes incorrect !"
)

# ============================================================
# 8 QUATTUORQUINQUAGÉSIES. SÉPARATION DES VERSIONS D'AMAGAMI
# ============================================================

# Amagami possède trois éditions distinctes :
#
# - PS2 (2009) : jeu original.
#
# - PSP (2011) : Amagami EbiKore+,
#   réédition enrichie avec du contenu supplémentaire.
#
# - PS Vita (2014) : Amagami EbiKore+,
#   version améliorée avec une nouvelle galerie d'illustrations,
#   des améliorations graphiques et sonores.
#
# Décision validée :
# Chaque édition possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes et ventes restent inchangées.


# ------------------------------------------------------------
# 1. AMAGAMI - PS2 (2009)
# ------------------------------------------------------------

masque_amagami_ps2 = (
    (df["Rank"] == 9448)
    & (df["Name"] == "Amagami")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2009)
)

assert masque_amagami_ps2.sum() == 1, (
    "Amagami : version PS2 2009 introuvable !"
)

df.loc[
    masque_amagami_ps2,
    "Game_Title_Clean"
] = "Amagami (Original 2009)"


# ------------------------------------------------------------
# 2. AMAGAMI EBIKORE+ - PSP (2011)
# ------------------------------------------------------------

masque_amagami_psp = (
    (df["Rank"] == 8785)
    & (df["Name"] == "Amagami")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2011)
)

assert masque_amagami_psp.sum() == 1, (
    "Amagami : version PSP 2011 introuvable !"
)

df.loc[
    masque_amagami_psp,
    "Game_Title_Clean"
] = "Amagami EbiKore+ (2011)"


# ------------------------------------------------------------
# 3. AMAGAMI EBIKORE+ - PS VITA (2014)
# ------------------------------------------------------------

masque_amagami_psv = (
    (df["Rank"] == 13626)
    & (df["Name"] == "Amagami")
    & (df["Platform"] == "PSV")
    & (df["Year"] == 2014)
)

assert masque_amagami_psv.sum() == 1, (
    "Amagami : version PS Vita 2014 introuvable !"
)

df.loc[
    masque_amagami_psv,
    "Game_Title_Clean"
] = "Amagami EbiKore+ (PS Vita 2014)"


# ------------------------------------------------------------
# 4. CONTRÔLE DES TROIS VERSIONS
# ------------------------------------------------------------

masque_amagami_total = (
    masque_amagami_ps2
    | masque_amagami_psp
    | masque_amagami_psv
)

# Vérifier que les trois lignes sont présentes
assert masque_amagami_total.sum() == 3, (
    "Amagami : nombre de lignes incorrect !"
)

# Vérifier que les trois titres normalisés sont distincts
assert df.loc[
    masque_amagami_total,
    "Game_Title_Clean"
].nunique() == 3, (
    "Amagami : les trois éditions ne sont pas séparées !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_amagami_ps2,
    "Year"
].iloc[0] == 2009, (
    "Amagami : année PS2 incorrecte !"
)

assert df.loc[
    masque_amagami_psp,
    "Year"
].iloc[0] == 2011, (
    "Amagami : année PSP incorrecte !"
)

assert df.loc[
    masque_amagami_psv,
    "Year"
].iloc[0] == 2014, (
    "Amagami : année PS Vita incorrecte !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_amagami_total,
        "Global_Sales"
    ].sum(), 2
) == 0.32, (
    "Amagami : total des ventes incorrect !"
)

# ============================================================
# 8 QUINQUINQUAGÉSIES. SÉPARATION DES VERSIONS DE SHADOW OF DESTINY
# ============================================================

# Shadow of Destiny possède deux éditions distinctes :
#
# - PS2 (2001) : jeu original.
#
# - PSP (2009) : portage amélioré avec de nouveaux
#   doublages et des modifications de contenu.
#
# Décision validée :
# Chaque édition possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes et ventes restent inchangées.


# ------------------------------------------------------------
# 1. SHADOW OF DESTINY - PS2 (2001)
# ------------------------------------------------------------

masque_shadow_destiny_ps2 = (
    (df["Rank"] == 7407)
    & (df["Name"] == "Shadow of Destiny")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2001)
)

assert masque_shadow_destiny_ps2.sum() == 1, (
    "Shadow of Destiny : version PS2 2001 introuvable !"
)

df.loc[
    masque_shadow_destiny_ps2,
    "Game_Title_Clean"
] = "Shadow of Destiny (Original 2001)"


# ------------------------------------------------------------
# 2. SHADOW OF DESTINY - PSP (2009)
# ------------------------------------------------------------

masque_shadow_destiny_psp = (
    (df["Rank"] == 11252)
    & (df["Name"] == "Shadow of Destiny")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2009)
)

assert masque_shadow_destiny_psp.sum() == 1, (
    "Shadow of Destiny : version PSP 2009 introuvable !"
)

df.loc[
    masque_shadow_destiny_psp,
    "Game_Title_Clean"
] = "Shadow of Destiny (PSP Enhanced 2009)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_shadow_destiny_total = (
    masque_shadow_destiny_ps2
    | masque_shadow_destiny_psp
)

# Vérifier que les deux lignes sont présentes
assert masque_shadow_destiny_total.sum() == 2, (
    "Shadow of Destiny : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_shadow_destiny_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Shadow of Destiny : les deux éditions ne sont pas séparées !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_shadow_destiny_ps2,
    "Year"
].iloc[0] == 2001, (
    "Shadow of Destiny : année PS2 incorrecte !"
)

assert df.loc[
    masque_shadow_destiny_psp,
    "Year"
].iloc[0] == 2009, (
    "Shadow of Destiny : année PSP incorrecte !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_shadow_destiny_total,
        "Global_Sales"
    ].sum(), 2
) == 0.30, (
    "Shadow of Destiny : total des ventes incorrect !"
)

# ============================================================
# 8 SEXQUINQUAGÉSIES. SÉPARATION DES VERSIONS DE ROMANCE OF THE THREE KINGDOMS II
# ============================================================

# Romance of the Three Kingdoms II regroupe deux jeux distincts :
#
# - SNES (1991) : portage du deuxième épisode de la série.
#
# - Nintendo 3DS (2015) : Sangokushi 2,
#   remake enrichi du troisième épisode de la série.
#
# Décision validée :
# Chaque jeu possède son propre Game_ID.
# Le titre normalisé de la version 3DS est corrigé.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les noms d'origine, années, plateformes et ventes
# restent inchangés.


# ------------------------------------------------------------
# 1. ROMANCE OF THE THREE KINGDOMS II - SNES (1991)
# ------------------------------------------------------------

masque_romance_2_snes = (
    (df["Rank"] == 6625)
    & (df["Name"] == "Romance of the Three Kingdoms II")
    & (df["Platform"] == "SNES")
    & (df["Year"] == 1991)
)

assert masque_romance_2_snes.sum() == 1, (
    "Romance of the Three Kingdoms II : version SNES introuvable !"
)

df.loc[
    masque_romance_2_snes,
    "Game_Title_Clean"
] = "Romance of the Three Kingdoms II"


# ------------------------------------------------------------
# 2. ROMANCE OF THE THREE KINGDOMS III - 3DS REMAKE (2015)
# ------------------------------------------------------------

masque_romance_3_3ds = (
    (df["Rank"] == 14628)
    & (df["Name"] == "Romance of the Three Kingdoms II")
    & (df["Platform"] == "3DS")
    & (df["Year"] == 2015)
)

assert masque_romance_3_3ds.sum() == 1, (
    "Romance of the Three Kingdoms : version 3DS introuvable !"
)

df.loc[
    masque_romance_3_3ds,
    "Game_Title_Clean"
] = "Romance of the Three Kingdoms III (3DS Remake 2015)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_romance_total = (
    masque_romance_2_snes
    | masque_romance_3_3ds
)

# Vérifier que les deux lignes sont présentes
assert masque_romance_total.sum() == 2, (
    "Romance of the Three Kingdoms : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_romance_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Romance of the Three Kingdoms : les deux jeux ne sont pas séparés !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_romance_2_snes,
    "Year"
].iloc[0] == 1991, (
    "Romance of the Three Kingdoms : année SNES incorrecte !"
)

assert df.loc[
    masque_romance_3_3ds,
    "Year"
].iloc[0] == 2015, (
    "Romance of the Three Kingdoms : année 3DS incorrecte !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_romance_total,
        "Global_Sales"
    ].sum(), 2
) == 0.28, (
    "Romance of the Three Kingdoms : total des ventes incorrect !"
)

# ============================================================
# 8 SEPTENQUINQUAGÉSIES. SÉPARATION DES VERSIONS DE WORLD SERIES BASEBALL
# ============================================================

# World Series Baseball regroupe deux jeux distincts :
#
# - Sega Saturn (1995) : épisode développé par Sega.
#
# - Xbox (2002) : nouvel épisode développé par
#   Visual Concepts et Blue Shift.
#
# Décision validée :
# Chaque jeu possède son propre Game_ID.
#
# L'année Saturn est corrigée dans le fichier de suivi
# et appliquée en section 3 BIS.
#
# Seule la colonne Game_Title_Clean est modifiée ici.


# ------------------------------------------------------------
# 1. WORLD SERIES BASEBALL - SATURN (1995)
# ------------------------------------------------------------

masque_world_series_sat = (
    (df["Rank"] == 13718)
    & (df["Name"] == "World Series Baseball")
    & (df["Platform"] == "SAT")
    & (df["Year"] == 1995)
)

assert masque_world_series_sat.sum() == 1, (
    "World Series Baseball : version Saturn 1995 introuvable !"
)

df.loc[
    masque_world_series_sat,
    "Game_Title_Clean"
] = "World Series Baseball (SAT 1995)"


# ------------------------------------------------------------
# 2. WORLD SERIES BASEBALL - XBOX (2002)
# ------------------------------------------------------------

masque_world_series_xb = (
    (df["Rank"] == 6992)
    & (df["Name"] == "World Series Baseball")
    & (df["Platform"] == "XB")
    & (df["Year"] == 2002)
)

assert masque_world_series_xb.sum() == 1, (
    "World Series Baseball : version Xbox 2002 introuvable !"
)

df.loc[
    masque_world_series_xb,
    "Game_Title_Clean"
] = "World Series Baseball (Xbox 2002)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_world_series_total = (
    masque_world_series_sat
    | masque_world_series_xb
)

# Vérifier que les deux lignes sont présentes
assert masque_world_series_total.sum() == 2, (
    "World Series Baseball : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_world_series_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "World Series Baseball : les deux jeux ne sont pas séparés !"
)

# Vérifier que l'année Saturn est corrigée
assert df.loc[
    masque_world_series_sat,
    "Year"
].iloc[0] == 1995, (
    "World Series Baseball : année Saturn incorrecte !"
)

# Vérifier que l'année Xbox est conservée
assert df.loc[
    masque_world_series_xb,
    "Year"
].iloc[0] == 2002, (
    "World Series Baseball : année Xbox incorrecte !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_world_series_total,
        "Global_Sales"
    ].sum(), 2
) == 0.27, (
    "World Series Baseball : total des ventes incorrect !"
)

# ============================================================
# 8 OCTOQUINQUAGÉSIES. SÉPARATION DES VERSIONS DE SYBERIA
# ============================================================

# Syberia possède deux versions distinctes :
#
# - PC (2002) / Xbox (2003) : version originale.
#
# - Nintendo DS (2008) : adaptation simplifiée,
#   avec suppression de dialogues et modification
#   de certaines énigmes.
#
# Décision validée :
# Les versions PC et Xbox partagent le même Game_ID.
# La version Nintendo DS possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes et ventes restent inchangées.


# ------------------------------------------------------------
# 1. SYBERIA - PC (2002)
# ------------------------------------------------------------

masque_syberia_pc = (
    (df["Rank"] == 14581)
    & (df["Name"] == "Syberia")
    & (df["Platform"] == "PC")
    & (df["Year"] == 2002)
)

assert masque_syberia_pc.sum() == 1, (
    "Syberia : version PC 2002 introuvable !"
)

df.loc[
    masque_syberia_pc,
    "Game_Title_Clean"
] = "Syberia (Original 2002)"


# ------------------------------------------------------------
# 2. SYBERIA - XBOX (2003)
# ------------------------------------------------------------

masque_syberia_xb = (
    (df["Rank"] == 10493)
    & (df["Name"] == "Syberia")
    & (df["Platform"] == "XB")
    & (df["Year"] == 2003)
)

assert masque_syberia_xb.sum() == 1, (
    "Syberia : version Xbox 2003 introuvable !"
)

df.loc[
    masque_syberia_xb,
    "Game_Title_Clean"
] = "Syberia (Original 2002)"


# ------------------------------------------------------------
# 3. SYBERIA - NINTENDO DS (2008)
# ------------------------------------------------------------

masque_syberia_ds = (
    (df["Rank"] == 9195)
    & (df["Name"] == "Syberia")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2008)
)

assert masque_syberia_ds.sum() == 1, (
    "Syberia : version DS 2008 introuvable !"
)

df.loc[
    masque_syberia_ds,
    "Game_Title_Clean"
] = "Syberia (DS 2008)"


# ------------------------------------------------------------
# 4. CONTRÔLE DES TROIS LIGNES
# ------------------------------------------------------------

masque_syberia_total = (
    masque_syberia_pc
    | masque_syberia_xb
    | masque_syberia_ds
)

# Vérifier que les trois lignes sont présentes
assert masque_syberia_total.sum() == 3, (
    "Syberia : nombre de lignes incorrect !"
)

# Vérifier qu'il existe exactement deux titres distincts
assert df.loc[
    masque_syberia_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Syberia : les deux versions ne sont pas séparées !"
)

# Vérifier que les versions PC et Xbox sont regroupées
assert df.loc[
    masque_syberia_pc | masque_syberia_xb,
    "Game_Title_Clean"
].nunique() == 1, (
    "Syberia : les versions PC et Xbox doivent être regroupées !"
)

# Vérifier que la version DS est séparée
assert (
    df.loc[masque_syberia_ds, "Game_Title_Clean"].iloc[0]
    != df.loc[masque_syberia_pc, "Game_Title_Clean"].iloc[0]
), (
    "Syberia : la version DS doit être séparée !"
)

# Vérifier que les années sont conservées
assert df.loc[masque_syberia_pc, "Year"].iloc[0] == 2002
assert df.loc[masque_syberia_xb, "Year"].iloc[0] == 2003
assert df.loc[masque_syberia_ds, "Year"].iloc[0] == 2008

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_syberia_total,
        "Global_Sales"
    ].sum(), 2
) == 0.27, (
    "Syberia : total des ventes incorrect !"
)

# ============================================================
# 8 NOVEMQUINQUAGÉSIES. SÉPARATION DES VERSIONS DE SUMMON NIGHT 4
# ============================================================

# Summon Night 4 possède deux éditions distinctes :
#
# - PS2 (2006) : jeu original développé par Flight-Plan.
#
# - PSP (2012) : réédition améliorée développée par
#   Felistella, avec de nouveaux personnages,
#   des améliorations du système de combat
#   et du contenu supplémentaire.
#
# Décision validée :
# Chaque édition possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes et ventes restent inchangées.


# ------------------------------------------------------------
# 1. SUMMON NIGHT 4 - PS2 (2006)
# ------------------------------------------------------------

masque_summon_night_4_ps2 = (
    (df["Rank"] == 8197)
    & (df["Name"] == "Summon Night 4")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2006)
)

assert masque_summon_night_4_ps2.sum() == 1, (
    "Summon Night 4 : version PS2 2006 introuvable !"
)

df.loc[
    masque_summon_night_4_ps2,
    "Game_Title_Clean"
] = "Summon Night 4 (PS2 2006)"


# ------------------------------------------------------------
# 2. SUMMON NIGHT 4 - PSP (2012)
# ------------------------------------------------------------

masque_summon_night_4_psp = (
    (df["Rank"] == 11788)
    & (df["Name"] == "Summon Night 4")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2012)
)

assert masque_summon_night_4_psp.sum() == 1, (
    "Summon Night 4 : version PSP 2012 introuvable !"
)

df.loc[
    masque_summon_night_4_psp,
    "Game_Title_Clean"
] = "Summon Night 4 (PSP Enhanced 2012)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_summon_night_4_total = (
    masque_summon_night_4_ps2
    | masque_summon_night_4_psp
)

# Vérifier que les deux lignes sont présentes
assert masque_summon_night_4_total.sum() == 2, (
    "Summon Night 4 : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_summon_night_4_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Summon Night 4 : les deux éditions ne sont pas séparées !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_summon_night_4_ps2,
    "Year"
].iloc[0] == 2006, (
    "Summon Night 4 : année PS2 incorrecte !"
)

assert df.loc[
    masque_summon_night_4_psp,
    "Year"
].iloc[0] == 2012, (
    "Summon Night 4 : année PSP incorrecte !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_summon_night_4_total,
        "Global_Sales"
    ].sum(), 2
) == 0.25, (
    "Summon Night 4 : total des ventes incorrect !"
)

# ============================================================
# 8 SEXAGÉSIES. SÉPARATION DES VERSIONS DE FATE/STAY NIGHT
# ============================================================

# Fate/Stay Night [Réalta Nua] possède deux éditions distinctes :
#
# - PS2 (2007) : première édition Réalta Nua.
#
# - PS Vita (2012) : réédition améliorée avec
#   de nouvelles cinématiques, des graphismes HD
#   et des musiques retravaillées.
#
# Décision validée :
# Chaque édition possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes et ventes restent inchangées.


# ------------------------------------------------------------
# 1. FATE/STAY NIGHT [RÉALTA NUA] - PS2 (2007)
# ------------------------------------------------------------

masque_fate_stay_night_ps2 = (
    (df["Rank"] == 8350)
    & (df["Name"] == "Fate/Stay Night [Réalta Nua]")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2007)
)

assert masque_fate_stay_night_ps2.sum() == 1, (
    "Fate/Stay Night : version PS2 2007 introuvable !"
)

df.loc[
    masque_fate_stay_night_ps2,
    "Game_Title_Clean"
] = "Fate/Stay Night [Réalta Nua] (2007)"


# ------------------------------------------------------------
# 2. FATE/STAY NIGHT [RÉALTA NUA] - PS VITA (2012)
# ------------------------------------------------------------

masque_fate_stay_night_psv = (
    (df["Rank"] == 12756)
    & (df["Name"] == "Fate/Stay Night [Réalta Nua]")
    & (df["Platform"] == "PSV")
    & (df["Year"] == 2012)
)

assert masque_fate_stay_night_psv.sum() == 1, (
    "Fate/Stay Night : version PS Vita 2012 introuvable !"
)

df.loc[
    masque_fate_stay_night_psv,
    "Game_Title_Clean"
] = "Fate/Stay Night [Réalta Nua] (PS Vita 2012)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_fate_stay_night_total = (
    masque_fate_stay_night_ps2
    | masque_fate_stay_night_psv
)

# Vérifier que les deux lignes sont présentes
assert masque_fate_stay_night_total.sum() == 2, (
    "Fate/Stay Night : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_fate_stay_night_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Fate/Stay Night : les deux éditions ne sont pas séparées !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_fate_stay_night_ps2,
    "Year"
].iloc[0] == 2007, (
    "Fate/Stay Night : année PS2 incorrecte !"
)

assert df.loc[
    masque_fate_stay_night_psv,
    "Year"
].iloc[0] == 2012, (
    "Fate/Stay Night : année PS Vita incorrecte !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_fate_stay_night_total,
        "Global_Sales"
    ].sum(), 2
) == 0.23, (
    "Fate/Stay Night : total des ventes incorrect !"
)

# ============================================================
# 8 UNSEXAGÉSIES. SÉPARATION DES JEUX MOON
# ============================================================

# Deux jeux différents portent le même nom :
#
# - PS (1997) : Moon: Remix RPG Adventure,
#   développé par Love-de-Lic.
#
# - DS (2009) : Moon, jeu de tir à la première personne
#   développé par Renegade Kid.
#
# Décision validée :
# Chaque jeu possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes, genres et ventes restent inchangés.


# ------------------------------------------------------------
# 1. MOON: REMIX RPG ADVENTURE - PS (1997)
# ------------------------------------------------------------

masque_moon_ps = (
    (df["Rank"] == 8095)
    & (df["Name"] == "Moon")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1997)
)

assert masque_moon_ps.sum() == 1, (
    "Moon : version PS 1997 introuvable !"
)

df.loc[
    masque_moon_ps,
    "Game_Title_Clean"
] = "Moon: Remix RPG Adventure (1997)"


# ------------------------------------------------------------
# 2. MOON - NINTENDO DS (2009)
# ------------------------------------------------------------

masque_moon_ds = (
    (df["Rank"] == 13295)
    & (df["Name"] == "Moon")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2009)
)

assert masque_moon_ds.sum() == 1, (
    "Moon : version DS 2009 introuvable !"
)

df.loc[
    masque_moon_ds,
    "Game_Title_Clean"
] = "Moon (DS 2009)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX JEUX
# ------------------------------------------------------------

masque_moon_total = (
    masque_moon_ps
    | masque_moon_ds
)

# Vérifier que les deux lignes sont présentes
assert masque_moon_total.sum() == 2, (
    "Moon : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_moon_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Moon : les deux jeux ne sont pas séparés !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_moon_ps,
    "Year"
].iloc[0] == 1997, (
    "Moon : année PS incorrecte !"
)

assert df.loc[
    masque_moon_ds,
    "Year"
].iloc[0] == 2009, (
    "Moon : année DS incorrecte !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_moon_total,
        "Global_Sales"
    ].sum(), 2
) == 0.23, (
    "Moon : total des ventes incorrect !"
)

# ============================================================
# 8 DUOSEXAGÉSIES. SÉPARATION DES VERSIONS DE LEGEND OF KAY
# ============================================================

# Legend of Kay possède trois versions distinctes :
#
# - PS2 (2005) : jeu original.
#
# - DS (2010) : adaptation spécifique avec modification
#   du gameplay et suppression du système de combat.
#
# - PS4 / Wii U (2015) : remaster Anniversary,
#   avec améliorations graphiques et sonores.
#
# Décision validée :
# Chaque version possède son propre Game_ID.
# Les versions PS4 et Wii U partagent le même Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes et ventes restent inchangées.


# ------------------------------------------------------------
# 1. LEGEND OF KAY - PS2 (2005)
# ------------------------------------------------------------

masque_legend_of_kay_ps2 = (
    (df["Rank"] == 12987)
    & (df["Name"] == "Legend of Kay")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2005)
)

assert masque_legend_of_kay_ps2.sum() == 1, (
    "Legend of Kay : version PS2 2005 introuvable !"
)

df.loc[
    masque_legend_of_kay_ps2,
    "Game_Title_Clean"
] = "Legend of Kay (Original 2005)"


# ------------------------------------------------------------
# 2. LEGEND OF KAY - NINTENDO DS (2010)
# ------------------------------------------------------------

masque_legend_of_kay_ds = (
    (df["Rank"] == 12367)
    & (df["Name"] == "Legend of Kay")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2010)
)

assert masque_legend_of_kay_ds.sum() == 1, (
    "Legend of Kay : version DS 2010 introuvable !"
)

df.loc[
    masque_legend_of_kay_ds,
    "Game_Title_Clean"
] = "Legend of Kay (DS 2010)"


# ------------------------------------------------------------
# 3. LEGEND OF KAY ANNIVERSARY - PS4 (2015)
# ------------------------------------------------------------

masque_legend_of_kay_ps4 = (
    (df["Rank"] == 12328)
    & (df["Name"] == "Legend of Kay")
    & (df["Platform"] == "PS4")
    & (df["Year"] == 2015)
)

assert masque_legend_of_kay_ps4.sum() == 1, (
    "Legend of Kay : version PS4 2015 introuvable !"
)

df.loc[
    masque_legend_of_kay_ps4,
    "Game_Title_Clean"
] = "Legend of Kay Anniversary (2015)"


# ------------------------------------------------------------
# 4. LEGEND OF KAY ANNIVERSARY - WII U (2015)
# ------------------------------------------------------------

masque_legend_of_kay_wiiu = (
    (df["Rank"] == 12823)
    & (df["Name"] == "Legend of Kay")
    & (df["Platform"] == "WiiU")
    & (df["Year"] == 2015)
)

assert masque_legend_of_kay_wiiu.sum() == 1, (
    "Legend of Kay : version Wii U 2015 introuvable !"
)

df.loc[
    masque_legend_of_kay_wiiu,
    "Game_Title_Clean"
] = "Legend of Kay Anniversary (2015)"


# ------------------------------------------------------------
# 5. CONTRÔLE DES TROIS VERSIONS
# ------------------------------------------------------------

masque_legend_of_kay_total = (
    masque_legend_of_kay_ps2
    | masque_legend_of_kay_ds
    | masque_legend_of_kay_ps4
    | masque_legend_of_kay_wiiu
)

# Vérifier que les quatre lignes sont présentes
assert masque_legend_of_kay_total.sum() == 4, (
    "Legend of Kay : nombre de lignes incorrect !"
)

# Vérifier qu'il existe exactement trois titres distincts
assert df.loc[
    masque_legend_of_kay_total,
    "Game_Title_Clean"
].nunique() == 3, (
    "Legend of Kay : les trois versions ne sont pas séparées !"
)

# Vérifier que les versions PS4 et Wii U sont regroupées
assert df.loc[
    masque_legend_of_kay_ps4 | masque_legend_of_kay_wiiu,
    "Game_Title_Clean"
].nunique() == 1, (
    "Legend of Kay : les versions Anniversary doivent être regroupées !"
)

# Vérifier que les années sont conservées
assert df.loc[masque_legend_of_kay_ps2, "Year"].iloc[0] == 2005
assert df.loc[masque_legend_of_kay_ds, "Year"].iloc[0] == 2010
assert df.loc[masque_legend_of_kay_ps4, "Year"].iloc[0] == 2015
assert df.loc[masque_legend_of_kay_wiiu, "Year"].iloc[0] == 2015

# Vérifier que les ventes de l'édition Anniversary sont conservées
assert round(
    df.loc[
        masque_legend_of_kay_ps4 | masque_legend_of_kay_wiiu,
        "Global_Sales"
    ].sum(), 2
) == 0.11, (
    "Legend of Kay : ventes Anniversary incorrectes !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_legend_of_kay_total,
        "Global_Sales"
    ].sum(), 2
) == 0.22, (
    "Legend of Kay : total des ventes incorrect !"
)

# ============================================================
# 8 TRISEXAGÉSIES. SÉPARATION DES JEUX AROUND THE WORLD IN 80 DAYS
# ============================================================

# Deux jeux différents portent le même nom :
#
# - GBA (2004) : jeu d'action et de plateformes
#   adapté du film sorti en 2004.
#
# - DS (2010) : jeu de réflexion de type Match-3,
#   adapté du roman de Jules Verne.
#
# Décision validée :
# Chaque jeu possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes, genres et ventes restent inchangés.


# ------------------------------------------------------------
# 1. AROUND THE WORLD IN 80 DAYS - GBA (2004)
# ------------------------------------------------------------

masque_around_world_gba = (
    (df["Rank"] == 13194)
    & (df["Name"] == "Around the World in 80 Days")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2004)
)

assert masque_around_world_gba.sum() == 1, (
    "Around the World in 80 Days : version GBA 2004 introuvable !"
)

df.loc[
    masque_around_world_gba,
    "Game_Title_Clean"
] = "Around the World in 80 Days (GBA 2004)"


# ------------------------------------------------------------
# 2. AROUND THE WORLD IN 80 DAYS - NINTENDO DS (2010)
# ------------------------------------------------------------

masque_around_world_ds = (
    (df["Rank"] == 8494)
    & (df["Name"] == "Around the World in 80 Days")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2010)
)

assert masque_around_world_ds.sum() == 1, (
    "Around the World in 80 Days : version DS 2010 introuvable !"
)

df.loc[
    masque_around_world_ds,
    "Game_Title_Clean"
] = "Around the World in 80 Days (DS 2010)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX JEUX
# ------------------------------------------------------------

masque_around_world_total = (
    masque_around_world_gba
    | masque_around_world_ds
)

# Vérifier que les deux lignes sont présentes
assert masque_around_world_total.sum() == 2, (
    "Around the World in 80 Days : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_around_world_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Around the World in 80 Days : les deux jeux ne sont pas séparés !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_around_world_gba,
    "Year"
].iloc[0] == 2004, (
    "Around the World in 80 Days : année GBA incorrecte !"
)

assert df.loc[
    masque_around_world_ds,
    "Year"
].iloc[0] == 2010, (
    "Around the World in 80 Days : année DS incorrecte !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_around_world_total,
        "Global_Sales"
    ].sum(), 2
) == 0.21, (
    "Around the World in 80 Days : total des ventes incorrect !"
)

# ============================================================
# 8 QUATTUORSEXAGÉSIES. SÉPARATION DES VERSIONS DE CULDCEPT
# ============================================================

# Culdcept possède deux éditions distinctes dans le dataset :
#
# - PS2 (2002) : Culdcept II: Second Expansion,
#   version enrichie de Culdcept II sorti sur Dreamcast.
#
# - 3DS (2012) : remake avec des graphismes retravaillés,
#   de nouvelles cartes et des mécaniques améliorées.
#
# Décision validée :
# Chaque édition possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes, genres et ventes restent inchangés.


# ------------------------------------------------------------
# 1. CULDCEPT II: SECOND EXPANSION - PS2 (2002)
# ------------------------------------------------------------

masque_culdcept_ps2 = (
    (df["Rank"] == 14556)
    & (df["Name"] == "Culdcept")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2002)
)

assert masque_culdcept_ps2.sum() == 1, (
    "Culdcept : version PS2 2002 introuvable !"
)

df.loc[
    masque_culdcept_ps2,
    "Game_Title_Clean"
] = "Culdcept II: Second Expansion (2002)"


# ------------------------------------------------------------
# 2. CULDCEPT - NINTENDO 3DS (2012)
# ------------------------------------------------------------

masque_culdcept_3ds = (
    (df["Rank"] == 8680)
    & (df["Name"] == "Culdcept")
    & (df["Platform"] == "3DS")
    & (df["Year"] == 2012)
)

assert masque_culdcept_3ds.sum() == 1, (
    "Culdcept : version 3DS 2012 introuvable !"
)

df.loc[
    masque_culdcept_3ds,
    "Game_Title_Clean"
] = "Culdcept (3DS Remake 2012)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_culdcept_total = (
    masque_culdcept_ps2
    | masque_culdcept_3ds
)

# Vérifier que les deux lignes sont présentes
assert masque_culdcept_total.sum() == 2, (
    "Culdcept : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_culdcept_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Culdcept : les deux versions ne sont pas séparées !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_culdcept_ps2,
    "Year"
].iloc[0] == 2002, (
    "Culdcept : année PS2 incorrecte !"
)

assert df.loc[
    masque_culdcept_3ds,
    "Year"
].iloc[0] == 2012, (
    "Culdcept : année 3DS incorrecte !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_culdcept_total,
        "Global_Sales"
    ].sum(), 2
) == 0.19, (
    "Culdcept : total des ventes incorrect !"
)

# ============================================================
# 8 QUINQUSEXAGÉSIES. SÉPARATION DES VERSIONS DE DOOM
# ============================================================

# Doom possède deux versions distinctes dans ce regroupement :
#
# - PC (1993) : jeu original développé par id Software.
#
# - GBA (2001) : adaptation spécifique avec modification
#   des niveaux, suppression de certains ennemis,
#   censure et ajout de cartes multijoueurs.
#
# Décision validée :
# Chaque version possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes, genres et ventes restent inchangés.


# ------------------------------------------------------------
# 1. DOOM ORIGINAL - PC (1993)
# ------------------------------------------------------------

masque_doom_pc = (
    (df["Rank"] == 14602)
    & (df["Name"] == "Doom")
    & (df["Platform"] == "PC")
    & (df["Year"] == 1993)
)

assert masque_doom_pc.sum() == 1, (
    "Doom : version PC 1993 introuvable !"
)

df.loc[
    masque_doom_pc,
    "Game_Title_Clean"
] = "Doom (Original 1993)"


# ------------------------------------------------------------
# 2. DOOM - GAME BOY ADVANCE (2001)
# ------------------------------------------------------------

masque_doom_gba = (
    (df["Rank"] == 9087)
    & (df["Name"] == "Doom")
    & (df["Platform"] == "GBA")
    & (df["Year"] == 2001)
)

assert masque_doom_gba.sum() == 1, (
    "Doom : version GBA 2001 introuvable !"
)

df.loc[
    masque_doom_gba,
    "Game_Title_Clean"
] = "Doom (GBA 2001)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_doom_total = (
    masque_doom_pc
    | masque_doom_gba
)

# Vérifier que les deux lignes sont présentes
assert masque_doom_total.sum() == 2, (
    "Doom : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_doom_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Doom : les deux versions ne sont pas séparées !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_doom_pc,
    "Year"
].iloc[0] == 1993, (
    "Doom : année PC incorrecte !"
)

assert df.loc[
    masque_doom_gba,
    "Year"
].iloc[0] == 2001, (
    "Doom : année GBA incorrecte !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_doom_total,
        "Global_Sales"
    ].sum(), 2
) == 0.17, (
    "Doom : total des ventes incorrect !"
)

# ============================================================
# 8 SEXSEXAGÉSIES. SÉPARATION DES VERSIONS DE CLANNAD
# ============================================================

# Clannad possède trois versions distinctes dans le dataset :
#
# - PS2 (2006) : première édition sur console.
#
# - PSP (2008) : adaptation de l'édition Full Voice.
#
# - Xbox 360 (2008) / PS3 (2011) : édition HD,
#   avec améliorations graphiques et sonores.
#
# Décision validée :
# Chaque version possède son propre Game_ID.
# Les versions Xbox 360 et PS3 partagent le même Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes, genres et ventes restent inchangés.


# ------------------------------------------------------------
# 1. CLANNAD - PS2 (2006)
# ------------------------------------------------------------

masque_clannad_ps2 = (
    (df["Rank"] == 13780)
    & (df["Name"] == "Clannad")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2006)
)

assert masque_clannad_ps2.sum() == 1, (
    "Clannad : version PS2 2006 introuvable !"
)

df.loc[
    masque_clannad_ps2,
    "Game_Title_Clean"
] = "Clannad (PS2 2006)"


# ------------------------------------------------------------
# 2. CLANNAD FULL VOICE - PSP (2008)
# ------------------------------------------------------------

masque_clannad_psp = (
    (df["Rank"] == 13816)
    & (df["Name"] == "Clannad")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2008)
)

assert masque_clannad_psp.sum() == 1, (
    "Clannad : version PSP 2008 introuvable !"
)

df.loc[
    masque_clannad_psp,
    "Game_Title_Clean"
] = "Clannad (Full Voice 2008)"


# ------------------------------------------------------------
# 3. CLANNAD HD EDITION - XBOX 360 (2008)
# ------------------------------------------------------------

masque_clannad_x360 = (
    (df["Rank"] == 14772)
    & (df["Name"] == "Clannad")
    & (df["Platform"] == "X360")
    & (df["Year"] == 2008)
)

assert masque_clannad_x360.sum() == 1, (
    "Clannad : version Xbox 360 2008 introuvable !"
)

df.loc[
    masque_clannad_x360,
    "Game_Title_Clean"
] = "Clannad (HD Edition 2008)"


# ------------------------------------------------------------
# 4. CLANNAD HD EDITION - PS3 (2011)
# ------------------------------------------------------------

masque_clannad_ps3 = (
    (df["Rank"] == 14244)
    & (df["Name"] == "Clannad")
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2011)
)

assert masque_clannad_ps3.sum() == 1, (
    "Clannad : version PS3 2011 introuvable !"
)

df.loc[
    masque_clannad_ps3,
    "Game_Title_Clean"
] = "Clannad (HD Edition 2008)"


# ------------------------------------------------------------
# 5. CONTRÔLE DES TROIS VERSIONS
# ------------------------------------------------------------

masque_clannad_total = (
    masque_clannad_ps2
    | masque_clannad_psp
    | masque_clannad_x360
    | masque_clannad_ps3
)

# Vérifier que les quatre lignes sont présentes
assert masque_clannad_total.sum() == 4, (
    "Clannad : nombre de lignes incorrect !"
)

# Vérifier qu'il existe exactement trois titres distincts
assert df.loc[
    masque_clannad_total,
    "Game_Title_Clean"
].nunique() == 3, (
    "Clannad : les trois versions ne sont pas séparées !"
)

# Vérifier que les versions Xbox 360 et PS3 sont regroupées
assert df.loc[
    masque_clannad_x360 | masque_clannad_ps3,
    "Game_Title_Clean"
].nunique() == 1, (
    "Clannad : les versions HD doivent être regroupées !"
)

# Vérifier que les années sont conservées
assert df.loc[masque_clannad_ps2, "Year"].iloc[0] == 2006
assert df.loc[masque_clannad_psp, "Year"].iloc[0] == 2008
assert df.loc[masque_clannad_x360, "Year"].iloc[0] == 2008
assert df.loc[masque_clannad_ps3, "Year"].iloc[0] == 2011

# Vérifier que les ventes de l'édition HD sont conservées
assert round(
    df.loc[
        masque_clannad_x360 | masque_clannad_ps3,
        "Global_Sales"
    ].sum(), 2
) == 0.06, (
    "Clannad : ventes de l'édition HD incorrectes !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_clannad_total,
        "Global_Sales"
    ].sum(), 2
) == 0.14, (
    "Clannad : total des ventes incorrect !"
)

# ============================================================
# 8 SEPTENSEXAGÉSIES. SÉPARATION DES VERSIONS DE KINIRO NO CORDA 3
# ============================================================

# Kiniro no Corda 3 possède deux versions distinctes
# dans le dataset :
#
# - PS2 / PSP (2010) : jeu original.
#
# - Nintendo 3DS (2015) : édition Full Voice Special,
#   avec doublage intégral, nouveaux événements,
#   illustrations et contenus supplémentaires.
#
# Décision validée :
# Les versions PS2 et PSP partagent le même Game_ID.
# La version Nintendo 3DS possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes, genres et ventes restent inchangés.


# ------------------------------------------------------------
# 1. KINIRO NO CORDA 3 ORIGINAL - PS2 (2010)
# ------------------------------------------------------------

masque_corda3_ps2 = (
    (df["Rank"] == 14404)
    & (df["Name"] == "Kiniro no Corda 3")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2010)
)

assert masque_corda3_ps2.sum() == 1, (
    "Kiniro no Corda 3 : version PS2 2010 introuvable !"
)

df.loc[
    masque_corda3_ps2,
    "Game_Title_Clean"
] = "Kiniro no Corda 3 (Original 2010)"


# ------------------------------------------------------------
# 2. KINIRO NO CORDA 3 ORIGINAL - PSP (2010)
# ------------------------------------------------------------

masque_corda3_psp = (
    (df["Rank"] == 10827)
    & (df["Name"] == "Kiniro no Corda 3")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2010)
)

assert masque_corda3_psp.sum() == 1, (
    "Kiniro no Corda 3 : version PSP 2010 introuvable !"
)

df.loc[
    masque_corda3_psp,
    "Game_Title_Clean"
] = "Kiniro no Corda 3 (Original 2010)"


# ------------------------------------------------------------
# 3. KINIRO NO CORDA 3 FULL VOICE SPECIAL - 3DS (2015)
# ------------------------------------------------------------

masque_corda3_3ds = (
    (df["Rank"] == 16531)
    & (df["Name"] == "Kiniro no Corda 3")
    & (df["Platform"] == "3DS")
    & (df["Year"] == 2015)
)

assert masque_corda3_3ds.sum() == 1, (
    "Kiniro no Corda 3 : version 3DS 2015 introuvable !"
)

df.loc[
    masque_corda3_3ds,
    "Game_Title_Clean"
] = "Kiniro no Corda 3: Full Voice Special (3DS 2015)"


# ------------------------------------------------------------
# 4. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_corda3_total = (
    masque_corda3_ps2
    | masque_corda3_psp
    | masque_corda3_3ds
)

# Vérifier que les trois lignes sont présentes
assert masque_corda3_total.sum() == 3, (
    "Kiniro no Corda 3 : nombre de lignes incorrect !"
)

# Vérifier que les deux éditions sont distinctes
assert df.loc[
    masque_corda3_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Kiniro no Corda 3 : les deux versions ne sont pas séparées !"
)

# Vérifier que les versions PS2 et PSP sont regroupées
assert df.loc[
    masque_corda3_ps2 | masque_corda3_psp,
    "Game_Title_Clean"
].nunique() == 1, (
    "Kiniro no Corda 3 : les versions originales doivent être regroupées !"
)

# Vérifier que les années sont conservées
assert df.loc[masque_corda3_ps2, "Year"].iloc[0] == 2010
assert df.loc[masque_corda3_psp, "Year"].iloc[0] == 2010
assert df.loc[masque_corda3_3ds, "Year"].iloc[0] == 2015

# Vérifier les ventes de la version originale
assert round(
    df.loc[
        masque_corda3_ps2 | masque_corda3_psp,
        "Global_Sales"
    ].sum(), 2
) == 0.12, (
    "Kiniro no Corda 3 : ventes de la version originale incorrectes !"
)

# Vérifier les ventes de l'édition Full Voice Special
assert round(
    df.loc[
        masque_corda3_3ds,
        "Global_Sales"
    ].sum(), 2
) == 0.01, (
    "Kiniro no Corda 3 : ventes de la version 3DS incorrectes !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_corda3_total,
        "Global_Sales"
    ].sum(), 2
) == 0.13, (
    "Kiniro no Corda 3 : total des ventes incorrect !"
)

# ============================================================
# 8 OCTOSEXAGÉSIES. SÉPARATION DES JEUX AGATHA CHRISTIE:
# THE ABC MURDERS
# ============================================================

# Agatha Christie: The ABC Murders correspond à deux jeux
# développés indépendamment dans le dataset :
#
# - Nintendo DS (2009) : adaptation orientée vers
#   la résolution d'énigmes et l'utilisation de l'écran tactile.
#
# - PC (2016) : nouvelle adaptation développée par
#   Artefacts Studio et éditée par Microids.
#
# Les deux jeux sont inspirés du même roman,
# mais possèdent un gameplay et une conception différents.
#
# Décision validée :
# Chaque jeu possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes, genres et ventes restent inchangés.


# ------------------------------------------------------------
# 1. AGATHA CHRISTIE: THE ABC MURDERS - DS (2009)
# ------------------------------------------------------------

masque_abc_murders_ds = (
    (df["Rank"] == 10446)
    & (df["Name"] == "Agatha Christie: The ABC Murders")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2009)
)

assert masque_abc_murders_ds.sum() == 1, (
    "Agatha Christie : version DS 2009 introuvable !"
)

df.loc[
    masque_abc_murders_ds,
    "Game_Title_Clean"
] = "Agatha Christie: The ABC Murders (2009)"


# ------------------------------------------------------------
# 2. AGATHA CHRISTIE: THE ABC MURDERS - PC (2016)
# ------------------------------------------------------------

masque_abc_murders_pc = (
    (df["Rank"] == 15473)
    & (df["Name"] == "Agatha Christie: The ABC Murders")
    & (df["Platform"] == "PC")
    & (df["Year"] == 2016)
)

assert masque_abc_murders_pc.sum() == 1, (
    "Agatha Christie : version PC 2016 introuvable !"
)

df.loc[
    masque_abc_murders_pc,
    "Game_Title_Clean"
] = "Agatha Christie: The ABC Murders (2016)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX JEUX
# ------------------------------------------------------------

masque_abc_murders_total = (
    masque_abc_murders_ds
    | masque_abc_murders_pc
)

# Vérifier que les deux lignes sont présentes
assert masque_abc_murders_total.sum() == 2, (
    "Agatha Christie : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_abc_murders_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Agatha Christie : les deux jeux ne sont pas séparés !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_abc_murders_ds,
    "Year"
].iloc[0] == 2009

assert df.loc[
    masque_abc_murders_pc,
    "Year"
].iloc[0] == 2016

# Vérifier les ventes de la version DS
assert round(
    df.loc[
        masque_abc_murders_ds,
        "Global_Sales"
    ].sum(), 2
) == 0.10, (
    "Agatha Christie : ventes DS incorrectes !"
)

# Vérifier les ventes de la version PC
assert round(
    df.loc[
        masque_abc_murders_pc,
        "Global_Sales"
    ].sum(), 2
) == 0.02, (
    "Agatha Christie : ventes PC incorrectes !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_abc_murders_total,
        "Global_Sales"
    ].sum(), 2
) == 0.12, (
    "Agatha Christie : total des ventes incorrect !"
)

# ============================================================
# 8 NOVEMSEXAGÉSIES. SÉPARATION DES JEUX TOP GUN
# ============================================================

# Top Gun correspond à deux jeux développés
# indépendamment dans le dataset :
#
# - Nintendo DS (2006) : jeu développé par Interactive Vision.
#
# - PlayStation 3 (2011) : jeu développé par Doublesix,
#   initialement commercialisé en téléchargement en 2010,
#   puis en édition physique en 2011.
#
# Les deux jeux exploitent la même licence,
# mais ne correspondent pas à la même adaptation.
#
# Décision validée :
# Chaque jeu possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes, genres et ventes restent inchangés.


# ------------------------------------------------------------
# 1. TOP GUN - NINTENDO DS (2006)
# ------------------------------------------------------------

masque_top_gun_ds = (
    (df["Rank"] == 13537)
    & (df["Name"] == "Top Gun")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2006)
)

assert masque_top_gun_ds.sum() == 1, (
    "Top Gun : version DS 2006 introuvable !"
)

df.loc[
    masque_top_gun_ds,
    "Game_Title_Clean"
] = "Top Gun (DS 2006)"


# ------------------------------------------------------------
# 2. TOP GUN - PLAYSTATION 3 (2011)
# ------------------------------------------------------------

masque_top_gun_ps3 = (
    (df["Rank"] == 12221)
    & (df["Name"] == "Top Gun")
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2011)
)

assert masque_top_gun_ps3.sum() == 1, (
    "Top Gun : version PS3 2011 introuvable !"
)

df.loc[
    masque_top_gun_ps3,
    "Game_Title_Clean"
] = "Top Gun (PS3 2011)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX JEUX
# ------------------------------------------------------------

masque_top_gun_total = (
    masque_top_gun_ds
    | masque_top_gun_ps3
)

# Vérifier que les deux lignes sont présentes
assert masque_top_gun_total.sum() == 2, (
    "Top Gun : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_top_gun_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Top Gun : les deux jeux ne sont pas séparés !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_top_gun_ds,
    "Year"
].iloc[0] == 2006

assert df.loc[
    masque_top_gun_ps3,
    "Year"
].iloc[0] == 2011

# Vérifier les ventes de la version DS
assert round(
    df.loc[
        masque_top_gun_ds,
        "Global_Sales"
    ].sum(), 2
) == 0.04, (
    "Top Gun : ventes DS incorrectes !"
)

# Vérifier les ventes de la version PS3
assert round(
    df.loc[
        masque_top_gun_ps3,
        "Global_Sales"
    ].sum(), 2
) == 0.07, (
    "Top Gun : ventes PS3 incorrectes !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_top_gun_total,
        "Global_Sales"
    ].sum(), 2
) == 0.11, (
    "Top Gun : total des ventes incorrect !"
)

# ============================================================
# 8 SEPTUAGÉSIES. SÉPARATION DES VERSIONS DE RHAPSODY:
# A MUSICAL ADVENTURE
# ============================================================

# Rhapsody: A Musical Adventure possède deux versions
# distinctes dans le dataset :
#
# - PlayStation (1998) : jeu original avec un système
#   de combat tactique sur une grille.
#
# - Nintendo DS (2008) : remake avec un nouveau système
#   de combat au tour par tour, de nouveaux contenus
#   et une interface adaptée à la console.
#
# Décision validée :
# Chaque version possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes, genres et ventes restent inchangés.


# ------------------------------------------------------------
# 1. RHAPSODY ORIGINAL - PLAYSTATION (1998)
# ------------------------------------------------------------

masque_rhapsody_ps = (
    (df["Rank"] == 13994)
    & (df["Name"] == "Rhapsody: A Musical Adventure")
    & (df["Platform"] == "PS")
    & (df["Year"] == 1998)
)

assert masque_rhapsody_ps.sum() == 1, (
    "Rhapsody : version PS 1998 introuvable !"
)

df.loc[
    masque_rhapsody_ps,
    "Game_Title_Clean"
] = "Rhapsody: A Musical Adventure (Original 1998)"


# ------------------------------------------------------------
# 2. RHAPSODY REMAKE - NINTENDO DS (2008)
# ------------------------------------------------------------

masque_rhapsody_ds = (
    (df["Rank"] == 12717)
    & (df["Name"] == "Rhapsody: A Musical Adventure")
    & (df["Platform"] == "DS")
    & (df["Year"] == 2008)
)

assert masque_rhapsody_ds.sum() == 1, (
    "Rhapsody : version DS 2008 introuvable !"
)

df.loc[
    masque_rhapsody_ds,
    "Game_Title_Clean"
] = "Rhapsody: A Musical Adventure (DS Remake 2008)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_rhapsody_total = (
    masque_rhapsody_ps
    | masque_rhapsody_ds
)

# Vérifier que les deux lignes sont présentes
assert masque_rhapsody_total.sum() == 2, (
    "Rhapsody : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_rhapsody_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Rhapsody : les deux versions ne sont pas séparées !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_rhapsody_ps,
    "Year"
].iloc[0] == 1998

assert df.loc[
    masque_rhapsody_ds,
    "Year"
].iloc[0] == 2008

# Vérifier les ventes de la version originale
assert round(
    df.loc[
        masque_rhapsody_ps,
        "Global_Sales"
    ].sum(), 2
) == 0.04, (
    "Rhapsody : ventes de la version originale incorrectes !"
)

# Vérifier les ventes du remake
assert round(
    df.loc[
        masque_rhapsody_ds,
        "Global_Sales"
    ].sum(), 2
) == 0.06, (
    "Rhapsody : ventes du remake incorrectes !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_rhapsody_total,
        "Global_Sales"
    ].sum(), 2
) == 0.10, (
    "Rhapsody : total des ventes incorrect !"
)

# ============================================================
# 8 UNSEPTUAGÉSIES. SÉPARATION DES VERSIONS DE
# THE LEGEND OF HEROES: TRAILS IN THE SKY THIRD CHAPTER
# ============================================================

# The Legend of Heroes: Trails in the Sky Third Chapter
# possède trois versions distinctes dans le dataset :
#
# - PSP (2008) : portage de la version originale PC.
#
# - PS3 (2013) : Kai HD Edition, remaster HD.
#
# - PS Vita (2016) : Evolution, édition améliorée
#   avec nouveaux portraits, doublages, bande-son
#   réarrangée et modernisation du système de combat.
#
# Décision validée :
# Chaque version possède son propre Game_ID.
#
# Cette classification respecte la logique appliquée
# au First Chapter dans la section 8 TRIQUINQUAGÉSIES.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes, genres et ventes restent inchangés.


# ------------------------------------------------------------
# 1. TRAILS IN THE SKY THIRD CHAPTER - PSP (2008)
# ------------------------------------------------------------

masque_trails_3rd_psp = (
    (df["Rank"] == 11912)
    & (df["Name"] == "The Legend of Heroes: Trails in the Sky Third Chapter")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2008)
)

assert masque_trails_3rd_psp.sum() == 1, (
    "Trails in the Sky Third Chapter : version PSP 2008 introuvable !"
)

df.loc[
    masque_trails_3rd_psp,
    "Game_Title_Clean"
] = "The Legend of Heroes: Trails in the Sky Third Chapter"


# ------------------------------------------------------------
# 2. TRAILS IN THE SKY THE 3RD KAI HD EDITION - PS3 (2013)
# ------------------------------------------------------------

masque_trails_3rd_ps3 = (
    (df["Rank"] == 16087)
    & (df["Name"] == "The Legend of Heroes: Trails in the Sky Third Chapter")
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2013)
)

assert masque_trails_3rd_ps3.sum() == 1, (
    "Trails in the Sky Third Chapter : version PS3 2013 introuvable !"
)

df.loc[
    masque_trails_3rd_ps3,
    "Game_Title_Clean"
] = "The Legend of Heroes: Trails in the Sky the 3rd Kai HD Edition (2013)"


# ------------------------------------------------------------
# 3. TRAILS IN THE SKY THE 3RD EVOLUTION - PS VITA (2016)
# ------------------------------------------------------------

masque_trails_3rd_psv = (
    (df["Rank"] == 15372)
    & (df["Name"] == "The Legend of Heroes: Trails in the Sky Third Chapter")
    & (df["Platform"] == "PSV")
    & (df["Year"] == 2016)
)

assert masque_trails_3rd_psv.sum() == 1, (
    "Trails in the Sky Third Chapter : version PSV 2016 introuvable !"
)

df.loc[
    masque_trails_3rd_psv,
    "Game_Title_Clean"
] = "The Legend of Heroes: Trails in the Sky the 3rd Evolution (2016)"


# ------------------------------------------------------------
# 4. CONTRÔLE DES TROIS VERSIONS
# ------------------------------------------------------------

masque_trails_3rd_total = (
    masque_trails_3rd_psp
    | masque_trails_3rd_ps3
    | masque_trails_3rd_psv
)

# Vérifier que les trois lignes sont présentes
assert masque_trails_3rd_total.sum() == 3, (
    "Trails in the Sky Third Chapter : nombre de lignes incorrect !"
)

# Vérifier que les trois titres normalisés sont distincts
assert df.loc[
    masque_trails_3rd_total,
    "Game_Title_Clean"
].nunique() == 3, (
    "Trails in the Sky Third Chapter : les trois versions ne sont pas séparées !"
)

# Vérifier que les années sont conservées
assert df.loc[masque_trails_3rd_psp, "Year"].iloc[0] == 2008
assert df.loc[masque_trails_3rd_ps3, "Year"].iloc[0] == 2013
assert df.loc[masque_trails_3rd_psv, "Year"].iloc[0] == 2016

# Vérifier les ventes de la version classique
assert round(
    df.loc[
        masque_trails_3rd_psp,
        "Global_Sales"
    ].sum(), 2
) == 0.07, (
    "Trails in the Sky Third Chapter : ventes PSP incorrectes !"
)

# Vérifier les ventes du remaster Kai HD
assert round(
    df.loc[
        masque_trails_3rd_ps3,
        "Global_Sales"
    ].sum(), 2
) == 0.01, (
    "Trails in the Sky Third Chapter : ventes PS3 incorrectes !"
)

# Vérifier les ventes de l'édition Evolution
assert round(
    df.loc[
        masque_trails_3rd_psv,
        "Global_Sales"
    ].sum(), 2
) == 0.02, (
    "Trails in the Sky Third Chapter : ventes PSV incorrectes !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_trails_3rd_total,
        "Global_Sales"
    ].sum(), 2
) == 0.10, (
    "Trails in the Sky Third Chapter : total des ventes incorrect !"
)

# ============================================================
# 8 DUOSEPTUAGÉSIES. SÉPARATION DES VERSIONS DE
# SD GUNDAM: GASHAPON WARS
# ============================================================

# SD Gundam: Gashapon Wars possède deux versions
# distinctes dans le dataset :
#
# - GameCube (2005) : version originale.
#
# - Wii (2010) : portage enrichi avec de nouveaux
#   modes de jeu et une interface adaptée à la console.
#
# Décision validée :
# Chaque version possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes, genres et ventes restent inchangés.


# ------------------------------------------------------------
# 1. SD GUNDAM: GASHAPON WARS - GAMECUBE (2005)
# ------------------------------------------------------------

masque_gashapon_gc = (
    (df["Rank"] == 11852)
    & (df["Name"] == "SD Gundam: Gashapon Wars")
    & (df["Platform"] == "GC")
    & (df["Year"] == 2005)
)

assert masque_gashapon_gc.sum() == 1, (
    "SD Gundam: Gashapon Wars : version GC 2005 introuvable !"
)

df.loc[
    masque_gashapon_gc,
    "Game_Title_Clean"
] = "SD Gundam: Gashapon Wars (Original 2005)"


# ------------------------------------------------------------
# 2. SD GUNDAM: GASHAPON WARS - WII (2010)
# ------------------------------------------------------------

masque_gashapon_wii = (
    (df["Rank"] == 14542)
    & (df["Name"] == "SD Gundam: Gashapon Wars")
    & (df["Platform"] == "Wii")
    & (df["Year"] == 2010)
)

assert masque_gashapon_wii.sum() == 1, (
    "SD Gundam: Gashapon Wars : version Wii 2010 introuvable !"
)

df.loc[
    masque_gashapon_wii,
    "Game_Title_Clean"
] = "SD Gundam: Gashapon Wars (Wii Enhanced 2010)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_gashapon_total = (
    masque_gashapon_gc
    | masque_gashapon_wii
)

# Vérifier que les deux lignes sont présentes
assert masque_gashapon_total.sum() == 2, (
    "SD Gundam: Gashapon Wars : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_gashapon_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "SD Gundam: Gashapon Wars : les deux versions ne sont pas séparées !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_gashapon_gc,
    "Year"
].iloc[0] == 2005

assert df.loc[
    masque_gashapon_wii,
    "Year"
].iloc[0] == 2010

# Vérifier les ventes de la version originale
assert round(
    df.loc[
        masque_gashapon_gc,
        "Global_Sales"
    ].sum(), 2
) == 0.07, (
    "SD Gundam: Gashapon Wars : ventes GC incorrectes !"
)

# Vérifier les ventes de la version enrichie
assert round(
    df.loc[
        masque_gashapon_wii,
        "Global_Sales"
    ].sum(), 2
) == 0.03, (
    "SD Gundam: Gashapon Wars : ventes Wii incorrectes !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_gashapon_total,
        "Global_Sales"
    ].sum(), 2
) == 0.10, (
    "SD Gundam: Gashapon Wars : total des ventes incorrect !"
)

# ============================================================
# 8 TRISEPTUAGÉSIES. SÉPARATION DES VERSIONS DE
# CORPSE PARTY: BLOOD COVERED - REPEATED FEAR
# ============================================================

# Corpse Party: Blood Covered - Repeated Fear possède
# deux versions distinctes dans le dataset :
#
# - PSP (2010) : version de référence.
#
# - Nintendo 3DS (2015) : réédition enrichie avec
#   des améliorations graphiques, musicales
#   et des chapitres supplémentaires.
#
# Décision validée :
# Chaque version possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes, genres et ventes restent inchangés.


# ------------------------------------------------------------
# 1. CORPSE PARTY - PSP (2010)
# ------------------------------------------------------------

masque_corpse_party_psp = (
    (df["Rank"] == 13144)
    & (df["Name"] == "Corpse Party: Blood Covered - Repeated Fear")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2010)
)

assert masque_corpse_party_psp.sum() == 1, (
    "Corpse Party : version PSP 2010 introuvable !"
)

df.loc[
    masque_corpse_party_psp,
    "Game_Title_Clean"
] = "Corpse Party: Blood Covered - Repeated Fear (2010)"


# ------------------------------------------------------------
# 2. CORPSE PARTY REMASTER - NINTENDO 3DS (2015)
# ------------------------------------------------------------

masque_corpse_party_3ds = (
    (df["Rank"] == 13933)
    & (df["Name"] == "Corpse Party: Blood Covered - Repeated Fear")
    & (df["Platform"] == "3DS")
    & (df["Year"] == 2015)
)

assert masque_corpse_party_3ds.sum() == 1, (
    "Corpse Party : version 3DS 2015 introuvable !"
)

df.loc[
    masque_corpse_party_3ds,
    "Game_Title_Clean"
] = "Corpse Party: Blood Covered - Repeated Fear (3DS Remaster 2015)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_corpse_party_total = (
    masque_corpse_party_psp
    | masque_corpse_party_3ds
)

# Vérifier que les deux lignes sont présentes
assert masque_corpse_party_total.sum() == 2, (
    "Corpse Party : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_corpse_party_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Corpse Party : les deux versions ne sont pas séparées !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_corpse_party_psp,
    "Year"
].iloc[0] == 2010

assert df.loc[
    masque_corpse_party_3ds,
    "Year"
].iloc[0] == 2015

# Vérifier les ventes de la version PSP
assert round(
    df.loc[
        masque_corpse_party_psp,
        "Global_Sales"
    ].sum(), 2
) == 0.05, (
    "Corpse Party : ventes PSP incorrectes !"
)

# Vérifier les ventes du remaster 3DS
assert round(
    df.loc[
        masque_corpse_party_3ds,
        "Global_Sales"
    ].sum(), 2
) == 0.04, (
    "Corpse Party : ventes 3DS incorrectes !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_corpse_party_total,
        "Global_Sales"
    ].sum(), 2
) == 0.09, (
    "Corpse Party : total des ventes incorrect !"
)

# ============================================================
# 8 QUATTUORSEPTUAGÉSIES. SÉPARATION DES VERSIONS DE
# THE LEGEND OF HEROES: TRAILS IN THE SKY SECOND CHAPTER
# ============================================================

# The Legend of Heroes: Trails in the Sky Second Chapter
# possède deux versions distinctes dans le dataset :
#
# - PSP (2007) : portage de la version originale PC.
#
# - PS3 (2013) : Kai HD Edition, remaster avec
#   des améliorations graphiques et sonores.
#
# Décision validée :
# Chaque version possède son propre Game_ID.
#
# Cette classification respecte la logique appliquée
# aux deux autres épisodes de la trilogie :
#
# - First Chapter : section 8 TRIQUINQUAGÉSIES.
# - Third Chapter : section 8 UNSEPTUAGÉSIES.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes, genres et ventes restent inchangés.


# ------------------------------------------------------------
# 1. TRAILS IN THE SKY SECOND CHAPTER - PSP (2007)
# ------------------------------------------------------------

masque_trails_sc_psp = (
    (df["Rank"] == 12365)
    & (df["Name"] == "The Legend of Heroes: Trails in the Sky Second Chapter")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2007)
)

assert masque_trails_sc_psp.sum() == 1, (
    "Trails in the Sky Second Chapter : version PSP 2007 introuvable !"
)

df.loc[
    masque_trails_sc_psp,
    "Game_Title_Clean"
] = "The Legend of Heroes: Trails in the Sky Second Chapter"


# ------------------------------------------------------------
# 2. TRAILS IN THE SKY SC KAI HD EDITION - PS3 (2013)
# ------------------------------------------------------------

masque_trails_sc_ps3 = (
    (df["Rank"] == 15401)
    & (df["Name"] == "The Legend of Heroes: Trails in the Sky Second Chapter")
    & (df["Platform"] == "PS3")
    & (df["Year"] == 2013)
)

assert masque_trails_sc_ps3.sum() == 1, (
    "Trails in the Sky Second Chapter : version PS3 2013 introuvable !"
)

df.loc[
    masque_trails_sc_ps3,
    "Game_Title_Clean"
] = "The Legend of Heroes: Trails in the Sky SC Kai HD Edition (2013)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_trails_sc_total = (
    masque_trails_sc_psp
    | masque_trails_sc_ps3
)

# Vérifier que les deux lignes sont présentes
assert masque_trails_sc_total.sum() == 2, (
    "Trails in the Sky Second Chapter : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_trails_sc_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Trails in the Sky Second Chapter : les deux versions ne sont pas séparées !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_trails_sc_psp,
    "Year"
].iloc[0] == 2007

assert df.loc[
    masque_trails_sc_ps3,
    "Year"
].iloc[0] == 2013

# Vérifier les ventes de la version classique
assert round(
    df.loc[
        masque_trails_sc_psp,
        "Global_Sales"
    ].sum(), 2
) == 0.06, (
    "Trails in the Sky Second Chapter : ventes PSP incorrectes !"
)

# Vérifier les ventes du remaster Kai HD
assert round(
    df.loc[
        masque_trails_sc_ps3,
        "Global_Sales"
    ].sum(), 2
) == 0.02, (
    "Trails in the Sky Second Chapter : ventes PS3 incorrectes !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_trails_sc_total,
        "Global_Sales"
    ].sum(), 2
) == 0.08, (
    "Trails in the Sky Second Chapter : total des ventes incorrect !"
)

# ============================================================
# 8 QUINQUASEPTUAGÉSIES. SÉPARATION DES VERSIONS DE
# ARABIANS LOST: THE ENGAGEMENT ON DESERT
# ============================================================

# Arabians Lost: The Engagement on Desert possède
# deux versions distinctes dans le dataset :
#
# - PS2 (2007) : première adaptation sur console.
#
# - PSP (2012) : réédition enrichie avec une refonte
#   des illustrations et des modifications narratives.
#
# Décision validée :
# Chaque version possède son propre Game_ID.
#
# Seule la colonne Game_Title_Clean est modifiée.
# Les années, plateformes, genres et ventes restent inchangés.


# ------------------------------------------------------------
# 1. ARABIANS LOST - PS2 (2007)
# ------------------------------------------------------------

masque_arabians_ps2 = (
    (df["Rank"] == 15587)
    & (df["Name"] == "Arabians Lost: The Engagement on Desert")
    & (df["Platform"] == "PS2")
    & (df["Year"] == 2007)
)

assert masque_arabians_ps2.sum() == 1, (
    "Arabians Lost : version PS2 2007 introuvable !"
)

df.loc[
    masque_arabians_ps2,
    "Game_Title_Clean"
] = "Arabians Lost: The Engagement on Desert (PS2 2007)"


# ------------------------------------------------------------
# 2. ARABIANS LOST ENHANCED - PSP (2012)
# ------------------------------------------------------------

masque_arabians_psp = (
    (df["Rank"] == 16372)
    & (df["Name"] == "Arabians Lost: The Engagement on Desert")
    & (df["Platform"] == "PSP")
    & (df["Year"] == 2012)
)

assert masque_arabians_psp.sum() == 1, (
    "Arabians Lost : version PSP 2012 introuvable !"
)

df.loc[
    masque_arabians_psp,
    "Game_Title_Clean"
] = "Arabians Lost: The Engagement on Desert (PSP Enhanced 2012)"


# ------------------------------------------------------------
# 3. CONTRÔLE DES DEUX VERSIONS
# ------------------------------------------------------------

masque_arabians_total = (
    masque_arabians_ps2
    | masque_arabians_psp
)

# Vérifier que les deux lignes sont présentes
assert masque_arabians_total.sum() == 2, (
    "Arabians Lost : nombre de lignes incorrect !"
)

# Vérifier que les deux titres normalisés sont distincts
assert df.loc[
    masque_arabians_total,
    "Game_Title_Clean"
].nunique() == 2, (
    "Arabians Lost : les deux versions ne sont pas séparées !"
)

# Vérifier que les années sont conservées
assert df.loc[
    masque_arabians_ps2,
    "Year"
].iloc[0] == 2007

assert df.loc[
    masque_arabians_psp,
    "Year"
].iloc[0] == 2012

# Vérifier les ventes de la version PS2
assert round(
    df.loc[
        masque_arabians_ps2,
        "Global_Sales"
    ].sum(), 2
) == 0.02, (
    "Arabians Lost : ventes PS2 incorrectes !"
)

# Vérifier les ventes de la version enrichie PSP
assert round(
    df.loc[
        masque_arabians_psp,
        "Global_Sales"
    ].sum(), 2
) == 0.01, (
    "Arabians Lost : ventes PSP incorrectes !"
)

# Vérifier que les ventes mondiales sont conservées
assert round(
    df.loc[
        masque_arabians_total,
        "Global_Sales"
    ].sum(), 2
) == 0.03, (
    "Arabians Lost : total des ventes incorrect !"
)

# ============================================================
# 9. CRÉATION DES IDENTIFIANTS DE JEUX
# ============================================================

# factorize attribue un numéro à chaque titre distinct.
# Deux lignes avec le même Game_Title_Clean auront le même ID.

df["Game_ID"] = (
    pd.factorize(df["Game_Title_Clean"], sort=True)[0] + 1
)

# ============================================================
# 10. CONTRÔLE DES IDENTIFIANTS
# ============================================================

print("\n=== CONTRÔLE DES GAME_ID ===")

print(f"Nombre de Game_ID distincts : {df['Game_ID'].nunique()}")
print(f"Game_ID manquants : {df['Game_ID'].isna().sum()}")

# Vérification sur nos trois jeux homonymes
controle_ids = df[df["Name"].isin(jeux_controles)]

resultat_ids = (
    controle_ids.groupby(["Game_ID", "Game_Title_Clean"])
    .agg(
        Nombre_Lignes=("Rank", "size"),
        Ventes_Mondiales=("Global_Sales", "sum")
    )
    .round(2)
)

print(resultat_ids.to_string())

# ============================================================
# 11. CRÉATION DES IDENTIFIANTS DE VERSIONS
# ============================================================

# Une version est définie provisoirement par :
# - le jeu identifié par Game_ID
# - la plateforme sur laquelle il est commercialisé

# On crée un identifiant numérique pour chaque combinaison.
df["Game_Version_ID"] = (
    df.groupby(["Game_ID", "Platform"]).ngroup() + 1
)


# ============================================================
# 12. CONTRÔLE DES IDENTIFIANTS DE VERSIONS
# ============================================================

print("\n=== CONTRÔLE DES GAME_VERSION_ID ===")

print(
    f"Nombre de versions distinctes : "
    f"{df['Game_Version_ID'].nunique()}"
)

print(
    f"Game_Version_ID manquants : "
    f"{df['Game_Version_ID'].isna().sum()}"
)

# Recherche des versions associées à plusieurs lignes
versions_multiples = (
    df.groupby("Game_Version_ID")
    .agg(
        Game_Title=("Game_Title_Clean", "first"),
        Platform=("Platform", "first"),
        Nombre_Lignes=("Rank", "size"),
        Ventes_Mondiales=("Global_Sales", "sum")
    )
)

versions_suspectes = versions_multiples[
    versions_multiples["Nombre_Lignes"] > 1
]

print("\n=== VERSIONS AVEC PLUSIEURS LIGNES ===")
print(versions_suspectes.to_string())

# ============================================================
# 13. IDENTIFICATION DES DOUBLONS POTENTIELS
# ============================================================

# Compter le nombre de lignes pour chaque version de jeu
df["Nombre_Lignes_Version"] = (
    df.groupby("Game_Version_ID")["Rank"]
    .transform("size")
)

# Signaler les versions présentes sur plusieurs lignes
df["Doublon_Potentiel"] = (
    df["Nombre_Lignes_Version"] > 1
)

# Exclure les éditions légitimes de Resident Evil 2
masque_re2_editions = (
    (df["Game_Title_Clean"] == "Resident Evil 2 (1998)")
    & (df["Platform"] == "PS")
)

df.loc[masque_re2_editions, "Doublon_Potentiel"] = False

# ============================================================
# 14. CONTRÔLE DES DOUBLONS POTENTIELS
# ============================================================

print("\n=== CONTRÔLE DES DOUBLONS POTENTIELS ===")

print(
    f"Lignes signalées : "
    f"{df['Doublon_Potentiel'].sum()}"
)

print(
    df.loc[
        df["Doublon_Potentiel"],
        [
            "Rank",
            "Game_Title_Clean",
            "Platform",
            "Year",
            "Game_ID",
            "Game_Version_ID",
            "Global_Sales"
        ]
    ].to_string(index=False)
)



# ============================================================
# 15. CONTRÔLE FINAL DE L'INTÉGRITÉ DES DONNÉES
# ============================================================

print("\n=== CONTRÔLE FINAL DU DATASET ===")

# Recharger le fichier source pour comparer.
df_source = pd.read_csv(FICHIER_SOURCE)

# Vérifier le nombre de lignes.
assert len(df) == len(df_source), "Nombre de lignes modifié !"

# Vérifier que Rank reste unique.
assert df["Rank"].is_unique, "Des Rank sont dupliqués !"

# Vérifier que les identifiants sont renseignés.
assert df["Game_ID"].notna().all(), "Game_ID manquants !"
assert df["Game_Version_ID"].notna().all(), "Game_Version_ID manquants !"

# ------------------------------------------------------------
# 15.1. CONTRÔLE DES COLONNES ORIGINALES HORS YEAR
# ------------------------------------------------------------

# Les années peuvent changer uniquement si elles sont validées.
colonnes_inchangees = [
    colonne
    for colonne in df_source.columns
    if colonne != "Year"
]

pd.testing.assert_frame_equal(
    df[colonnes_inchangees].reset_index(drop=True),
    df_source[colonnes_inchangees].reset_index(drop=True)
)

# ------------------------------------------------------------
# 15.2. CONTRÔLE DES ANNÉES CORRIGÉES
# ------------------------------------------------------------

# Reconstituer les années attendues à partir du fichier source
# et des corrections validées.
annees_attendues = df_source[
    ["Rank", "Name", "Platform", "Year"]
].merge(
    corrections_annees,
    on=["Rank", "Name", "Platform"],
    how="left",
    validate="one_to_one"
)

annees_attendues["Year"] = (
    annees_attendues["Year_Corrected"]
    .combine_first(annees_attendues["Year"])
)

# Vérifier que chaque année correspond à la valeur attendue.
pd.testing.assert_series_equal(
    pd.to_numeric(df["Year"]).reset_index(drop=True),
    pd.to_numeric(
        annees_attendues["Year"]
    ).reset_index(drop=True),
    check_names=False,
    check_dtype=False
)

# ------------------------------------------------------------
# 15.3. CONTRÔLE DES VENTES
# ------------------------------------------------------------

assert abs(
    df["Global_Sales"].sum() - df_source["Global_Sales"].sum()
) < 0.000001, "Le total des ventes a changé !"

# ------------------------------------------------------------
# 15.4. CONTRÔLE DES DOUBLONS POTENTIELS
# ------------------------------------------------------------

# Identifier les versions présentes plusieurs fois.
doublons_attendus = df.duplicated(
    subset=["Game_Version_ID"],
    keep=False
)

# Vérifier que le signalement est cohérent.
assert df["Doublon_Potentiel"].astype(bool).equals(
    doublons_attendus
), "Incohérence dans le signalement des doublons !"

# Afficher le nombre de lignes signalées.
nb_doublons = int(doublons_attendus.sum())

print(f"Lignes signalées comme doublons potentiels : {nb_doublons}")

# ------------------------------------------------------------
# 15.5. BILAN
# ------------------------------------------------------------

print("Nombre de lignes : OK")
print("Unicité des Rank : OK")
print("Identifiants : OK")
print("Colonnes originales hors Year : OK")
print("Années corrigées : OK")
print("Total des ventes : OK")
print("Doublons potentiels : OK")

print("\nTous les contrôles d'intégrité sont validés.")


# ============================================================
# 16. EXPORT DU DATASET ENRICHI
# ============================================================

# Définition du chemin du nouveau fichier
FICHIER_SORTIE = BASE_DIR / "data" / "vgsales_enriched.csv"

# Enregistrement sans ajouter l'index Pandas
df.to_csv(FICHIER_SORTIE, index=False)

print("\n=== EXPORT DU DATASET ENRICHI ===")

print(f"Fichier créé : {FICHIER_SORTIE.name}")
print(f"Nombre de lignes : {len(df)}")
print(f"Nombre de colonnes : {len(df.columns)}")

print("\nExport terminé avec succès.")

# ============================================================
# 17. VÉRIFICATION DU FICHIER EXPORTÉ
# ============================================================

# Recharger le CSV qui vient d'être créé
df_export = pd.read_csv(FICHIER_SORTIE)

print("\n=== VÉRIFICATION DU FICHIER EXPORTÉ ===")

# Comparer le nombre de lignes et de colonnes
assert df_export.shape == df.shape, (
    "Les dimensions du fichier exporté sont incorrectes !"
)

# Vérifier les identifiants
assert df_export["Game_ID"].notna().all()
assert df_export["Game_Version_ID"].notna().all()

# Vérifier les ventes mondiales
assert abs(
    df_export["Global_Sales"].sum() - df["Global_Sales"].sum()
) < 0.000001

# Vérifier que les doublons potentiels sont conservés à l'export.
assert df_export["Doublon_Potentiel"].astype(bool).sum() == (
    df["Doublon_Potentiel"].astype(bool).sum()
), "Le nombre de doublons potentiels a changé lors de l'export !"

# Vérifier que les colonnes et les valeurs sont conservées
pd.testing.assert_frame_equal(
    df_export,
    df,
    check_dtype=False
)

print(f"Lignes : {len(df_export)}")
print(f"Colonnes : {len(df_export.columns)}")
print(f"Ventes mondiales : {df_export['Global_Sales'].sum():.2f} M")
print("Identifiants : OK")
print("Doublons potentiels : OK")
print("Comparaison avec le DataFrame : OK")

print("\nLe fichier enrichi est validé.")


# ============================================================
# 18. AUDIT UNIQUE DES REGROUPEMENTS SUSPECTS
# ============================================================
# Audit non destructif : ne modifie ni les Game_ID ni les ventes.
# Les cas confirmés peuvent être exclus du classement, pas du dataset.

# ============================================================
# JEUX DÉJÀ VÉRIFIÉS ET VALIDÉS
# ============================================================

TITRES_VALIDES = {
    "Resident Evil 2 (1998)",
    "God of War Collection",
    "Final Fantasy III (Remake 3D)",
    "Resident Evil (Remake 2002)",
    "Terraria",
    "Xenoblade Chronicles",
    "Tales of the Abyss",
    "Breath of Fire III",
    "Sniper Elite",  # PC, PS2, Xbox 2005 + Wii 2010 : regroupement validé
    "Sakura Wars: So Long, My Love",
    "Resident Evil Director's Cut",
    "Bookworm",
    "Chaos;Head Noah",
}

audit = (
    df.groupby(["Game_ID", "Game_Title_Clean"], dropna=False)
    .agg(
        Nb_Lignes=("Rank", "size"),
        Nb_Plateformes=("Platform", "nunique"),
        Annee_Min=("Year", "min"),
        Annee_Max=("Year", "max"),
        Ventes_M=("Global_Sales", "sum"),
    )
    .reset_index()
)
audit["Ecart_Annees"] = audit["Annee_Max"] - audit["Annee_Min"]
suspects = audit.loc[
    (audit["Nb_Lignes"] > 1)
    & (audit["Ecart_Annees"] >= 5)
    & (~audit["Game_Title_Clean"].isin(TITRES_VALIDES))
].sort_values(["Ventes_M", "Ecart_Annees"], ascending=[False, False])

print("\n=== AUDIT UNIQUE DES GAME_ID ===")
print(f"Regroupements suspects : {len(suspects)}")
print(suspects.head(20).round(2).to_string(index=False))


# ============================================================
# DIAGNOSTIC PONCTUEL D'UN JEU
# ============================================================

# Exemple : --jeu "Myst"
# Recherche exacte, sans inclure les titres similaires.

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Regroupement des jeux et audit"
    )

    parser.add_argument(
        "--jeu",
        help="Titre exact du jeu à inspecter"
    )

    args = parser.parse_args()

    if args.jeu:

        # Recherche du titre exact, sans distinction de casse
        titre_recherche = args.jeu.strip().casefold()

        selection = df.loc[
            df["Name"].astype("string").str.casefold().eq(titre_recherche)
            | df["Game_Title_Clean"].astype("string").str.casefold().eq(titre_recherche)
        ].copy()

        colonnes = [
            "Rank", "Name", "Platform", "Year",
            "Publisher", "Genre", "Global_Sales",
            "Game_Title_Clean", "Game_ID"
        ]

        print(f"\n=== DIAGNOSTIC : {args.jeu} ===")

        if selection.empty:
            print("Aucun jeu trouvé avec ce titre exact.")
        else:
            print(
                selection[colonnes]
                .sort_values(["Year", "Platform"])
                .to_string(index=False)
            )

            print(f"\nNombre de lignes : {len(selection)}")
            print(f"Nombre de Game_ID : {selection['Game_ID'].nunique()}")
            print(f"Ventes mondiales : {selection['Global_Sales'].sum():.2f} M")

