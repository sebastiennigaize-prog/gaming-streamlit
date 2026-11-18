from pathlib import Path
from datetime import datetime

import pandas as pd


# ============================================================
# 1. CHEMINS DES FICHIERS
# ============================================================

FICHIER = Path("data/editeurs_a_verifier.csv")
DOSSIER_BACKUP = Path("data/backups")

DOSSIER_BACKUP.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. EXCEPTIONS IDENTIFIÉES
# ============================================================

EXCEPTIONS = {
    2224: "Plateforme GBA incoherente",
    7955: "Identification du jeu incertaine",
    14315: "Version Xbox 360 annulee",
    15868: "Titre et plateforme incoherents",
    16201: "Version Xbox 360 non confirmee",
    16232: "Jeu annule avant commercialisation",
}


# ============================================================
# 3. CHARGEMENT ET VERIFICATIONS
# ============================================================

# Chargement du fichier de suivi
df = pd.read_csv(FICHIER)

# Conversion explicite des colonnes textuelles
# pour éviter les erreurs de type float64
df["Publisher_Corrected"] = df["Publisher_Corrected"].astype("string")
df["Source_Publisher"] = df["Source_Publisher"].astype("string")
df["Statut_Verification"] = df["Statut_Verification"].astype("string")
df["Motif_Exclusion"] = df["Motif_Exclusion"].astype("string")

# Vérification des Rank
ranks_absents = set(EXCEPTIONS) - set(df["Rank"])

if ranks_absents:
    raise ValueError(
        f"Ranks absents du fichier : {sorted(ranks_absents)}"
    )

if df["Rank"].duplicated().any():
    raise ValueError("Des Rank sont en doublon.")


# ============================================================
# 4. SAUVEGARDE AVANT MODIFICATION
# ============================================================

horodatage = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

backup = DOSSIER_BACKUP / (
    f"editeurs_a_verifier_{horodatage}.csv"
)

df.to_csv(backup, index=False, encoding="utf-8-sig")

print(f"Sauvegarde creee : {backup}")


# ============================================================
# 5. DOCUMENTATION DES EXCEPTIONS
# ============================================================

for rank, motif in EXCEPTIONS.items():

    masque = df["Rank"] == rank

    df.loc[masque, "Statut_Verification"] = "Exclu"
    df.loc[masque, "Motif_Exclusion"] = motif

    df.loc[masque, "Publisher_Corrected"] = None
    df.loc[masque, "Source_Publisher"] = None


# ============================================================
# 6. ENREGISTREMENT
# ============================================================

df.to_csv(FICHIER, index=False, encoding="utf-8-sig")

print(f"Exceptions documentees : {len(EXCEPTIONS)}")
print("Fichier de suivi mis a jour.")
