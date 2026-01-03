import os
import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

class ValenceModel:
    def __init__(self, model_path='models/valence_model.cbm'):
        self.model_path = model_path
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
        # 1. Chargement et filtres
        df = pd.read_csv(csv_path)
        df['neighborhood'] = df['neighborhood'].fillna("Unknown")
        df['district'] = df['district'].fillna("Unknown")
        df['status'] = df['status'].fillna("good")
        df['geo_cluster'] = df['geo_cluster'].astype(str) # On s'assure que c'est du texte

        # 2. Features (Nettoyées et complètes)
        features = [
            'size', 'rooms', 'bathrooms', 'floor', 'hasLift', 'exterior',
            'district', 'status', 'neighborhood', 'latitude', 'longitude',
            'bath_ratio', 'light_score', 'geo_cluster',
            'dist_center', 'dist_beach', 'dist_turia', 'dist_arts_sciences',
            'dist_upv', 'dist_metro_xativa', 'dist_metro',
            'is_house', 'needs_reform', 'is_ground_floor',
            'has_parking', 'is_penthouse'
        ]

        X = df[features]
        y = np.log1p(df['price'])

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # 3. Entraînement
        print(f"🚀 Entraînement V3 sur {len(df)} annonces...")

        # Liste des colonnes catégorielles
        cat_features = ['district', 'status', 'neighborhood', 'geo_cluster']

        self.model.fit(
            X_train, y_train,
            cat_features=cat_features,
            eval_set=(X_test, y_test),
            verbose=100
        )

        # 4. Évaluation
        preds_log = self.model.predict(X_test)
        mae = mean_absolute_error(np.expm1(y_test), np.expm1(preds_log))
        print(f"\n📊 MAE FINAL : {mae:,.0f} €")

        # 5. Sauvegarde
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        self.model.save_model(self.model_path)
        print(f"✅ Modèle sauvegardé : {self.model_path}")

    def predict_one(self, property_dict):
        df_new = pd.DataFrame([property_dict])
        pred_log = self.model.predict(df_new)[0]
        return np.expm1(pred_log)
