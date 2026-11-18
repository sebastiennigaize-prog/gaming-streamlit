
import pandas as pd
from pathlib import Path
from datetime import datetime
from shutil import copy2

# ==================================================
# 1. CHEMINS DES FICHIERS
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DOSSIER_DATA = BASE_DIR / "data"

FICHIER_SUIVI = DOSSIER_DATA / "annees_a_verifier.csv"
FICHIER_CORRECTIONS = DOSSIER_DATA / "corrections_validees.csv"
DOSSIER_BACKUP = DOSSIER_DATA / "backups"


# ==================================================
# 2. CHARGEMENT DES DONNÉES
# ==================================================

df = pd.read_csv(FICHIER_SUIVI)
corrections = pd.read_csv(FICHIER_CORRECTIONS)

# Conversion des types de données
df["Year_Corrected"] = pd.to_numeric(
    df["Year_Corrected"],
    errors="coerce"
).astype("Int64")

df["Source_Year"] = df["Source_Year"].astype("string")
df["Statut_Verification"] = (
    df["Statut_Verification"].astype("string")
)

corrections["Year_Corrected"] = pd.to_numeric(
    corrections["Year_Corrected"],
    errors="raise"
).astype("Int64")

print(f"Lignes du fichier de suivi : {len(df)}")
print(f"Corrections proposées : {len(corrections)}")


# ==================================================
# 3. VÉRIFICATION DU FICHIER DE CORRECTIONS
# ==================================================

colonnes_obligatoires = [
    "Rank",
    "Name",
    "Platform",
    "Year_Corrected",
    "Source_Year"
]

for colonne in colonnes_obligatoires:
    if colonne not in corrections.columns:
        raise ValueError(
            f"Colonne manquante : {colonne}"
        )

if corrections[colonnes_obligatoires].isna().any().any():
    raise ValueError(
        "Certaines corrections contiennent des valeurs manquantes."
    )

if corrections["Rank"].duplicated().any():
    raise ValueError(
        "Le fichier de corrections contient des Rank en double."
    )


# ==================================================
# 4. IDENTIFICATION DES CORRECTIONS À APPLIQUER
# ==================================================

a_appliquer = []

for correction in corrections.to_dict("records"):

    masque = (
        (df["Rank"] == correction["Rank"]) &
        (df["Name"] == correction["Name"]) &
        (df["Platform"] == correction["Platform"])
    )

    # Chaque correction doit correspondre à une seule ligne
    if masque.sum() != 1:
        raise ValueError(
            f"Correspondance introuvable ou multiple : "
            f"{correction['Name']} ({correction['Platform']})"
        )

    ligne = df.loc[masque].iloc[0]

    # Ne jamais écraser une correction déjà enregistrée
    if (
        ligne["Statut_Verification"] == "Verifie"
        or pd.notna(ligne["Year_Corrected"])
    ):
        print(
            f"Déjà renseigné, ignoré : "
            f"{correction['Name']} ({correction['Platform']})"
        )
        continue

    a_appliquer.append(correction)

print(f"\nNouvelles corrections : {len(a_appliquer)}")


# ==================================================
# 5. APPLICATION DES CORRECTIONS EN MÉMOIRE
# ==================================================

for correction in a_appliquer:

    masque = (
        (df["Rank"] == correction["Rank"]) &
        (df["Name"] == correction["Name"]) &
        (df["Platform"] == correction["Platform"])
    )

    df.loc[masque, "Year_Corrected"] = (
        correction["Year_Corrected"]
    )

    df.loc[masque, "Source_Year"] = (
        correction["Source_Year"]
    )

    df.loc[masque, "Statut_Verification"] = "Verifie"

    print(
        f"Corrigé : {correction['Name']} "
        f"({correction['Platform']}) "
        f"-> {correction['Year_Corrected']}"
    )


# ==================================================
# 6. SAUVEGARDE ET ENREGISTREMENT
# ==================================================

if a_appliquer:

    DOSSIER_BACKUP.mkdir(exist_ok=True)

    date_backup = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    FICHIER_BACKUP = (
        DOSSIER_BACKUP /
        f"annees_a_verifier_{date_backup}.csv"
    )

    # Sauvegarder le fichier avant modification
    copy2(FICHIER_SUIVI, FICHIER_BACKUP)

    # Enregistrer les corrections
    df.to_csv(FICHIER_SUIVI, index=False)

    print("\nSauvegarde créée :", FICHIER_BACKUP.name)
    print("Fichier de suivi mis à jour.")

else:
    print("\nAucune nouvelle correction à enregistrer.")


# ==================================================
# 7. BILAN FINAL
# ==================================================

nb_verifies = (
    df["Statut_Verification"] == "Verifie"
).sum()

print("\nBILAN DES CORRECTIONS")
print("=" * 45)

print(f"Années vérifiées : {nb_verifies}")
print(f"Années restant à vérifier : {len(df) - nb_verifies}")


# ==================================================
# 8. DIAGNOSTIC RESIDENT EVIL
# ==================================================

print("\n=== VERIFICATION RESIDENT EVIL ===")

# Rechercher les deux jeux dans le fichier de suivi
resident_evil = df[
    df["Rank"].isin([326, 8299])
]

# Afficher les informations de suivi
print(resident_evil.to_string(index=False))

print(
    "\nNombre de lignes trouvées :",
    len(resident_evil)
)

