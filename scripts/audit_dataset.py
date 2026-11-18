
import pandas as pd
from pathlib import Path

# Rechercher le dataset original
fichiers = list(Path(".").rglob("vgsales.csv"))
fichiers = [
    f for f in fichiers
    if ".venv" not in f.parts
]

if len(fichiers) != 1:
    print("Fichiers vgsales.csv trouvés :")
    for f in fichiers:
        print(f)
    raise SystemExit("Impossible d'identifier un fichier unique.")

fichier = fichiers[0]
df = pd.read_csv(fichier)

print(f"\nFICHIER ANALYSÉ : {fichier}")
print(f"Nombre de lignes : {len(df)}")
print(f"Nombre de colonnes : {len(df.columns)}")

print("\n=== VALEURS MANQUANTES PAR COLONNE ===")

for colonne in df.columns:
    serie = df[colonne]
    nan = serie.isna().sum()

    # Repérer les valeurs textuelles non renseignées
    texte = serie.astype("string").str.strip().str.lower()

    inconnus = texte.isin([
        "unknown", "inconnu", "not available",
        "n/a", "null", "none", "?"
    ]).fillna(False).sum()

    espaces = (
        serie.notna() &
        texte.eq("").fillna(False)
    ).sum()

    total = nan + inconnus + espaces

    print(
        f"{colonne:18} "
        f"NaN={nan:5} | "
        f"Unknown/autres={inconnus:5} | "
        f"Vides={espaces:5} | "
        f"Total={total:5} | "
        f"{total / len(df) * 100:.2f}%"
    )

print("\n=== CONTRÔLE YEAR ===")
if "Year" in df.columns:
    print("Années manquantes :", df["Year"].isna().sum())

print("\n=== CONTRÔLE PUBLISHER ===")
if "Publisher" in df.columns:
    p = df["Publisher"]
    print("NaN :", p.isna().sum())
    print(
        "Unknown :",
        p.astype("string").str.strip()
        .str.lower().eq("unknown").sum()
    )

print("\n=== DOUBLONS ===")
print("Lignes totalement identiques :", df.duplicated().sum())
print("Rank dupliqués :", df["Rank"].duplicated().sum()
      if "Rank" in df.columns else "Colonne absente")
