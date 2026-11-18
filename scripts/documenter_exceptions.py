
import pandas as pd
from pathlib import Path

# 1. Chemin du fichier de suivi
fichier = Path("data/annees_a_verifier.csv")

# 2. Chargement des données
df = pd.read_csv(fichier)

# 3. Dictionnaire des exceptions
# Rank : (statut, motif)
exceptions = {
    14315: (
        "Annule",
        "Version Xbox 360 annulée"
    ),
    15868: (
        "Annule",
        "Version Nintendo DS annulée"
    ),
    16201: (
        "Incoherence",
        "Jeu sorti sur PSP, pas sur Xbox 360"
    ),
    16232: (
        "Annule",
        "Projet abandonné avant commercialisation"
    ),
    16249: (
        "Incoherence",
        "Confusion entre édition PS3 et Re-appearance sur Xbox 360"
    )
}

# 4. Création de la colonne explicative
if "Motif_Exclusion" not in df.columns:
    df["Motif_Exclusion"] = ""

# 5. Vérification des identifiants
ranks_attendus = set(exceptions)
ranks_presents = set(df["Rank"])

if not ranks_attendus.issubset(ranks_presents):
    raise ValueError("Certains Rank sont absents du fichier")

# 6. Mise à jour des cinq entrées
for rank, (statut, motif) in exceptions.items():
    masque = df["Rank"] == rank

    df.loc[masque, "Statut_Verification"] = statut
    df.loc[masque, "Motif_Exclusion"] = motif

# 7. Enregistrement
df.to_csv(fichier, index=False, encoding="utf-8-sig")

# 8. Contrôle final
print("Exceptions documentées :")
print(
    df.loc[
        df["Rank"].isin(exceptions),
        ["Rank", "Name", "Platform",
         "Year_Corrected", "Statut_Verification",
         "Motif_Exclusion"]
    ].to_string(index=False)
)

print("\nRépartition des statuts :")
print(df["Statut_Verification"].value_counts())
