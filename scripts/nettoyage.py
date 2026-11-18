
import pandas as pd
from pathlib import Path

# ==================================================
# 1. CHEMINS DES FICHIERS
# ==================================================

# Localiser le dossier principal Gaming_Streamlit
BASE_DIR = Path(__file__).resolve().parent.parent

# Chemin vers le dataset original
FICHIER_SOURCE = BASE_DIR / "data" / "vgsales.csv"

# Chemin vers le fichier de suivi des années manquantes
FICHIER_SUIVI = BASE_DIR / "data" / "annees_a_verifier.csv"


# ==================================================
# 2. CHARGEMENT DES DONNÉES
# ==================================================

# Charger le fichier CSV original
df = pd.read_csv(FICHIER_SOURCE)

print("Dataset chargé avec succès !")
print(f"Nombre de lignes : {df.shape[0]}")
print(f"Nombre de colonnes : {df.shape[1]}")

print("\nValeurs manquantes avant nettoyage :")
print(df.isna().sum())


# ==================================================
# 3. NETTOYAGE DES DONNÉES
# ==================================================

# Créer une copie pour conserver les données originales
df_clean = df.copy()

# Remplacer les éditeurs manquants par "Unknown"
df_clean["Publisher"] = df_clean["Publisher"].fillna("Unknown")

# Convertir les années en entiers tout en conservant
# les valeurs manquantes grâce au type Int64
df_clean["Year"] = df_clean["Year"].astype("Int64")


# ==================================================
# 4. VÉRIFICATION DU NETTOYAGE
# ==================================================

print("\nValeurs manquantes après nettoyage :")
print(df_clean.isna().sum())

print("\nTypes des colonnes nettoyées :")
print(df_clean[["Year", "Publisher"]].dtypes)


# ==================================================
# 5. RECHERCHE DES ANNÉES CANDIDATES
# ==================================================

# Sélectionner les jeux sans année de sortie
jeux_sans_annee = df_clean[df_clean["Year"].isna()].copy()

# Sélectionner les jeux dont l'année est connue
jeux_avec_annee = df_clean[df_clean["Year"].notna()]

# Regrouper toutes les années connues pour chaque titre
annees_par_jeu = jeux_avec_annee.groupby("Name")["Year"].agg(
    lambda valeurs: sorted(valeurs.unique().tolist())
)

# Associer les années candidates aux jeux sans année
jeux_sans_annee["Annees_Candidates"] = (
    jeux_sans_annee["Name"]
    .map(annees_par_jeu)
    .apply(
        lambda valeurs: ", ".join(map(str, valeurs))
        if isinstance(valeurs, list)
        else ""
    )
)

# Compter le nombre d'années candidates
jeux_sans_annee["Nb_Annees_Candidates"] = (
    jeux_sans_annee["Annees_Candidates"]
    .apply(lambda valeur: len(valeur.split(", ")) if valeur else 0)
)

print("\nBilan des années candidates :")
print(
    jeux_sans_annee["Nb_Annees_Candidates"]
    .value_counts()
    .sort_index()
)


# ==================================================
# 6. PRÉPARATION DU FICHIER DE SUIVI
# ==================================================

# Colonnes destinées aux corrections vérifiées
jeux_sans_annee["Year_Corrected"] = pd.NA
jeux_sans_annee["Source_Year"] = pd.NA
jeux_sans_annee["Statut_Verification"] = "A_verifier"


# ==================================================
# 7. EXPORT SÉCURISÉ
# ==================================================

# Ne créer le fichier que s'il n'existe pas déjà
# pour protéger les corrections manuelles

if not FICHIER_SUIVI.exists():
    jeux_sans_annee.to_csv(FICHIER_SUIVI, index=False)
    print("\nFichier de suivi créé.")
else:
    print("\nFichier de suivi déjà existant : aucune modification.")

print(f"Chemin du fichier : {FICHIER_SUIVI}")
print(f"Nombre de jeux sans année : {len(jeux_sans_annee)}")
