
import pandas as pd
from pathlib import Path

# ==================================================
# 1. CHARGEMENT DU DATASET ORIGINAL
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent
FICHIER_SOURCE = BASE_DIR / "data" / "vgsales.csv"

df = pd.read_csv(FICHIER_SOURCE)

# ==================================================
# 2. JEUX À CONTRÔLER
# ==================================================

jeux_a_controler = [
    "Final Fantasy VII",
    "Pokemon Red/Pokemon Blue",
    "Sonic the Hedgehog"
]

# ==================================================
# 3. RECHERCHE DANS LE DATASET
# ==================================================

resultat = df[
    df["Name"].isin(jeux_a_controler)
].copy()

# ==================================================
# 4. AFFICHAGE DES RÉSULTATS
# ==================================================

print("AUDIT DES ANNÉES DE SORTIE")
print("=" * 55)

print(
    resultat[
        ["Name", "Platform", "Year"]
    ]
    .sort_values(["Name", "Platform"])
    .to_string(index=False)
)

print("\nNombre de lignes trouvées :", len(resultat))
