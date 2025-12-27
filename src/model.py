import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
import os

class ValenceModel:
    def __init__(self, model_path='models/valence_model.cbm'):
        self.model_path = model_path
        # On définit les paramètres ICI
        self.model = CatBoostRegressor(
            iterations=500,
            learning_rate=0.05,
            loss_function='MAE',
            allow_writing_files=False
        )
        # On charge le modèle existant s'il y en a un
        if os.path.exists(self.model_path):
            self.model.load_model(self.model_path)

    def train(self, csv_path='data/processed/valence_training_set.csv'):
        """Entraîne le modèle sur le dataset traité"""
        df = pd.read_csv(csv_path)

        features = ['size', 'rooms', 'bathrooms', 'floor', 'hasLift', 'exterior', 'district', 'latitude', 'longitude']
        X = df[features]
        y = df['price']

        cat_features = ['district']

        print("🏋️ Entraînement en cours...")
        # Le fit() ne prend plus que les données et les colonnes catégorielles
        self.model.fit(
            X, y,
            cat_features=cat_features,
            verbose=100
        )

        os.makedirs('models', exist_ok=True)
        self.model.save_model(self.model_path)
        print(f"✅ Modèle sauvegardé dans {self.model_path}")


    def predict_one(self, property_dict):
        """Prédit le prix pour un dictionnaire de caractéristiques"""
        df_new = pd.DataFrame([property_dict])
        prediction = self.model.predict(df_new)[0]
        return prediction

# --- EXEMPLE D'UTILISATION ---
if __name__ == "__main__":
    ai = ValenceModel()

    # Pour ré-entraîner :
    ai.train()

    # Pour tester une annonce :
    test_appart = {
        'size': 140,
        'rooms': 4,
        'bathrooms': 1,
        'floor': 0,
        'hasLift': False,
        'exterior': True,
        'district': "El Cabanyal",
        'latitude': 39.46,
        'longitude': -0.33
    }

    prix = ai.predict_one(test_appart)
    print(f"💰 Estimation IA : {prix:,.0f} €")
