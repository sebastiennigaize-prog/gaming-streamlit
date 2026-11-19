Gaming Streamlit — Rapport technique de nettoyage et de fiabilisation
État : dataset enrichi validé — 18 novembre 2026
Dépôt : https://github.com/sebastiennigaize-prog/gaming-streamlit
Version de référence : commit b99fc72
1. Objectif et périmètre
Préparer une base de ventes de jeux vidéo exploitable pour les analyses SQL, les tableaux de bord et une application Streamlit. Le principal enjeu est de distinguer une ligne commerciale (jeu sur une plateforme), un jeu ou une édition distincte et sa déclinaison par plateforme. Une simple agrégation par nom risquerait de fusionner des jeux différents ou de compter plusieurs fois un même titre dans les statistiques de catalogue.

Le fichier vgsales.csv constitue la source brute du projet. L'origine exacte de la distribution, sa licence et sa méthode de collecte restent à documenter avant toute diffusion publique des données. Les ventes sont exprimées en millions d'unités, et non en chiffre d'affaires. Le catalogue ne représente pas nécessairement l'intégralité du marché.
2. Organisation du traitement
Fichier	Rôle
data/vgsales.csv	Données brutes
data/vgsales_clean.csv	Entrée nettoyée du regroupement
data/annees_a_verifier.csv	Suivi des années et corrections validées
data/corrections_validees.csv	Corrections d'années documentées
data/editeurs_a_verifier.csv	Suivi des éditeurs
data/corrections_editeurs.csv	Corrections des éditeurs
data/doublons_a_verifier.csv	Suivi des doublons
data/vgsales_enriched.csv	Dataset final
data/backups/	Sauvegardes locales, exclues du versionnement


Le projet utilise des scripts Python et Pandas pour les audits, la correction et l'enrichissement. Les scripts d'analyse et de correction sont séparés du script final scripts/regrouper_jeux.py. Les détails chiffrés des anomalies initiales et du traitement des éditeurs devront être complétés à partir de leurs scripts et fichiers de suivi : ils n'ont pas été réexaminés pour ce rapport.
3. Problèmes identifiés et solutions
Difficulté	Solution
Années manquantes ou incohérentes	Recherche documentaire par titre et plateforme, correction tracée
Éditeurs à vérifier ou à harmoniser	Fichiers de suivi et de corrections dédiés
Jeux homonymes	Distinction par année, plateforme et identité du jeu
Titres alternatifs et numérotation régionale	Normalisation vers un titre commun lorsque l'identité est confirmée
Portages, remakes et éditions améliorées	Classification selon la nature réelle de la version
Plusieurs lignes pour un même jeu et une même plateforme	Signalement sans suppression automatique
Risque de régression lors de la maintenance	Assertions, audits, conservation des ventes et comparaison SHA-256


4. Correction des années
Les dates sont recherchées au niveau de la plateforme concernée. Les fichiers de corrections consultés contiennent notamment des références à MobyGames, GameFAQs et à des sites officiels d'éditeurs ou constructeurs. Les URL sont conservées dans le champ Source_Year ; leur validité individuelle n'a pas été revérifiée pour ce rapport.

Exemples documentés : NASCAR Thunder 2003 (PS2) → 2002 ; LEGO Harry Potter: Years 5-7 (3DS) → 2011 ; The Lord of the Rings: War in the North (PS3 et X360) → 2011.

Dans le script final, seules les lignes dont Statut_Verification vaut Verifie et dont Year_Corrected est renseigné sont sélectionnées. La jointure gauche utilise Rank, Name et Platform, avec validation one_to_one. combine_first remplace l'année uniquement lorsqu'une correction existe. La colonne temporaire est ensuite supprimée.

Le dernier journal d'exécution confirme 275 corrections appliquées. Ce nombre correspond aux lignes ayant une correction renseignée, pas nécessairement à 275 valeurs différentes de l'année d'origine. Le nombre final d'années manquantes reste à mesurer sur le CSV.
5. Normalisation des jeux et règles métier
- Conserver Name, le libellé source, et créer Game_Title_Clean pour le regroupement.
- Regrouper les portages simples d'une même version sous le même identifiant.
- Séparer les jeux homonymes, remakes, remasters et rééditions substantiellement distinctes.
- Examiner les cas ambigus individuellement et soumettre les décisions à validation métier.
- Ne pas modifier les ventes pour résoudre un problème d'identification.
Exemples de décisions
Cas	Décision
Mortal Kombat	Jeu original de 1992 distinct du reboot de 2011
Need for Speed: Most Wanted	Séparation des jeux de 2005 et 2012 ; portage Wii U de 2013 associé au second
Sonic the Hedgehog	Séparation des jeux de 1991 et 2006
Resident Evil 2	PS, N64 et GC regroupés sous l'original de 1998 ; Dual Shock Edition séparée
Final Fantasy III	Original NES de 1990 distinct du remake 3D ; traitement de l'appellation américaine du jeu SNES correspondant à Final Fantasy VI
Tales of Phantasia	Versions SNES 1995, PS 1998 et GBA 2003 séparées
Bomberman	Distinction des versions NES 1985, DS 2005, PSP 2006 et Wii 2008


Ces décisions sont propres au projet et ne prétendent pas constituer une taxonomie universelle du jeu vidéo.
6. Identifiants et granularité
Rank reste la clé unique de la ligne source. Game_ID est calculé via pd.factorize sur Game_Title_Clean avec tri, puis incrémenté de 1. Game_Version_ID est calculé via groupby(["Game_ID", "Platform"]).ngroup() + 1.

Ces identifiants sont déterministes pour un même dataset et un même ensemble de règles, mais peuvent être renumérotés si le catalogue change. Une clé persistante serait nécessaire en cas de mises à jour incrémentales.

Le grain du dataset final reste la ligne commerciale source, et non le jeu unique. Pour compter les jeux, utiliser le nombre distinct de Game_ID.
7. Doublons potentiels
Le nombre de lignes par Game_Version_ID est calculé par transform("size"). Les groupes de plusieurs lignes sont signalés dans Doublon_Potentiel. Le script contient une ancienne exception Resident Evil 2 et vérifie finalement que les indicateurs correspondent aux versions répétées ; aucune ligne n'est actuellement masquée par cette exception.
Jeu	Plateforme	Rank	Ventes mondiales cumulées (M)
Madden NFL 13	PS3	604, 16130	2,57
Sonic the Hedgehog (2006)	PS3	1717, 4147	1,66
Resident Evil Director's Cut	PS3	9673, 13533	0,16


Six lignes, soit trois groupes, sont conservées et signalées. Le signalement ne prouve pas qu'il s'agit de ventes comptées deux fois. Une exclusion éventuelle nécessite une justification documentaire. Les ventes publiées dans ce rapport incluent ces lignes.
8. Contrôles qualité et audit
Le script contient des assertions propres aux règles de classification ainsi que des contrôles globaux : nombre de lignes, unicité de Rank, identifiants renseignés, conservation des colonnes d'origine hors Year, conformité des corrections d'années, conservation des ventes, cohérence du signalement des doublons. Après export, le CSV est relu et comparé au DataFrame avec pd.testing.assert_frame_equal(check_dtype=False).

L'audit final regroupe par Game_ID et Game_Title_Clean, calcule les effectifs, le nombre de plateformes, les années minimale et maximale et les ventes. Il signale les groupes de plusieurs lignes dont l'écart d'années est d'au moins cinq ans, hors liste de 13 titres préalablement validés (TITRES_VALIDES). Cette exclusion concerne uniquement l'audit, jamais les données.

Résultat final : 0 regroupement suspect selon ce critère. Ce résultat ne garantit pas l'absence de toute anomalie historique ; les erreurs produisant un écart inférieur à cinq ans ne sont notamment pas détectées par ce filtre.
9. Consolidation et traçabilité
La version consolidée du script réduit le volume de 445 lignes (194 insertions et 639 suppressions selon Git). Les améliorations structurelles ont été effectuées sans changer les résultats ; les règles successives incertaines ont été conservées par prudence.

La copie data/backups/vgsales_enriched_reference.csv a servi de référence avant modification. Après exécution du nouveau script, les deux fichiers présentaient la même empreinte SHA-256 :
5fe6d7e11ca34037d4a7153c7eb084e3c85f6fb170c3bc0414f0ad057139ac20
Le commit 251e6bb correspond à la finalisation initiale du nettoyage. Le commit b99fc72 correspond à la consolidation, poussée sur main. Le dernier git status confirme la synchronisation avec origin/main.
10. Bilan final
Indicateur	Valeur
Lignes	16 597
Colonnes	16
Titres bruts distincts	11 493
Game_ID distincts	11 668
Game_Version_ID distincts	16 594
Jeux monoplateformes	8 988 (77,03 %)
Jeux multiplateformes	2 680 (22,97 %)
Plateformes	31
Genres	12
Éditeurs	630
Période observée	1977–2020
Ventes mondiales (millions)	8 920,42
Lignes signalées comme doublons potentiels	6
Corrections d'années appliquées	275
Regroupements suspects selon l'audit	0


11. Reproduction et limites
Depuis la racine du projet, dans l'environnement Python configuré :
./.venv/Scripts/python.exe scripts/regrouper_jeux.py
sha256sum data/vgsales_enriched.csv data/backups/vgsales_enriched_reference.csv
Diagnostic ponctuel (le script exécute également le pipeline complet) :
./.venv/Scripts/python.exe scripts/regrouper_jeux.py --jeu "Resident Evil 2"
Ce rapport repose sur le script consolidé, les extraits de corrections datés du 11 novembre, les résultats des analyses précédentes et les journaux d'exécution et Git du 18 novembre. Les fichiers CSV complets et les scripts amont n'ont pas été réexécutés pour sa rédaction. Avant de finaliser la documentation, compléter les statistiques du nettoyage initial, les détails de normalisation des éditeurs, le nombre de valeurs manquantes résiduelles et les informations de provenance et de licence.

La prochaine étape est la modélisation relationnelle du dataset, en conservant la granularité et la traçabilité définies ici.