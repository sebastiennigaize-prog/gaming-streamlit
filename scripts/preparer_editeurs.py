
import pandas as pd
from pathlib import Path

# 1. Charger le dataset original
df = pd.read_csv("data/vgsales.csv")

# 2. Repérer les éditeurs absents ou inconnus
publisher = df["Publisher"].astype("string").str.strip()

masque = (
    publisher.isna()
    | publisher.str.lower().eq("unknown").fillna(False)
)

# 3. Extraire uniquement les jeux concernés
editeurs = df.loc[masque].copy()

# 4. Ajouter les colonnes de suivi
editeurs["Publisher_Corrected"] = pd.NA
editeurs["Source_Publisher"] = pd.NA
editeurs["Statut_Verification"] = "A_verifier"
editeurs["Motif_Exclusion"] = pd.NA

# 5. Créer le fichier de suivi
destination = Path("data/editeurs_a_verifier.csv")

if destination.exists():
    raise FileExistsError(
        f"Le fichier existe déjà : {destination}. "
        "Aucune donnée n'a été écrasée."
    )

editeurs.to_csv(
    destination,
    index=False,
    encoding="utf-8-sig"
)

# 6. Vérification
print("Fichier créé :", destination)
print("Jeux à vérifier :", len(editeurs))

print("\nPremiers jeux à analyser :")
print(
    editeurs[
        ["Rank", "Name", "Platform", "Year", "Publisher"]
    ].head(10).to_string(index=False)
)
