import pandas as pd
import numpy as np
from model import ValenceModel
import os

def detect_opportunities(data_path='data/processed/valence_training_set.csv'):
    ai = ValenceModel()

    if not os.path.exists(data_path):
        print("❌ Dataset introuvable. Lance le main.py d'abord.")
        return pd.DataFrame()

    df = pd.read_csv(data_path)

    # 1. Alignement des features sur le modèle V5
    features = [
        'size', 'rooms', 'bathrooms', 'floor_clean', 'hasLift', 'exterior',
        'district', 'neighborhood', 'latitude', 'longitude',
        'bath_ratio', 'light_score', 'geo_cluster',
        'dist_center', 'dist_beach', 'dist_turia', 'dist_arts_sciences',
        'dist_upv', 'dist_metro_xativa', 'dist_metro',
        'is_house', 'needs_reform', 'is_ground_floor',
        'has_parking', 'is_penthouse', 'has_terrace', 'has_balcony',
        'is_last_floor', 'is_south_facing',
        'realtime_growth', 'momentum_score', 'historical_growth'
    ]

    print(f"🕵️ Analyse de {len(df)} annonces (V5 Industrielle)...")

    # Vérification colonnes
    missing = [c for c in features if c not in df.columns]
    if missing:
        print(f"❌ Colonnes manquantes : {missing}")
        return pd.DataFrame()

    # 2. Prédiction intelligente
    df['estimated_price'] = ai.predict(df)

    # 3. Calcul des métriques financières
    df['profit_potential'] = df['estimated_price'] - df['price']
    df['discount_pct'] = (df['profit_potential'] / df['estimated_price']) * 100

    # 4. CALCUL DE L'INVESTMENT SCORE (0-100)
    # A. Score de Marge (Normalisé 0-60)
    # On considère qu'un discount de 30% est le top (60 pts)
    margin_score = (df['discount_pct'] / 30) * 60
    margin_score = margin_score.clip(0, 60)

    # B. Score de Momentum (Normalisé 0-25)
    # Un momentum de 1.5 (accélération de 50% vs historique) = 25 pts
    momentum_bonus = (df['momentum_score'] / 1.5) * 25
    momentum_bonus = momentum_bonus.clip(0, 25)

    # C. Score Qualité (0-15 pts)
    quality_bonus = (
        df['has_terrace'] * 5 +
        df['is_last_floor'] * 5 +
        df['is_south_facing'] * 5
    )

    df['investment_score'] = margin_score + momentum_bonus + quality_bonus

    # 5. Filtres de sécurité
    # On élimine les erreurs manifestes (marge > 50%) ou les prix incohérents
    opps = df[
        (df['discount_pct'] > 12) &
        (df['discount_pct'] < 50) &
        (df['price'] > 55000)
    ].copy()

    return opps.sort_values(by='investment_score', ascending=False)

def print_report(opps):
    print(f"\n🚀 TOP {len(opps.head(15))} OPPORTUNITÉS (Tirées par Investment Score)\n")
    for _, row in opps.head(15).iterrows():
        url = f"https://www.idealista.com/inmueble/{int(row['propertyCode'])}/"

        # Icônes de confort
        icons = ""
        if row['has_terrace']: icons += "🌳 "
        if row['is_south_facing']: icons += "☀️ "
        if row['is_last_floor']: icons += "🔝 "

        print(f"⭐ SCORE: {int(row['investment_score'])}/100 | {row['neighborhood']}")
        print(f"💰 Prix: {int(row['price']):,} € (Est: {int(row['estimated_price']):,} €)")
        print(f"📈 Marge: +{row['discount_pct']:.1f}% | Momentum: {row['momentum_score']:.2f} {icons}")
        print(f"🔗 {url}")
        print("-" * 50)
