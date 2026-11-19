Gaming Streamlit — Règles métier
1. Objectif et granularité
Le dataset enrichi conserve une ligne par observation source, identifiée par Rank. Un jeu peut apparaître sur plusieurs plateformes ou dans plusieurs observations. Le regroupement ne doit pas supprimer de ventes.
2. Identification des jeux et versions
- Name conserve le titre source.
- Game_Title_Clean représente le titre normalisé de la version retenue.
- Game_ID identifie une version de base du jeu, indépendamment de ses simples portages.
- Game_Version_ID identifie le couple Game_ID / Platform.
- Les identifiants sont générés automatiquement, et non attribués manuellement. Ils peuvent évoluer si le référentiel des titres change.
Situation	Décision
Simple portage de la même version	Même Game_ID
Remake	Game_ID distinct
Remaster	Game_ID distinct
Réédition matériellement enrichie	Game_ID distinct
Homonymes désignant des jeux différents	Game_ID distinct
Cas ambigu	Diagnostic et validation avant modification


Une différence d'année ou de plateforme ne suffit pas à elle seule à établir l'existence d'une nouvelle version.
3. Exemples de décisions validées
Jeu	Décision
Resident Evil 2	PS, N64 et GC regroupés pour la version originale ; édition Dual Shock séparée.
Final Fantasy	NES 1987 et WonderSwan 2000 séparés.
Final Fantasy III	Version originale et remake 3D séparés.
Tales of Phantasia	SNES 1995, PS 1998 et GBA 2003 séparés.
Super Ghouls ’n Ghosts	SNES 1991 et GBA 2002 séparés.
Tactics Ogre: Let Us Cling Together	SNES 1995 et PSP 2010 séparés.
Shinobi	PS2 2002 et 3DS 2011 séparés.
Need for Speed: Most Wanted	Jeux de 2005 et 2012 séparés.
Mortal Kombat	Jeux de 1992 et 2011 séparés.
Sonic the Hedgehog	Jeux de 1991 et 2006 séparés.


Ces exemples décrivent les décisions du projet, non un inventaire exhaustif des éditions commercialisées.
4. Années et éditeurs
Les années corrigées sont appliquées à partir des corrections validées, rapprochées sur Rank, Name et Platform. Le dernier journal d'exécution indique 275 corrections appliquées. Les corrections d'éditeurs sont suivies séparément. Ne pas déduire automatiquement une année de sortie ou un éditeur à partir du seul titre.
5. Doublons potentiels
Une version présente sur plusieurs lignes pour une même plateforme est signalée, et non automatiquement supprimée. Nombre_Lignes_Version compte les observations du couple jeu/plateforme ; Doublon_Potentiel signale les groupes de taille supérieure à un.

Six observations sont signalées dans le résultat validé : Madden NFL 13 (PS3), Sonic the Hedgehog (2006) (PS3), Resident Evil Director's Cut (PS3), deux observations chacun. Leur signalement ne démontre pas qu'il s'agit de ventes dupliquées.
6. Audit des regroupements
Le contrôle recherche les groupes de plusieurs observations dont l'écart entre années extrêmes atteint au moins cinq ans. Les regroupements examinés et validés peuvent être exclus via TITRES_VALIDES. Un résultat de zéro suspect signifie qu'aucun groupe ne satisfait les critères résiduels de cet audit ; il ne garantit pas une exactitude historique absolue.
7. Procédure de modification
1. Diagnostiquer le jeu concerné avec scripts/regrouper_jeux.py --jeu "Titre" dans l'environnement Python du projet.
2. Examiner les observations, plateformes, dates et ventes.
3. Proposer une classification et obtenir sa validation en cas de doute.
4. Modifier uniquement les règles nécessaires et conserver les contrôles d'intégrité.
5. Réexécuter le script et examiner l'audit et les totaux.
6. Pour une refactorisation sans changement métier, comparer le CSV produit à la référence via SHA-256.
8. Résultat de référence
Indicateur	Valeur
Observations	16 597
Colonnes	16
Game_ID distincts	11 668
Game_Version_ID distincts	16 594
Ventes mondiales (millions)	8 920,42
Observations signalées	6
Regroupements suspects résiduels	0


La consolidation du script (commit b99fc72) a conservé l'empreinte SHA-256 du CSV : 5fe6d7e11ca34037d4a7153c7eb084e3c85f6fb170c3bc0414f0ad057139ac20.
9. Traçabilité et limites
Ce document synthétise les décisions validées et les journaux d'exécution disponibles. Les sources historiques individuelles, la provenance et la licence du dataset restent à compléter ; aucun nouveau contrôle des CSV ou des sources externes n'a été réalisé pour cette rédaction. Les règles détaillées de regroupement restent dans scripts/regrouper_jeux.py.

Voir aussi [le rapport de nettoyage](nettoyage_des_donnees.md) et [le dictionnaire des données](dictionnaire_des_donnees.md).