import os
import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

class ValenceModel:
    def __init__(self, model_path='models/valence_model.cbm'):
        self.model_path = model_path
        self.model = None
        # Liste exhaustive des 32 variables (alignée sur processing.py)
        self.features = [
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
        # Colonnes que l'IA traite comme du texte/catégories
        self.cat_features = ['district', 'neighborhood', 'geo_cluster']

        if os.path.exists(self.model_path):
            self.load()

    def train(self, csv_path='data/processed/valence_training_set.csv'):
        df = pd.read_csv(csv_path)

        # Nettoyage de sécurité pour les catégories
        for col in self.cat_features:
            df[col] = df[col].fillna("Unknown").astype(str)

        X = df[self.features]
        # Utilisation du Log pour stabiliser les prédictions sur les gros montants
        y = np.log1p(df['price'])

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)

        print(f"🚀 Entraînement V5 Industrielle sur {len(df)} annonces...")

        # Initialisation propre du régresseur
        self.model = CatBoostRegressor(
            iterations=1500,        # Plus d'itérations pour plus de features
            learning_rate=0.03,    # Plus lent pour plus de précision
            depth=8,
            loss_function='RMSE',
            eval_metric='MAE',     # On surveille l'erreur en euros
            early_stopping_rounds=100,
            random_seed=42,
            verbose=100
        )

        self.model.fit(
            X_train, y_train,
            cat_features=self.cat_features,
            eval_set=(X_test, y_test),
            use_best_model=True
        )

        # Évaluation
        preds_log = self.model.predict(X_test)
        actuals = np.expm1(y_test)
        predictions = np.expm1(preds_log)

        mae = mean_absolute_error(actuals, predictions)
        r2 = r2_score(y_test, preds_log)

        print(f"\n📊 RÉSULTATS V5 :")
        print(f"Erreur Moyenne (MAE) : {mae:,.0f} €")
        print(f"Précision (R2 Score) : {r2:.2%}")

        # Feature Importance : Savoir ce qui fait le prix à Valence
        print("\n🔥 Top 5 facteurs déterminants :")
        importances = self.model.get_feature_importance()
        for score, name in sorted(zip(importances, self.features), reverse=True)[:5]:
            print(f"- {name}: {score:.2f}%")

        self.save()

    def save(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        self.model.save_model(self.model_path)
        print(f"✅ Modèle sauvegardé : {self.model_path}")

    def load(self):
        self.model = CatBoostRegressor()
        self.model.load_model(self.model_path)
        print("🧠 Modèle V5 chargé.")

    def predict(self, df):
        # Prétraitement des catégories pour le scan
        for col in self.cat_features:
            df[col] = df[col].fillna("Unknown").astype(str)
        preds_log = self.model.predict(df[self.features])
        return np.expm1(preds_log)
