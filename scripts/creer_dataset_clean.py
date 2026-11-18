
import pandas as pd
from pathlib import Path

# ============================================================
# 1. CHEMINS
# ============================================================

source = Path("data/vgsales.csv")
destination = Path("data/vgsales_clean.csv")

# ============================================================
# 2. CHARGEMENT
# ============================================================

df = pd.read_csv(source)

print("Nombre de lignes avant :", len(df))

# ============================================================
# 3. VERIFICATION DU DOUBLON
# ============================================================

colonnes = [c for c in df.columns if c != "Rank"]

ligne_a_exclure = df[df["Rank"] == 15002]
ligne_a_conserver = df[df["Rank"] == 15000]

if len(ligne_a_exclure) != 1 or len(ligne_a_conserver) != 1:
    raise ValueError("Les deux Rank attendus sont introuvables.")

# Comparaison de toutes les colonnes sauf Rank
pd.testing.assert_frame_equal(
    ligne_a_exclure[colonnes].reset_index(drop=True),
    ligne_a_conserver[colonnes].reset_index(drop=True),
)

# ============================================================
# 4. EXCLUSION DU DOUBLON
# ============================================================

df_clean = df[df["Rank"] != 15002].copy()

# ============================================================
# 5. CONTROLES
# ============================================================

if len(df_clean) != 16597:
    raise ValueError("Nombre de lignes incorrect.")

if df_clean.duplicated(subset=colonnes).any():
    raise ValueError("Il reste des doublons exacts.")

if df_clean["Rank"].duplicated().any():
    raise ValueError("Doublons Rank detectes.")

if df_clean["Year"].isna().sum() != 5:
    raise ValueError("Nombre d'annees manquantes inattendu.")

editeurs_manquants = (
    df_clean["Publisher"].isna()
    | df_clean["Publisher"].astype("string")
      .str.strip().eq("Unknown").fillna(False)
)

if editeurs_manquants.sum() != 6:
    raise ValueError("Nombre d'editeurs manquants inattendu.")

# ============================================================
# 6. ENREGISTREMENT
# ============================================================

df_clean.to_csv(destination, index=False, encoding="utf-8")

# Relecture pour verifier le fichier enregistre
verification = pd.read_csv(destination)

pd.testing.assert_frame_equal(
    df_clean.reset_index(drop=True),
    verification,
    check_dtype=False,
)

# ============================================================
# 7. BILAN
# ============================================================

print("Nombre de lignes apres :", len(df_clean))
print("Doublons exacts restants :",
      df_clean.duplicated(subset=colonnes).sum())
print("Ventes mondiales avant :",
      round(df["Global_Sales"].sum(), 2), "millions")
print("Ventes mondiales apres :",
      round(df_clean["Global_Sales"].sum(), 2), "millions")
print("Fichier cree :", destination)
