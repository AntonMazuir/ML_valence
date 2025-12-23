import streamlit as st

from utils.data_loader import load_data
from utils.scoring import add_score_column, add_marge_and_ecart

def main():
    st.title("📊 Comparatif global des biens")

    df = load_data()
    df = add_score_column(df)
    df = add_marge_and_ecart(df)

    colonnes = [
        "Titre du bien", "Quartier", "Surface (m²)", "Prix d’achat (€)",
        "Valeur estimée après travaux (€)", "Plus-value brute (€)",
        "Marge (%)", "Score", "Écart au marché (€/m²)"
    ]

    st.dataframe(df[colonnes].sort_values("Score", ascending=False), use_container_width=True)

if __name__ == "__main__":
    main()
