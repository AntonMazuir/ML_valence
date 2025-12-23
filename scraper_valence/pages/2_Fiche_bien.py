import streamlit as st
import pandas as pd

from utils.data_loader import load_data
from utils.scoring import add_score_column

def main():
    st.title("📄 Analyse détaillée d’un bien")

    df = load_data()
    df = add_score_column(df)

    quartiers = sorted(df["Quartier"].dropna().unique())
    quartier = st.selectbox("Filtrer par quartier :", quartiers)

    biens_quartier = df[df["Quartier"] == quartier].sort_values("Score", ascending=False)
    bien_choisi = st.selectbox("🏢 Choisissez un bien :", biens_quartier["Titre du bien"])

    bien = biens_quartier[biens_quartier["Titre du bien"] == bien_choisi].iloc[0]

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(bien["Titre du bien"])
        st.markdown(f"**Quartier :** {bien['Quartier']}")
        st.markdown(f"**Surface :** {bien['Surface (m²)']} m²")
        st.markdown(f"**Prix d’achat :** €{bien['Prix d’achat (€)']:,}".replace(",", " "))
        st.markdown(f"**Coût total :** €{bien['Coût total (€)']:,}".replace(",", " "))
        st.markdown(f"**Valeur estimée après travaux :** €{bien['Valeur estimée après travaux (€)']:,}".replace(",", " "))
        st.markdown(f"**Plus-value brute :** €{bien['Plus-value brute (€)']:,}".replace(",", " "))
        st.markdown(f"**Score global :** {bien['Score']} / 100")

    with col2:
        if "lien photos" in bien.index and pd.notna(bien["lien photos"]):
            st.image(bien["lien photos"], caption="Photo du bien", use_column_width=True)

if __name__ == "__main__":
    main()
