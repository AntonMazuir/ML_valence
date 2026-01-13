import pandas as pd
import numpy as np
from model import ValenceModel
import os

def detect_opportunities(data_path='data/processed/valence_training_set.csv'):
    # --- ÉTAPE 1 : INITIALISATION ---
    ai = ValenceModel()

    if not os.path.exists(data_path):
        print("❌ Dataset introuvable. Lance le main.py d'abord.")
        return pd.DataFrame()

    df = pd.read_csv(data_path)
    print(f"🕵️ Analyse de {len(df)} annonces (Système V5 Robuste)...")

    # --- ÉTAPE 2 : PRÉDICTION DE LA VALEUR DE MARCHÉ ---
    # L'IA estime le "Juste Prix" intrinsèque (sans regarder le prix affiché)
    df['estimated_price'] = ai.predict(df)

    # --- ÉTAPE 3 : CALCULS DES MARGES ---
    # profit_potential = gain théorique à la revente après travaux
    # On compare l'estimation IA au "Budget Total" (Prix + Travaux + Frais)
    df['real_profit_potential'] = df['estimated_price'] - df['total_investment']
    df['margin_pct'] = (df['real_profit_potential'] / df['estimated_price']) * 100

    # --- ÉTAPE 4 : LE SYSTÈME DE SCORING 2.0 (SUR 100 POINTS) ---

    # A. Score de Marge (40 pts) : L'écart entre prix IA et Budget Total
    # Un profit de +25% sur investissement total = 40 pts
    margin_score = (df['margin_pct'] / 25) * 40
    margin_score = margin_score.clip(0, 40)

    # B. Score de Rendement (30 pts) : On récompense le Cash-flow
    # Un rendement net de 8% (best_yield) = 30 pts
    yield_score = (df['best_yield'] / 8) * 30
    yield_score = yield_score.clip(0, 30)

    # C. Score de Momentum (20 pts) : Quartiers qui montent vite
    # Un momentum de 1.5 (50% plus vite que l'historique) = 20 pts
    momentum_score = (df['momentum_score'] / 1.5) * 20
    momentum_score = momentum_score.clip(0, 20)

    # D. Bonus Qualité / Airbnb (10 pts)
    # On valorise la Licence Airbnb et les prestations de confort
    quality_bonus = (
        df['is_airbnb_ready'] * 4 +  # Licence détectée = gros bonus
        df['has_terrace'] * 3 +
        df['is_last_floor'] * 3
    )
    quality_bonus = quality_bonus.clip(0, 10)

    # TOTAL DU SCORE D'INVESTISSEMENT
    df['investment_score'] = margin_score + yield_score + momentum_score + quality_bonus

    # --- ÉTAPE 5 : FILTRES DE SÉCURITÉ (LE TAMIS) ---
    # 1. On évite les erreurs d'estimation (trop beau pour être vrai > 50%)
    # 2. On veut une marge minimale (profit > 10% après travaux)
    # 3. On évite les biens trop bas de gamme (prix > 55k)
    opps = df[
        (df['margin_pct'] > 10) &
        (df['margin_pct'] < 50) &
        (df['price'] > 55000)
    ].copy()

    return opps.sort_values(by='investment_score', ascending=False)

def print_report(opps):
    """ Affiche un résumé rapide dans le terminal """
    print(f"\n🚀 TOP {len(opps.head(15))} OPPORTUNITÉS (Ranking IA & Finance)\n")
    for _, row in opps.head(15).iterrows():
        url = f"https://www.idealista.com/inmueble/{int(row['propertyCode'])}/"

        # Tags visuels
        tags = []
        if row['is_airbnb_ready']: tags.append("✈️ AIRBNB")
        if row['yield_airbnb'] > row['net_yield']: tags.append("💰 BOOST SAISONNIER")

        tag_str = " | ".join(tags) if tags else "🏠 LONG TERME"

        print(f"⭐ SCORE: {int(row['investment_score'])}/100 | {row['neighborhood']}")
        print(f"💵 Prix: {int(row['price']):,} € | Budget Total: {int(row['total_investment']):,} €")
        print(f"📊 Rendement: {row['best_yield']:.2f}% Net | Marge Revente: +{row['margin_pct']:.1f}%")
        print(f"📍 {tag_str}")
        print(f"🔗 {url}")
        print("-" * 60)

if __name__ == "__main__":
    opportunities = detect_opportunities()
    print_report(opportunities)
