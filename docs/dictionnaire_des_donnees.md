Gaming Streamlit — Dictionnaire des données
1. Périmètre
Ce document décrit data/vgsales_enriched.csv, validé le 18 novembre 2026. Il contient 16 597 lignes et 16 variables. Une ligne représente un enregistrement de ventes du dataset source, et non nécessairement un jeu unique.
2. Variables
Les types ci-dessous sont des types logiques proposés pour la modélisation ; les types effectivement inférés à la lecture du CSV restent à contrôler.
Variable	Type logique	Description	Unité / rôle
Rank	Entier	Rang d'origine de l'enregistrement, conservé après nettoyage	Identifiant unique de ligne
Name	Texte	Nom du jeu avant regroupement des titres	Libellé source
Platform	Texte	Code de la plateforme	Dimension, 31 plateformes
Year	Entier nullable	Année de sortie de l'enregistrement, après application des corrections validées	Année, 1977–2020 observées
Genre	Texte	Genre du jeu	Dimension, 12 genres
Publisher	Texte	Éditeur après nettoyage	Dimension, 630 éditeurs recensés
NA_Sales	Décimal	Ventes en Amérique du Nord	Millions d'unités
EU_Sales	Décimal	Ventes en Europe	Millions d'unités
JP_Sales	Décimal	Ventes au Japon	Millions d'unités
Other_Sales	Décimal	Ventes dans les autres régions	Millions d'unités
Global_Sales	Décimal	Ventes mondiales enregistrées dans le dataset	Millions d'unités
Game_Title_Clean	Texte	Titre normalisé distinguant les versions selon les règles métier	Clé métier de regroupement
Game_ID	Entier	Identifiant généré à partir du titre normalisé	11 668 jeux ou versions distinctes
Game_Version_ID	Entier	Identifiant généré pour chaque couple Game_ID / Platform	16 594 couples distincts
Nombre_Lignes_Version	Entier	Nombre de lignes partageant un Game_Version_ID	Effectif
Doublon_Potentiel	Booléen	Indicateur de répétition potentielle d'une version sur une plateforme	6 lignes signalées


3. Granularité et règles d'exploitation
- Rank est unique dans le dataset validé et constitue une clé de ligne adaptée à la table de faits.
- Game_ID identifie une version métier du jeu : les simples portages peuvent être regroupés, les remakes, remasters et rééditions distinctes sont séparés.
- Game_Version_ID distingue les couples jeu-version métier / plateforme. Il n'est pas unique par ligne.
- Les deux identifiants sont calculés automatiquement ; leur stabilité entre futurs jeux de données enrichis n'est pas garantie.
- Pour compter les jeux, utiliser le nombre distinct de Game_ID, plutôt que le nombre de lignes.
- Les ventes mondiales sont déjà une mesure globale : ne pas les additionner aux ventes régionales. Des écarts d'arrondi sont possibles entre le total mondial et la somme des régions.
- Ne pas supprimer automatiquement les doublons potentiels : les lignes sont conservées et signalées.
4. Contrôles de référence
Indicateur	Valeur
Lignes	16 597
Colonnes	16
Game_ID distincts	11 668
Game_Version_ID distincts	16 594
Ventes mondiales (millions)	8 920,42
Corrections d'années appliquées	275
Lignes signalées	6
Regroupements suspects selon l'audit	0


Les six lignes signalées correspondent à trois couples jeu/plateforme : Madden NFL 13 (PS3), Sonic the Hedgehog (2006) (PS3) et Resident Evil Director's Cut (PS3).
5. Limites et vérifications à compléter
La provenance exacte, la licence, la couverture commerciale et la définition des unités de ventes doivent être confirmées auprès de la source originale. Les types Pandas réels, la nullabilité et les valeurs manquantes par colonne doivent être mesurés avant la modélisation SQL. Les valeurs de référence proviennent des journaux d'exécution validés, et non d'une nouvelle lecture intégrale du CSV pour ce document.

Voir aussi [le rapport de nettoyage](nettoyage_des_donnees.md).