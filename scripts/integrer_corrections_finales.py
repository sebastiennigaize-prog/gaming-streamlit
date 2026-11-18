
from pathlib import Path
from datetime import datetime
import os
import shutil

import pandas as pd


# ============================================================
# 1. CHEMINS DES FICHIERS
# ============================================================

FICHIER_ORIGINAL = Path("data/vgsales.csv")
FICHIER_ANNEES = Path("data/annees_a_verifier.csv")
FICHIER_EDITEURS = Path("data/editeurs_a_verifier.csv")
DOSSIER_BACKUP = Path("data/backups")

COLONNES_ORIGINALES = [
    "Rank", "Name", "Platform", "Year", "Genre",
    "Publisher", "NA_Sales", "EU_Sales",
    "JP_Sales", "Other_Sales", "Global_Sales"
]


# ============================================================
# 2. CHARGEMENT DES DONNEES
# ============================================================

original = pd.read_csv(FICHIER_ORIGINAL)
annees = pd.read_csv(FICHIER_ANNEES)
editeurs = pd.read_csv(FICHIER_EDITEURS)

resultat = original.copy()

print("Dataset original :", original.shape)


# ============================================================
# 3. CONTROLES PREALABLES
# ============================================================

if original.shape != (16598, 11):
    raise ValueError("Dimensions inattendues du dataset.")

if original.columns.tolist() != COLONNES_ORIGINALES:
    raise ValueError("Les colonnes originales ont change.")

for nom, df in [
    ("Original", original),
    ("Annees", annees),
    ("Editeurs", editeurs),
]:
    if df["Rank"].isna().any():
        raise ValueError(f"Rank manquant dans {nom}.")

    if df["Rank"].duplicated().any():
        raise ValueError(f"Rank en doublon dans {nom}.")

if len(annees) != 271 or len(editeurs) != 261:
    raise ValueError("Nombre de lignes inattendu dans les suivis.")

annees_valides = annees[
    annees["Statut_Verification"] == "Verifie"
].copy()

editeurs_valides = editeurs[
    editeurs["Statut_Verification"] == "Verifie"
].copy()

if len(annees_valides) != 266:
    raise ValueError("Il faut exactement 266 annees verifiees.")

if len(editeurs_valides) != 255:
    raise ValueError("Il faut exactement 255 editeurs verifies.")

if annees["Statut_Verification"].value_counts().to_dict() != {
    "Verifie": 266,
    "Annule": 3,
    "Incoherence": 2,
}:
    raise ValueError("Statuts des annees inattendus.")

if editeurs["Statut_Verification"].value_counts().to_dict() != {
    "Verifie": 255,
    "Exclu": 6,
}:
    raise ValueError("Statuts des editeurs inattendus.")

if annees_valides[
    ["Year_Corrected", "Source_Year"]
].isna().any().any():
    raise ValueError("Annees ou sources manquantes.")

if editeurs_valides[
    ["Publisher_Corrected", "Source_Publisher"]
].isna().any().any():
    raise ValueError("Editeurs ou sources manquants.")


# ============================================================
# 4. VERIFICATION DES CORRESPONDANCES
# ============================================================

def verifier_correspondances(suivi, nom):
    comparaison = suivi[["Rank", "Name", "Platform"]].merge(
        original[["Rank", "Name", "Platform"]],
        on="Rank",
        how="left",
        suffixes=("_suivi", "_original"),
        indicator=True,
        validate="one_to_one",
    )

    erreurs = comparaison[
        (comparaison["_merge"] != "both")
        | (
            comparaison["Name_suivi"]
            != comparaison["Name_original"]
        )
        | (
            comparaison["Platform_suivi"]
            != comparaison["Platform_original"]
        )
    ]

    if not erreurs.empty:
        print(erreurs.to_string(index=False))
        raise ValueError(
            f"Correspondances incorrectes : {nom}"
        )


verifier_correspondances(annees, "annees")
verifier_correspondances(editeurs, "editeurs")


# ============================================================
# 5. VERIFICATION DES VALEURS A CORRIGER
# ============================================================

original_index = original.set_index("Rank")

# Les annees corrigees doivent etre des entiers valides
annees_numeriques = pd.to_numeric(
    annees_valides["Year_Corrected"],
    errors="coerce",
)

if (
    annees_numeriques.isna().any()
    or (annees_numeriques % 1 != 0).any()
    or (annees_numeriques < 1950).any()
    or (annees_numeriques > 2026).any()
):
    raise ValueError("Certaines annees corrigees sont invalides.")

# On corrige uniquement des annees initialement manquantes
if original_index.loc[
    annees_valides["Rank"], "Year"
].notna().any():
    raise ValueError("Une annee originale est deja renseignee.")

# On corrige uniquement des editeurs NaN ou Unknown
editeurs_originaux = original_index.loc[
    editeurs_valides["Rank"], "Publisher"
]

masque_invalide = (
    editeurs_originaux.notna()
    & editeurs_originaux.astype("string")
        .str.strip().ne("Unknown").fillna(False)
)

if masque_invalide.any():
    raise ValueError(
        "Un editeur original contient deja une valeur valide."
    )


# ============================================================
# 6. APPLICATION EN MEMOIRE
# ============================================================

resultat = resultat.set_index("Rank")

for rank, annee in zip(
    annees_valides["Rank"],
    annees_numeriques.astype(int),
):
    resultat.at[rank, "Year"] = int(annee)

for rank, editeur in zip(
    editeurs_valides["Rank"],
    editeurs_valides["Publisher_Corrected"],
):
    resultat.at[rank, "Publisher"] = editeur

resultat = resultat.reset_index()


# ============================================================
# 7. CONTROLES FINAUX AVANT ENREGISTREMENT
# ============================================================

if resultat.shape != original.shape:
    raise ValueError("Les dimensions ont change.")

if resultat.columns.tolist() != original.columns.tolist():
    raise ValueError("Les colonnes ont change.")

colonnes_inchangees = [
    col for col in original.columns
    if col not in ["Year", "Publisher"]
]

pd.testing.assert_frame_equal(
    original[colonnes_inchangees],
    resultat[colonnes_inchangees],
    check_dtype=True,
)

# Les annees restantes correspondent aux cinq exceptions
if resultat["Year"].isna().sum() != 5:
    raise ValueError("Nombre d'annees manquantes incorrect.")

# Les editeurs restants correspondent aux six exceptions
editeurs_manquants = (
    resultat["Publisher"].isna()
    | resultat["Publisher"].astype("string")
        .str.strip().eq("Unknown").fillna(False)
)

if editeurs_manquants.sum() != 6:
    raise ValueError("Nombre d'editeurs manquants incorrect.")

# Verifier que les valeurs appliquees sont exactes
resultat_index = resultat.set_index("Rank")

for rank, annee in zip(
    annees_valides["Rank"],
    annees_numeriques.astype(int),
):
    if resultat_index.at[rank, "Year"] != annee:
        raise ValueError(f"Annee incorrecte pour Rank {rank}")

for rank, editeur in zip(
    editeurs_valides["Rank"],
    editeurs_valides["Publisher_Corrected"],
):
    if resultat_index.at[rank, "Publisher"] != editeur:
        raise ValueError(f"Editeur incorrect pour Rank {rank}")


# ============================================================
# 8. SAUVEGARDE ET ENREGISTREMENT
# ============================================================

DOSSIER_BACKUP.mkdir(parents=True, exist_ok=True)

horodatage = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

backup = DOSSIER_BACKUP / f"vgsales_{horodatage}.csv"

# Ecriture dans un fichier temporaire
temporaire = FICHIER_ORIGINAL.with_name(
    "vgsales_temp_validation.csv"
)

try:
    resultat.to_csv(
        temporaire,
        index=False,
        encoding="utf-8",
    )

    # Verification du CSV relu avant remplacement
    verification = pd.read_csv(temporaire)

    pd.testing.assert_frame_equal(
        resultat,
        verification,
        check_dtype=False,
    )

    # Sauvegarde de l'original, sans le modifier
    shutil.copy2(FICHIER_ORIGINAL, backup)

    # Remplacement seulement apres tous les controles
    os.replace(temporaire, FICHIER_ORIGINAL)

except Exception:
    if temporaire.exists():
        temporaire.unlink()
    raise


# ============================================================
# 9. BILAN
# ============================================================

print()
print("Integration terminee avec succes.")
print("Sauvegarde :", backup)
print("Annees corrigees :", len(annees_valides))
print("Editeurs corriges :", len(editeurs_valides))
print("Annees encore manquantes :", 5)
print("Editeurs encore non renseignes :", 6)
print("Dimensions finales :", resultat.shape)
print("Autres colonnes inchangees : OUI")
