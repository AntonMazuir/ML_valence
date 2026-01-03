import pandas as pd
import glob
import os
import json
from pathlib import Path
import numpy as np
from sklearn.cluster import KMeans


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
        self.VALENCE_POI = {
            'dist_center': (39.470, -0.376),
            'dist_beach': (39.470, -0.324),
            'dist_turia': (39.473, -0.364),
            'dist_arts_sciences': (39.454, -0.350),
            'dist_upv': (39.479, -0.337),
            'dist_metro_xativa': (39.467, -0.377)
        }
        self.METRO_HUBS = [
            (39.467, -0.377), # Xàtiva (Centre)
            (39.471, -0.384), # Àngel Guimerà (Croisement lignes)
            (39.482, -0.364), # Benimaclet (Nord / Université)
            (39.453, -0.349), # Amistat (Zone Est)
            (39.461, -0.392), # Av. del Cid (Ouest)
            (39.474, -0.334), # Marítim (Port/Plage)
            (39.489, -0.375)  # Empalme (Nord-Ouest)
        ]

        self.TURIA_LINE = [
            (39.481, -0.402), # Entrée Bioparc
            (39.479, -0.387), # Musée des Sciences Naturelles
            (39.475, -0.376), # Pont de Serranos
            (39.468, -0.358), # Palais de la Musique
            (39.457, -0.345)  # Cité des Arts
        ]

        self.COAST_LINE = [
            (39.483, -0.322), # Patacona
            (39.471, -0.324), # Malvarrosa
            (39.458, -0.330)  # Marina / Port
        ]

    def get_min_dist(self, lat, lon, points):
        return min([haversine_distance(lat, lon, p[0], p[1]) for p in points])

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
        # 1. Préparation initiale
        if 'description' not in df.columns:
            df['description'] = ""

        # 2. Nettoyage des types
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['size'] = pd.to_numeric(df['size'], errors='coerce')
        df['bathrooms'] = pd.to_numeric(df['bathrooms'], errors='coerce').fillna(1)
        df['rooms'] = pd.to_numeric(df['rooms'], errors='coerce').fillna(1)

        # 3. FEATURE ENGINEERING : Distances POI (Plage, Centre, etc.)
        # On boucle sur tous les dictionnaires VALENCE_POI définis dans le __init__
        for poi_name, coords in self.VALENCE_POI.items():
            df[poi_name] = haversine_distance(
                df['latitude'], df['longitude'],
                coords[0], coords[1]
            )
        # Distance au Centre (Point unique reste pertinent)
        df['dist_center'] = haversine_distance(df['latitude'], df['longitude'], 39.470, -0.376)

        # Distances intelligentes (Plus proche voisin)
        df['dist_metro'] = df.apply(lambda r: self.get_min_dist(r['latitude'], r['longitude'], self.METRO_HUBS), axis=1)
        df['dist_turia'] = df.apply(lambda r: self.get_min_dist(r['latitude'], r['longitude'], self.TURIA_LINE), axis=1)
        df['dist_beach'] = df.apply(lambda r: self.get_min_dist(r['latitude'], r['longitude'], self.COAST_LINE), axis=1)

        # Distance UPV (Point unique pertinent pour la zone étudiante)
        df['dist_upv'] = haversine_distance(df['latitude'], df['longitude'], 39.479, -0.337)


        # 4. FEATURE ENGINEERING : Standing
        df['bath_ratio'] = df['bathrooms'] / (df['rooms'] + 0.1)

        floor_map = {'bj': 0, 'en': 0.5, 'st': 0, 'ss': -1}
        df['floor'] = df['floor'].replace(floor_map)
        df['floor'] = pd.to_numeric(df['floor'], errors='coerce').fillna(1)

        df['hasLift'] = df['hasLift'].fillna(False).astype(int)
        df['exterior'] = df['exterior'].fillna(True).astype(int)
        df['light_score'] = df['floor'] * df['exterior']

        # 1. Typologie de bien (Maison vs Appartement)
        # Le "Chalet" au Cabanyal est une maison de pêcheur, très prisée.
        df['is_house'] = df['propertyType'].apply(lambda x: 1 if x in ['chalet', 'house'] else 0)

        # 2. État de rénovation (Le point CRUCIAL)
        # Si status == 'renew', le prix est bas car il faut rajouter 500-800€/m2 de travaux.
        df['needs_reform'] = (df['status'] == 'renew').astype(int)

        # 3. Rez-de-chaussée (Bajo)
        # 'bj' dans le JSON = Planta Baja. Souvent moins cher et plus bruyant.
        df['is_ground_floor'] = df['floor'].apply(lambda x: 1 if x == 'bj' else 0)

        # 4. Stationnement (Parking)
        df['has_parking'] = df['parkingSpace'].apply(
            lambda x: 1 if isinstance(x, dict) and x.get('hasParkingSpace') else 0
        )

        # 5. Attributs Premium (Penthouse / Atico)
        df['is_penthouse'] = (df['propertyType'] == 'penthouse').astype(int)

        # 5. FILTRAGE (Nue-propriété et Cohérence)
        prohibited_terms = ['nuda propiedad', 'usufructo', 'persona mayor', 'inmueble sin posesión', 'subasta']
        mask = df['description'].str.lower().str.contains('|'.join(prohibited_terms), na=False)
        df = df[~mask].copy()

        df['price_m2'] = df['price'] / df['size']
        df = df[
            (df['size'] >= 30) & (df['size'] <= 400) &
            (df['price_m2'] >= 800) & (df['price_m2'] <= 7500) &
            (df['price'] > 45000) & (df['price'] < 1000000)
        ].copy()

        # 6. Ajout du Clustering K-Means
        df = self.add_geo_clusters(df)

        # 6. SÉLECTION FINALE (Mise à jour pour inclure TOUS les POI)
        # On prend les features de base + toutes les colonnes qui commencent par 'dist_'
        poi_columns = [c for c in df.columns if c.startswith('dist_')]

        final_features = [
            'propertyCode', 'price', 'size', 'rooms', 'bathrooms',
            'floor', 'hasLift', 'exterior', 'district', 'neighborhood',
            'latitude', 'longitude', 'status', 'bath_ratio', 'light_score',
            'geo_cluster', 'is_house', 'needs_reform', 'is_ground_floor',
            'has_parking', 'is_penthouse'
        ] + poi_columns

        return df[[c for c in final_features if c in df.columns]]


    def add_geo_clusters(self, df, n_clusters=15):
        # On crée des clusters basés uniquement sur Latitude/Longitude
        coords = df[['latitude', 'longitude']]
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df['geo_cluster'] = kmeans.fit_predict(coords).astype(str)
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
