import pandas as pd
import numpy as np
from model import ValenceModel  # On importe ta classe
import os

def detect_opportunities(data_path='data/processed/valence_training_set.csv'):
    # 1. Charger le modèle via ta classe
    ai = ValenceModel()

    if not os.path.exists(data_path):
        print("❌ Dataset introuvable. Lance le main.py d'abord.")
        return pd.DataFrame()

    df = pd.read_csv(data_path)

    # 2. Nettoyage rapide (indispensable pour les catégories)
    df['neighborhood'] = df['neighborhood'].fillna("Unknown")
    df['district'] = df['district'].fillna("Unknown")
    df['status'] = df['status'].fillna("good")

    # 3. Prédiction de masse
    # On réutilise les features définies dans ton modèle
    features = [
        'size', 'rooms', 'bathrooms', 'floor', 'hasLift',
        'exterior', 'district', 'neighborhood', 'status',
        'dist_center', 'dist_beach', 'latitude', 'longitude'
    ]

    print(f"🕵️ Analyse de {len(df)} annonces en cours...")

    # Utilisation de la méthode interne de CatBoost pour la vitesse
    preds_log = ai.model.predict(df[features])
    df['estimated_price'] = np.expm1(preds_log)

    # 4. Calcul du score d'opportunité
    df['profit_potential'] = df['estimated_price'] - df['price']
    df['discount_pct'] = (df['profit_potential'] / df['estimated_price']) * 100

    # 5. Filtre : On cherche les "anomalies" de prix (ex: -15% vs marché)
    # On exclut aussi les estimations délirantes (ex: prix > 1M€)
    opps = df[(df['discount_pct'] > 15) & (df['price'] > 50000)].copy()

    return opps.sort_values(by='discount_pct', ascending=False)

def print_report(opps):
    print(f"\n🎯 {len(opps)} OPPORTUNITÉS DÉTECTÉES SUR VALENCE\n")
    # On affiche le Top 10
    for _, row in opps.head(10).iterrows():
        # Lien propre
        url = f"https://www.idealista.com/inmueble/{int(row['propertyCode'])}/"

        print(f"📍 {row['neighborhood']} | {int(row['size'])}m²")
        print(f"💰 Affiche: {int(row['price']):,} €")
        print(f"🤖 Est. IA: {int(row['estimated_price']):,} €")
        print(f"📈 Marge potentielle: {row['discount_pct']:.1f}%")
        print(f"🔗 Lien: {url}")
        print("-" * 45)

if __name__ == "__main__":
    results = detect_opportunities()
    if not results.empty:
        print_report(results)
