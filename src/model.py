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

        # --- ÉTAPE 1 : DÉFINITION DES FEATURES (LA BRIQUE UNIQUEMENT) ---
        # On retire tout ce qui est financier (yield, investment) pour éviter la triche
        self.features = [
            'size', 'rooms', 'bathrooms', 'floor_clean', 'hasLift', 'exterior',
            'light_score', 'district', 'neighborhood', 'latitude', 'longitude',
            'needs_reform', 'geo_cluster', 'has_terrace', 'has_balcony',
            'is_last_floor', 'is_south_facing', 'dist_center', 'dist_beach',
            'dist_turia', 'dist_arts_sciences', 'dist_upv', 'dist_metro_xativa'
        ]

        # Variables textuelles à encoder
        self.cat_features = ['district', 'neighborhood', 'geo_cluster']

        if os.path.exists(self.model_path):
            self.load()

    def train(self, csv_path='data/processed/valence_training_set.csv'):
        # Chargement du dataset généré par le processor
        df = pd.read_csv(csv_path)

        # --- ÉTAPE 2 : SÉCURITÉ GÉO-CLUSTER ---
        # Si pour une raison X le cluster manque, on ne bloque pas tout
        if 'geo_cluster' not in df.columns:
            print("⚠️ geo_cluster manquant, vérifie ton processing.py")
            if 'geo_cluster' in self.cat_features: self.cat_features.remove('geo_cluster')
            if 'geo_cluster' in self.features: self.features.remove('geo_cluster')

        # Nettoyage des données catégorielles
        for col in self.cat_features:
            if col in df.columns:
                df[col] = df[col].fillna("Unknown").astype(str)

        # On ne garde que les features qui existent réellement dans le CSV
        features_to_use = [f for f in self.features if f in df.columns]

        X = df[features_to_use]
        y = np.log1p(df['price']) # On prédit le Log du prix pour plus de précision

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)

        print(f"🚀 Entraînement V5 Robuste sur {len(df)} annonces...")
        print(f"🧠 L'IA analyse {len(features_to_use)} caractéristiques physiques.")

        # --- ÉTAPE 3 : CONFIGURATION CATBOOST (GRID SEARCH OPTIMIZED) ---
        self.model = CatBoostRegressor(
            iterations=2000,
            learning_rate=0.02,
            depth=4,
            l2_leaf_reg=1,
            loss_function='RMSE',
            eval_metric='MAE',
            early_stopping_rounds=100,
            random_seed=42,
            verbose=100
        )

        self.model.fit(
            X_train, y_train,
            cat_features=[c for c in self.cat_features if c in features_to_use],
            eval_set=(X_test, y_test),
            use_best_model=True
        )

        # --- ÉTAPE 4 : ÉVALUATION RÉELLE ---
        preds_log = self.model.predict(X_test)
        mae = mean_absolute_error(np.expm1(y_test), np.expm1(preds_log))
        r2 = r2_score(y_test, preds_log)

        print(f"\n📊 PERFORMANCE FINALE :")
        print(f"Erreur Moyenne (MAE) : {mae:,.0f} €")
        print(f"Fiabilité (R2) : {r2:.2%}")

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
        # Utilise les mêmes colonnes que l'entraînement
        features_to_use = [f for f in self.features if f in df.columns]
        for col in self.cat_features:
            if col in df.columns:
                df[col] = df[col].fillna("Unknown").astype(str)

        preds_log = self.model.predict(df[features_to_use])
        return np.expm1(preds_log)
