import pandas as pd
import numpy as np
from model import ValenceModel
import os

def detect_opportunities(data_path='data/processed/valence_training_set.csv'):
    # 1. Charger le modèle
    ai = ValenceModel()

    if not os.path.exists(data_path):
        print("❌ Dataset introuvable. Lance le main.py d'abord.")
        return pd.DataFrame()

    df = pd.read_csv(data_path)

    # 2. Nettoyage et préparation des types (Crucial pour CatBoost)
    df['neighborhood'] = df['neighborhood'].fillna("Unknown")
    df['district'] = df['district'].fillna("Unknown")
    df['status'] = df['status'].fillna("good")
    df['geo_cluster'] = df['geo_cluster'].astype(str) # Important : doit être en string

    # 3. Features ALIGNÉES sur le modèle V3
    features = [
        'size', 'rooms', 'bathrooms', 'floor', 'hasLift', 'exterior',
        'district', 'status', 'neighborhood', 'latitude', 'longitude',
        'bath_ratio', 'light_score', 'geo_cluster',
        'dist_center', 'dist_beach', 'dist_turia', 'dist_arts_sciences',
        'dist_upv', 'dist_metro_xativa', 'dist_metro',
        'is_house', 'needs_reform', 'is_ground_floor',
        'has_parking', 'is_penthouse'
    ]

    print(f"🕵️ Analyse de {len(df)} annonces avec intelligence géographique...")

    # Vérification que toutes les colonnes sont présentes
    missing_cols = [c for c in features if c not in df.columns]
    if missing_cols:
        print(f"❌ Erreur : Colonnes manquantes dans le CSV : {missing_cols}")
        return pd.DataFrame()

    # Prédiction
    preds_log = ai.model.predict(df[features])
    df['estimated_price'] = np.expm1(preds_log)

    # 4. Calcul du score d'opportunité
    df['profit_potential'] = df['estimated_price'] - df['price']
    df['discount_pct'] = (df['profit_potential'] / df['estimated_price']) * 100

    # 5. Filtre de qualité
    # On cherche les vrais rabais, prix > 50k (exclut garages) et discount < 60% (exclut erreurs IA)
    opps = df[(df['discount_pct'] > 15) & (df['discount_pct'] < 60) & (df['price'] > 50000)].copy()

    return opps.sort_values(by='discount_pct', ascending=False)

def print_report(opps):
    print(f"\n🎯 {len(opps)} OPPORTUNITÉS DÉTECTÉES SUR VALENCE\n")
    for _, row in opps.head(15).iterrows():
        url = f"https://www.idealista.com/inmueble/{int(row['propertyCode'])}/"
        print(f"📍 {row['neighborhood']} ({row['district']})")
        print(f"💰 Prix: {int(row['price']):,} € | 🤖 Est. IA: {int(row['estimated_price']):,} €")
        print(f"📈 Marge: +{row['discount_pct']:.1f}% ({int(row['profit_potential']):,} €)")
        print(f"🔗 {url}")
        print("-" * 45)
