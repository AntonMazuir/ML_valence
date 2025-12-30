import os
import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

class ValenceModel:
    def __init__(self, model_path='models/valence_model.cbm'):
        self.model_path = model_path
        # On définit le modèle avec tes réglages optimisés
        self.model = CatBoostRegressor(
            iterations=1000,
            learning_rate=0.04,
            depth=8,
            loss_function='RMSE',
            early_stopping_rounds=50,
            allow_writing_files=False
        )
        if os.path.exists(self.model_path):
            self.model.load_model(self.model_path)

    def train(self, csv_path='data/processed/valence_training_set.csv'):
        """Cette méthode sera appelée par main.py"""
        # 1. Chargement et filtres
        df = pd.read_csv(csv_path)
        df['neighborhood'] = df['neighborhood'].fillna("Unknown")
        df['district'] = df['district'].fillna("Unknown")
        df['status'] = df['status'].fillna("good")
        df = df[(df['price'] > 40000) & (df['price'] < 900000)]

        # 2. Features
        features = [
            'size', 'rooms', 'bathrooms', 'floor', 'hasLift',
            'exterior', 'district', 'status', 'neighborhood',
            'dist_center', 'dist_beach', 'latitude', 'longitude',
            'bath_ratio', 'light_score'
        ]

        X = df[features]
        y = np.log1p(df['price'])

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # 3. Entraînement
        print(f"🚀 Entraînement sur {len(df)} annonces avec Log-Transform...")
        self.model.fit(
            X_train, y_train,
            cat_features=['district', 'status', 'neighborhood'],
            eval_set=(X_test, y_test),
            verbose=100
        )

        # 4. Évaluation rapide
        preds_log = self.model.predict(X_test)
        mae = mean_absolute_error(np.expm1(y_test), np.expm1(preds_log))
        print(f"\n📊 MAE : {mae:,.0f} €")

        # 5. Sauvegarde
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        self.model.save_model(self.model_path)
        print(f"✅ Modèle sauvegardé : {self.model_path}")

    def predict_one(self, property_dict):
        """Utilisé pour tester un bien précis ou par le scanner"""
        df_new = pd.DataFrame([property_dict])
        pred_log = self.model.predict(df_new)[0]
        return np.expm1(pred_log)
