import streamlit as st

st.set_page_config(
    page_title="Simulateur Immobilier Valence",
    layout="wide"
)

st.title("🏙️ Projet Invest Valence")
st.write("Utilisez le menu de gauche pour naviguer entre les pages.")
st.markdown(
    """
    ### Ce que vous pouvez faire :
    - 📄 Consulter la fiche détaillée de chaque bien
    - 📊 Comparer les biens selon leur score, marge et écart au marché
    - 🧮 Simuler un nouveau projet d'investissement à Valence
    """
)