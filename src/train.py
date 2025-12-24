import pandas as pd
import numpy as np
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt

def train_model():
    # 1. Chargement des données
    df = pd.read_csv('data/processed/valence_training_set.csv')
    df = df[df['price'] < 800000] # On enlève le très haut luxe qui fausse tout

    # 2. Sélection des colonnes (On ignore l'ID et les prix au m2 pour ne pas tricher)
    features = ['size', 'rooms', 'bathrooms', 'floor', 'hasLift', 'exterior', 'district', 'latitude', 'longitude']
    target = 'price'

    X = df[features]
    y = df[target]

    # 3. Split : 80% pour apprendre, 20% pour tester
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Configuration de CatBoost
    # On précise quelles colonnes sont des catégories (texte)
    cat_features = ['district']

    model = CatBoostRegressor(
        iterations=500,
        learning_rate=0.05,
        depth=6,
        allow_writing_files=False,
        loss_function='MAE', # On optimise l'Erreur Absolue Moyenne
        verbose=100
    )

    # 5. Entraînement
    print("🚀 Entraînement du modèle en cours...")
    model.fit(X_train, y_train, cat_features=cat_features, eval_set=(X_test, y_test))

    # 6. Évaluation
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    print(f"\n📊 RÉSULTATS :")
    print(f"Erreur Moyenne (MAE) : {mae:,.0f} €")
    print(f"Score R2 (Fiabilité) : {r2:.2%}")

    # Voir quelles caractéristiques comptent le plus
    importances = model.get_feature_importance()
    feature_names = X.columns
    for score, name in sorted(zip(importances, feature_names), reverse=True):
        print(f"{name}: {score:.2f}%")

    return model

if __name__ == "__main__":
    train_model()
