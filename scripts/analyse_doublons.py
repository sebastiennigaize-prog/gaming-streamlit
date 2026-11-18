
import pandas as pd
from pathlib import Path

# ==================================================
# 1. CHARGEMENT DU DATASET
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent
FICHIER_SOURCE = BASE_DIR / "data" / "vgsales.csv"

df = pd.read_csv(FICHIER_SOURCE)

print(f"Nombre total de lignes : {len(df)}")


# ==================================================
# 2. DÉFINITION DES COLONNES À COMPARER
# ==================================================

# Comparer toutes les colonnes sauf Rank
colonnes_comparaison = [
    colonne for colonne in df.columns
    if colonne != "Rank"
]


# ==================================================
# 3. IDENTIFICATION DES DOUBLONS
# ==================================================

# Identifier les lignes identiques sur toutes
# les colonnes de comparaison
doublons_exacts = df[
    df.duplicated(
        subset=colonnes_comparaison,
        keep=False
    )
].copy()

# Trier pour faciliter la lecture
doublons_exacts = doublons_exacts.sort_values(
    by=["Name", "Platform", "Rank"]
)


# ==================================================
# 4. AFFICHAGE DU BILAN
# ==================================================

print("\nDOUBLONS IDENTIQUES HORS RANK")
print("=" * 50)

print(f"Lignes concernées : {len(doublons_exacts)}")

# Nombre de lignes excédentaires si l'on conserve
# une seule ligne par groupe identique
nb_excedentaires = df.duplicated(
    subset=colonnes_comparaison
).sum()

print(f"Lignes potentiellement redondantes : {nb_excedentaires}")


# ==================================================
# 5. AFFICHAGE DES LIGNES CONCERNÉES
# ==================================================

if doublons_exacts.empty:
    print("\nAucun doublon identique trouvé.")
else:
    print("\nLignes concernées :")
    print(doublons_exacts.to_string(index=False))


# ==================================================
# 6. CONCLUSION
# ==================================================

print("\nAucune ligne n'a été supprimée.")
print("Le dataset original reste inchangé.")
