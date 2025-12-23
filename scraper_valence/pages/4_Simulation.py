import streamlit as st

from utils.data_loader import PRIX_M2_QUARTIER
from utils.ml import load_price_model, predict_prix_m2

def main():
    st.title("🧮 Simulation d’un nouveau projet à Valence")

    modele_prix = load_price_model()

    col1, col2 = st.columns(2)

    with col1:
        titre = st.text_input("Titre du bien", "Appartement test – Valence")
        quartier = st.selectbox("Quartier", sorted(PRIX_M2_QUARTIER.keys()))
        surface = st.number_input("Surface (m²)", min_value=10.0, max_value=300.0, value=70.0, step=1.0)
        prix_achat = st.number_input("Prix d’achat (€)", min_value=30000.0, max_value=1000000.0, value=150000.0, step=5000.0)
        cout_travaux = st.number_input("Coût des travaux (€)", min_value=0.0, max_value=500000.0, value=30000.0, step=5000.0)

    with col2:
        frais_notaire = st.number_input("Frais de notaire (€)", min_value=0.0, value=12000.0, step=1000.0)
        autres_frais = st.number_input("Autres frais (€)", min_value=0.0, value=5000.0, step=1000.0)
        valeur_apres_travaux = st.number_input("Valeur estimée après travaux (€)", min_value=0.0, value=230000.0, step=5000.0)

    if st.button("Calculer la rentabilité"):
        cout_total = prix_achat + cout_travaux + frais_notaire + autres_frais
        plus_value = valeur_apres_travaux - cout_total
        marge_pct = (plus_value / cout_total) * 100 if cout_total > 0 else 0

        prix_m2 = prix_achat / surface
        ecart_marche = prix_m2 - PRIX_M2_QUARTIER.get(quartier, 0)

        st.subheader("📌 Résultats")
        st.markdown(f"**Coût total :** {cout_total:,.0f} €")
        st.markdown(f"**Plus-value :** {plus_value:,.0f} €")
        st.markdown(f"**Marge :** {marge_pct:.1f} %")
        st.markdown(f"**Prix/m² :** {prix_m2:,.0f} €/m²")
        st.markdown(f"**Écart marché :** {ecart_marche:,.0f} €/m²")

        score = 0
        score += min(max(marge_pct, 0), 40)
        if ecart_marche < 0:
            score += min(abs(ecart_marche) / 50, 30)
        score += 10
        score = round(min(score, 100))

        st.markdown(f"**Score global :** {score} / 100")

        if modele_prix:
            prix_m2_ia = predict_prix_m2(modele_prix, quartier, surface)
            if prix_m2_ia:
                st.markdown("### 🔮 IA")
                st.markdown(f"**Prix marché IA /m² :** {prix_m2_ia:,.0f} €")

if __name__ == "__main__":
    main()
