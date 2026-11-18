
import pandas as pd
from pathlib import Path

# ==================================================
# 1. CHARGEMENT DU FICHIER DE SUIVI
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent
FICHIER_SUIVI = BASE_DIR / "data" / "annees_a_verifier.csv"

df = pd.read_csv(FICHIER_SUIVI)

print(f"Nombre total de lignes à examiner : {len(df)}")


# ==================================================
# 2. SÉLECTION DES JEUX NON VÉRIFIÉS
# ==================================================

jeux_restants = df[
    df["Statut_Verification"] != "Verifie"
].copy()

print(f"Jeux restant à vérifier : {len(jeux_restants)}")


# ==================================================
# 3. SÉLECTION DES ANNÉES CANDIDATES UNIQUES
# ==================================================

jeux_prioritaires = jeux_restants[
    jeux_restants["Nb_Annees_Candidates"] == 1
].copy()

print(
    "Jeux avec une seule année candidate :",
    len(jeux_prioritaires)
)


# ==================================================
# 4. AFFICHAGE DES 20 PREMIERS
# ==================================================

colonnes = [
    "Rank",
    "Name",
    "Platform",
    "Publisher",
    "Annees_Candidates"
]

print("\n20 premiers jeux à rechercher :")

print(
    jeux_prioritaires[colonnes]
    .head(20)
    .to_string(index=False)
)


# ==================================================
# 5. BILAN
# ==================================================

print("\nBILAN")
print("=" * 45)

print(
    "Lignes vérifiées :",
    (df["Statut_Verification"] == "Verifie").sum()
)

print("Lignes restant à vérifier :", len(jeux_restants))
