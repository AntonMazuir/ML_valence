import pandas as pd
import glob
import os
import json
from pathlib import Path
import numpy as np


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Rayon de la Terre en km
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return 2 * R * np.arctan2(np.sqrt(a), np.sqrt(1-a))

class DataProcessor:
    def __init__(self, raw_dir="data/raw", processed_dir="data/processed"):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def load_all_json(self):
        """Lit tous les fichiers JSON et les combine en un DataFrame unique"""
        all_files = list(self.raw_dir.glob("*.json"))
        if not all_files:
            print("⚠️ Aucun fichier JSON trouvé.")
            return pd.DataFrame()

        dfs = []

        for file in all_files:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'elementList' in data:
                    dfs.append(pd.DataFrame(data['elementList']))

        # Concaténation et suppression des doublons (basé sur l'ID unique Idealista)
        full_df = pd.concat(dfs, ignore_index=True)
        full_df = full_df.drop_duplicates(subset=['propertyCode'])
        print(f"📦 Total : {len(full_df)} annonces uniques collectées.")
        return full_df

    def clean_for_ml(self, df):
        # 1. Sélection élargie
        features = [
            'propertyCode', 'price', 'size', 'rooms', 'bathrooms',
            'floor', 'hasLift', 'exterior', 'district', 'neighborhood',
            'latitude', 'longitude', 'status', 'propertyType',
            'bath_ratio', 'light_score'
        ]
        existing_features = [c for c in features if c in df.columns]
        df = df[existing_features].copy()

        # 2. Nettoyage des types et remplissage des vides
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['size'] = pd.to_numeric(df['size'], errors='coerce')
        df['hasLift'] = df['hasLift'].fillna(False).astype(int)
        df['exterior'] = df['exterior'].fillna(True).astype(int)

        # 3. FEATURE ENGINEERING : Distances stratégiques
        # Coordonnées Plaza del Ayuntamiento (Centre)
        df['dist_center'] = haversine_distance(df['latitude'], df['longitude'], 39.470, -0.376)
        # Coordonnées Plage (Malvarrosa/Cabanyal)
        df['dist_beach'] = haversine_distance(df['latitude'], df['longitude'], 39.470, -0.324)

        # Ratio Salle de bain / Pièces (Standing)
        # Un 2 chambres / 2 SDB vaut plus qu'un 4 chambres / 1 SDB
        df['bath_ratio'] = df['bathrooms'] / df['rooms']
        # On gère les divisions par zéro si rooms=0 (studios)
        df['bath_ratio'] = df['bath_ratio'].replace([np.inf, -np.inf], 1)

        # Score de Lumière/Étage
        # Un étage élevé avec balcon/extérieur = Prime de prix à Valence
        df['light_score'] = df['floor'] * df['exterior']

        # 4. Traitement du "Status"
        # On simplifie : si c'est vide, on considère que c'est "bon état" par défaut
        df['status'] = df['status'].fillna('good')

        # On élimine la Nue-propriété (Nuda propiedad) ou le fait que la maison soit en vente à la mort du propriétaire
        prohibited_terms = ['nuda propiedad', 'usufructo', 'persona mayor', 'inmueble sin posesión']
        mask = df['description'].str.lower().contains('|'.join(prohibited_terms), na=False)
        df = df[~mask]

        # 2. Filtres de "Bon Sens" Immobilier
        # On enlève les biens trop petits (souvent des locaux/garages mal classés)
        # ou les prix au m2 délirants (erreurs de saisie)
        df['price_m2'] = df['price'] / df['size']

        df = df[
            (df['size'] >= 30) & (df['size'] <= 400) &      # Tailles réalistes
            (df['price_m2'] >= 700) & (df['price_m2'] <= 7000)] # Prix m2 cohérents pour Valence

        # 5. Traitement des étages (Floor)
        # On transforme 'bj' (bajo) en 0, 'en' (entresuelo) en 0.5, etc.
        floor_map = {'bj': 0, 'en': 0.5, 'st': 0, 'ss': -1}
        df['floor'] = df['floor'].replace(floor_map)
        df['floor'] = pd.to_numeric(df['floor'], errors='coerce').fillna(1) # Étage 1 par défaut

        # 6. Filtres Anti-Bruit (Outliers)
        # On enlève le luxe extrême et les erreurs de saisie
        df = df[(df['price'] > 40000) & (df['price'] < 1200000)]
        df = df[(df['size'] > 20) & (df['size'] < 400)]

        return df

    def save_processed(self, df):
        """Sauvegarde le dataset propre"""
        output_path = self.processed_dir / "valence_training_set.csv"
        df.to_csv(output_path, index=False)
        print(f"💾 Dataset prêt pour l'IA : {output_path}")

if __name__ == "__main__":
    processor = DataProcessor()
    raw_data = processor.load_all_json()
    if not raw_data.empty:
        clean_data = processor.clean_for_ml(raw_data)
        processor.save_processed(clean_data)
