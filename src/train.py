import os
import pandas as pd
import numpy as np
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt

def train_model():
    # 1. Chargement et filtres
    df = pd.read_csv('data/processed/valence_training_set.csv')
    # Remplacer les NaN par du texte pour neighborhood et district
    df['neighborhood'] = df['neighborhood'].fillna("Unknown")
    df['district'] = df['district'].fillna("Unknown")
    df['status'] = df['status'].fillna("good") # Sécurité pour l'état du bien

    # On garde une fourchette réaliste pour l'investissement
    df = df[(df['price'] > 40000) & (df['price'] < 900000)]

    # 2. Sélection étendue des colonnes
    # On ajoute nos nouvelles colonnes calculées par le processing
    features = [
        'size', 'rooms', 'bathrooms', 'floor', 'hasLift',
        'exterior', 'district', 'status', 'neighborhood',
        'dist_center', 'dist_beach', 'latitude', 'longitude'
    ]

    X = df[features]
    # On utilise le LOG pour stabiliser l'apprentissage
    y = np.log1p(df['price'])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 3. Configuration CatBoost
    # Attention : status est maintenant une catégorie !
    cat_features = ['district', 'status', 'neighborhood']

    model = CatBoostRegressor(
        iterations=1000,         # On peut monter car on a le Early Stopping
        learning_rate=0.04,
        depth=8,
        loss_function='RMSE',    # RMSE fonctionne mieux sur le Log
        early_stopping_rounds=50, # Arrête si le score sur X_test ne s'améliore plus
        allow_writing_files=False,
        verbose=100
    )

    # 4. Entraînement
    print("🚀 Entraînement du modèle avec Log-Transform...")
    model.fit(X_train, y_train, cat_features=cat_features, eval_set=(X_test, y_test))

    # 5. Évaluation (On doit ré-inverser le log pour les euros)
    preds_log = model.predict(X_test)
    preds = np.expm1(preds_log)
    actuals = np.expm1(y_test)

    mae = mean_absolute_error(actuals, preds)
    r2 = r2_score(y_test, preds_log) # R2 sur le log est plus représentatif

    print(f"\n📊 RÉSULTATS FINAUX :")
    print(f"Erreur Moyenne (MAE) : {mae:,.0f} €")
    print(f"Score R2 (Fiabilité) : {r2:.2%}")

    # Feature Importance
    importances = model.get_feature_importance()
    for score, name in sorted(zip(importances, features), reverse=True):
        print(f"{name}: {score:.2f}%")

    # On sauvegarde le modèle pour pouvoir l'utiliser ailleurs !
    # Créer le dossier s'il n'existe pas
    if not os.path.exists('models'):
        os.makedirs('models')

    model.save_model('models/valence_model.cbm')
    return model

if __name__ == "__main__":
    train_model()
