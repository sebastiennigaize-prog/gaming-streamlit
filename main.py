import streamlit as st
import pandas as pd

# Configuration
st.set_page_config(
    page_title="Gaming Explorer",
    page_icon="🎮",
    layout="wide"
)

st.title("🎮 Gaming Explorer")

st.write(
    "Bienvenue dans mon application dédiée aux jeux vidéo ! "
    "Explore quelques jeux célèbres selon leur genre."
)

st.divider()


# Base de données jeux
jeux = pd.DataFrame({
    "Jeu": [
        "The Witcher 3",
        "Minecraft",
        "FIFA 25",
        "Civilization VI",
        "Zelda Breath of the Wild",
        "Cyberpunk 2077"
    ],

    "Genre": [
        "RPG",
        "Aventure",
        "Sport",
        "Stratégie",
        "Aventure",
        "Action"
    ],

    "Plateforme": [
        "PC / Console",
        "PC / Console",
        "Console",
        "PC",
        "Nintendo Switch",
        "PC / Console"
    ],

    "Note": [
        9.8,
        9.5,
        8.0,
        9.2,
        9.7,
        8.5
    ],

    "Image": [
        "https://upload.wikimedia.org/wikipedia/en/0/0c/Witcher_3_cover_art.jpg",
        "https://upload.wikimedia.org/wikinews/en/7/7a/Minecraft_game_cover.jpeg",
        "https://www.micromania.fr/dw/image/v2/BCRB_PRD/on/demandware.static/-/Sites-masterCatalog_Micromania/default/dwe41e9b48/images/packshots/ea-fc-25/FC25ps52DPFTfront_fr_nl_RGB.jpg",
        "https://static.wikia.nocookie.net/sidmeierscivilization/images/c/c2/Civilization_VI_jaquette.webp/revision/latest?cb=20240507095942&path-prefix=fr",
        "https://www.gamecash.fr/thumbnail-400-450/the-legend-of-zelda-breath-of-the-wild-us-e142417.jpg",
        "https://upload.wikimedia.org/wikipedia/en/9/9f/Cyberpunk_2077_box_art.jpg"
    ]
})


# Choix du genre
st.header("⭐ Choisis ton univers gaming")


# Sidebar
st.sidebar.header("🎮 Filtres")


genre = st.sidebar.selectbox(
    "Choisis un genre",
    jeux["Genre"].unique()
)


plateformes_disponibles = jeux[
    jeux["Genre"] == genre
]["Plateforme"].unique()


plateforme = st.sidebar.selectbox(
    "Choisis une plateforme",
    plateformes_disponibles
)


# Filtrer les jeux
selection = jeux[
    (jeux["Genre"] == genre) &
    (jeux["Plateforme"] == plateforme)
]


st.divider()


st.header("🕹️ Détails d'un jeu")


if len(selection) > 0:

    jeu_choisi = st.selectbox(
        "Sélectionne un jeu",
        selection["Jeu"]
    )


    infos_jeu = selection[
        selection["Jeu"] == jeu_choisi
    ].iloc[0]


else:

    st.warning(
        "⚠️ Aucun jeu disponible pour cette combinaison genre / plateforme."
    )

    st.stop()



# Affichage

col1, col2 = st.columns(2)


with col1:

    st.subheader(infos_jeu["Jeu"])

    st.write(
        f"🎯 Genre : {infos_jeu['Genre']}"
    )

    st.write(
        f"🎮 Plateforme : {infos_jeu['Plateforme']}"
    )

    st.write(
        f"⭐ Note : {infos_jeu['Note']}/10"
    )


with col2:

    st.image(
        infos_jeu["Image"],
        width=250
    )



# Tableau

st.divider()

st.subheader(
    f"🎯 Jeux : {genre} - {plateforme}"
)


st.dataframe(
    selection,
    use_container_width=True
)



# Statistique

st.metric(
    "Nombre de jeux trouvés",
    len(selection)
)



# Graphique

st.divider()

st.header("📊 Analyse des notes par genre")


moyennes = jeux.groupby("Genre")["Note"].mean()


st.bar_chart(moyennes)