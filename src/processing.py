import pandas as pd
import glob
import os
import json
from pathlib import Path

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
        """Nettoyage chirurgical pour le modèle"""
        # 1. Sélection des features prioritaires
        features = [
            'propertyCode', 'price', 'size', 'rooms', 'bathrooms',
            'floor', 'hasLift', 'exterior', 'district', 'neighborhood',
            'latitude', 'longitude', 'status', 'propertyType'
        ]

        # On ne garde que les colonnes qui existent vraiment
        existing_features = [c for c in features if c in df.columns]
        df = df[existing_features].copy()

        # 2. Nettoyage des types
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['size'] = pd.to_numeric(df['size'], errors='coerce')

        # Étages : on remplace les valeurs textuelles par des chiffres
        # (ex: 'bj' -> 0, 'en' -> 0.5)
        df['floor'] = pd.to_numeric(df['floor'], errors='coerce').fillna(0)

        # 3. Calcul de la cible (Target)
        df['price_per_m2'] = df['price'] / df['size']

        # 4. Filtre de qualité (on enlève le bruit)
        df = df[df['price'] > 30000]  # Pas de garages
        df = df[df['size'] > 15]      # Pas de débarras

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
