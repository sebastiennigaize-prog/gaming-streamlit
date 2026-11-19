🎮 Gaming Explorer — Video Game Sales Analytics
Projet personnel de Data Analytics consacré à l’étude des ventes de jeux vidéo, de la préparation des données à leur visualisation dans une application interactive.
🎯 Objectifs
- Construire un dataset fiable et documenté.
- Identifier les jeux, leurs différentes versions et leurs plateformes.
- Étudier les ventes par période, région, genre, éditeur et plateforme.
- Construire une base relationnelle et développer un tableau de bord interactif.
📊 Le dataset enrichi
Indicateur	Valeur
Observations	16 597
Variables	16
Jeux uniques	11 668
Couples jeu–plateforme distincts	16 594
Plateformes	31
Genres	12
Éditeurs	630
Période observée	1977–2020
Ventes mondiales (millions)	8 920,42


Les ventes correspondent aux observations du dataset, et non à une mesure exhaustive du marché mondial.
🧹 Data cleaning et fiabilisation
Le travail de préparation comprend :
- Audit des données, des dates et des doublons.
- Correction des années de sortie (275 corrections appliquées lors du dernier traitement).
- Normalisation des éditeurs et des titres.
- Distinction des homonymes, portages, remakes, remasters et éditions enrichies.
- Génération automatique des identifiants Game_ID et Game_Version_ID.
- Contrôles d’intégrité et documentation des exceptions.
Exemples de décisions métier
Jeu	Traitement
Resident Evil 2	Regroupement des portages de la version originale ; séparation de l’édition Dual Shock.
Final Fantasy	Séparation de la version NES et de la version WonderSwan.
Tales of Phantasia	Distinction des versions SNES, PlayStation et Game Boy Advance.
Tactics Ogre	Distinction de la version originale et du remake PSP.


Contrôles qualité
- 0 identifiant manquant lors du dernier contrôle.
- 0 regroupement suspect résiduel selon les critères de l’audit.
- 6 observations signalées comme doublons potentiels, conservées pour éviter une suppression injustifiée.
- Conservation du nombre de lignes et du total des ventes lors du regroupement.
- Consolidation du script validée par comparaison SHA-256 : le CSV généré est identique au fichier de référence.
🛠️ Technologies
Utilisées : Python, Pandas, Streamlit, Git, GitHub, VS Code.

Prévues pour les prochaines phases : DuckDB, SQL, Plotly.
📂 Structure du projet
Gaming_Streamlit/
├── data/
│   ├── vgsales.csv
│   ├── vgsales_clean.csv
│   ├── vgsales_enriched.csv
│   └── ... (fichiers de suivi et de correction)
├── docs/
│   ├── nettoyage_des_donnees.md
│   ├── dictionnaire_des_donnees.md
│   └── regles_metier.md
├── images/
├── scripts/
│   ├── nettoyage.py
│   ├── audit_dataset.py
│   ├── correction_annees.py
│   ├── correction_editeurs.py
│   ├── creer_dataset_clean.py
│   ├── regrouper_jeux.py
│   └── ... (scripts complémentaires)
├── main.py
├── pyproject.toml
└── README.md
📚 Documentation technique
- [Rapport de nettoyage des données](docs/nettoyage_des_donnees.md)
- [Dictionnaire des données](docs/dictionnaire_des_donnees.md)
- [Règles métier et classification des jeux](docs/regles_metier.md)
🚀 Installation et exécution
Cloner le dépôt, puis installer les dépendances avec uv (à installer au préalable) :
git clone https://github.com/sebastiennigaize-prog/gaming-streamlit.git
cd gaming-streamlit
uv sync
Pour régénérer le dataset enrichi à partir du dataset nettoyé et des fichiers de correction existants :
uv run python scripts/regrouper_jeux.py
Pour afficher un diagnostic ciblé (le pipeline complet est également exécuté) :
uv run python scripts/regrouper_jeux.py --jeu "Resident Evil 2"
Pour lancer le prototype Streamlit :
uv run streamlit run main.py
📸 Prototype initial
La première version de Gaming Explorer permet de filtrer une sélection de jeux par genre et plateforme, d’afficher leurs informations et de comparer leurs notes. Elle précède le nouveau pipeline de données ; les fonctionnalités utilisant le dataset enrichi restent à développer.

🗺️ Feuille de route
- [x] Audit, nettoyage et correction des données
- [x] Normalisation des titres et génération des identifiants
- [x] Validation du dataset enrichi et consolidation du script
- [x] Première documentation technique
- [ ] Vérification complémentaire de la provenance, de la licence et des statistiques initiales
- [ ] Modélisation en schéma en étoile avec DuckDB
- [ ] Analyses exploratoires et requêtes SQL
- [ ] Développement de l’application Streamlit sur le dataset enrichi
- [ ] Documentation finale et valorisation dans le portfolio
⚠️ Limites et traçabilité
La provenance exacte, la licence de redistribution, la couverture des ventes et certaines statistiques du nettoyage initial restent à confirmer. Les dates et regroupements reposent sur les corrections et conventions documentées dans le projet. L’absence de signalement dans l’audit ne garantit pas l’absence de toute erreur historique.
Projet personnel de reconversion professionnelle vers le métier de Data Analyst.