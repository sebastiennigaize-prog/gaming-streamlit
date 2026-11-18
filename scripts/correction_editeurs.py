
from pathlib import Path
from datetime import datetime
import shutil

import pandas as pd


# ============================================================
# 1. CHEMINS
# ============================================================

FICHIER_SUIVI = Path("data/editeurs_a_verifier.csv")
FICHIER_CORRECTIONS = Path("data/corrections_editeurs.csv")
DOSSIER_BACKUP = Path("data/backups")


# ============================================================
# 2. CHARGEMENT DES FICHIERS
# ============================================================

suivi = pd.read_csv(FICHIER_SUIVI)
corrections = pd.read_csv(FICHIER_CORRECTIONS)

# Colonnes contenant du texte
colonnes_texte = [
    "Publisher_Corrected",
    "Source_Publisher",
    "Statut_Verification",
    "Motif_Exclusion",
]

for colonne in colonnes_texte:
    suivi[colonne] = suivi[colonne].astype("string")

corrections["Publisher_Corrected"] = (
    corrections["Publisher_Corrected"].astype("string")
)
corrections["Source_Publisher"] = (
    corrections["Source_Publisher"].astype("string")
)


# ============================================================
# 3. VERIFICATIONS AVANT MODIFICATION
# ============================================================

if len(suivi) != 261:
    raise ValueError("Le fichier de suivi ne contient pas 261 lignes.")

if len(corrections) != 255:
    raise ValueError("Le fichier ne contient pas 255 corrections.")

if suivi["Rank"].duplicated().any():
    raise ValueError("Doublons Rank dans le fichier de suivi.")

if corrections["Rank"].duplicated().any():
    raise ValueError("Doublons Rank dans les corrections.")

if corrections[
    ["Rank", "Name", "Platform",
     "Publisher_Corrected", "Source_Publisher"]
].isna().any().any():
    raise ValueError("Une correction contient une valeur manquante.")

# Vérification des correspondances exactes
comparaison = corrections.merge(
    suivi[["Rank", "Name", "Platform", "Statut_Verification"]],
    on="Rank",
    how="left",
    suffixes=("_correction", "_suivi"),
    indicator=True,
    validate="one_to_one",
)

erreurs = comparaison[
    (comparaison["_merge"] != "both")
    | (comparaison["Name_correction"] != comparaison["Name_suivi"])
    | (comparaison["Platform_correction"] != comparaison["Platform_suivi"])
]

if not erreurs.empty:
    raise ValueError(
        "Certaines corrections ne correspondent pas au suivi."
    )

if (comparaison["Statut_Verification"] == "Exclu").any():
    raise ValueError("Une correction concerne un jeu exclu.")

if (suivi["Statut_Verification"] == "Exclu").sum() != 6:
    raise ValueError("Le suivi ne contient pas exactement 6 exceptions.")


# ============================================================
# 4. SAUVEGARDE
# ============================================================

DOSSIER_BACKUP.mkdir(parents=True, exist_ok=True)

horodatage = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

backup = DOSSIER_BACKUP / (
    f"editeurs_a_verifier_{horodatage}.csv"
)

shutil.copy2(FICHIER_SUIVI, backup)

print(f"Sauvegarde creee : {backup}")


# ============================================================
# 5. APPLICATION DES CORRECTIONS
# ============================================================

# Indexation par Rank pour retrouver les bonnes lignes
suivi = suivi.set_index("Rank")
corrections = corrections.set_index("Rank")

# Report des éditeurs et des sources
suivi.loc[
    corrections.index, "Publisher_Corrected"
] = corrections["Publisher_Corrected"]

suivi.loc[
    corrections.index, "Source_Publisher"
] = corrections["Source_Publisher"]

# Les 255 jeux corrigés deviennent vérifiés
suivi.loc[
    corrections.index, "Statut_Verification"
] = "Verifie"

# Suppression des éventuels anciens motifs d'exclusion
suivi.loc[
    corrections.index, "Motif_Exclusion"
] = pd.NA

suivi = suivi.reset_index()


# ============================================================
# 6. CONTROLE FINAL
# ============================================================

nb_verifies = (suivi["Statut_Verification"] == "Verifie").sum()
nb_exclus = (suivi["Statut_Verification"] == "Exclu").sum()
nb_restants = (suivi["Statut_Verification"] == "A_verifier").sum()

if (nb_verifies, nb_exclus, nb_restants) != (255, 6, 0):
    raise ValueError(
        "Bilan incoherent : "
        f"{nb_verifies} verifies, "
        f"{nb_exclus} exclus, "
        f"{nb_restants} restants."
    )


# ============================================================
# 7. ENREGISTREMENT
# ============================================================

suivi.to_csv(
    FICHIER_SUIVI,
    index=False,
    encoding="utf-8-sig",
)

print()
print("Corrections appliquees :", nb_verifies)
print("Exceptions conservees :", nb_exclus)
print("Jeux restant a verifier :", nb_restants)
print("Fichier de suivi mis a jour.")
