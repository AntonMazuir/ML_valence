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

        self.METRO_HUBS = [(39.467, -0.377), (39.471, -0.384), (39.482, -0.364), (39.453, -0.349), (39.461, -0.392), (39.474, -0.334), (39.489, -0.375)]
        self.TURIA_LINE = [(39.481, -0.402), (39.479, -0.387), (39.475, -0.376), (39.468, -0.358), (39.457, -0.345)]
        self.COAST_LINE = [(39.483, -0.322), (39.471, -0.324), (39.458, -0.330)]

        self.VALENCIA_MARKET_DATA = {
            'Exposició': (4364, 0.158), 'Mestalla': (3646, 0.235), 'Aiora': (2701, 0.133),
            'Albors': (2927, 0.331), 'La Creu del Grau': (2739, 0.269), 'Penya-Roja': (4148, 0.057),
            'El Carme': (3046, 0.301), 'El Mercat': (2701, 0.328), 'El Pilar': (2927, 0.337),
            'La Seu': (2739, 0.025), 'La Xerea': (4148, 0.161), 'Sant Francesc': (4072, 0.199),
            'El Pla del Remei': (4863, 0.195), 'Gran Vía': (4348, 0.198), 'Russafa': (3852, 0.176),
            'Arrancapins': (3154, 0.176), 'El Botànic': (3569, 0.252), 'La Petxina': (3155, 0.215),
            'La Roqueta': (3500, 0.135), 'Campanar': (2746, 0.206), 'El Calvari': (2500, 0.354),
            'Sant Pau': (3966, 0.145), 'Vara de Quart': (2126, 0.186), 'Patraix': (2587, 0.210),
            'Benimaclet': (2998, 0.270), 'Ciutat de les Arts i de les Ciencies': (4429, 0.332),
            'En Corts': (2958, 0.270), 'Malilla': (2725, 0.271), 'Ciutat Jardí': (2917, 0.129),
            'L\'Amistat': (2682, 0.196), 'L\'Illa Perduda': (2778, 0.277), 'Beteró': (2850, 0.281),
            'El Cabanyal-El Canyamelar': (2967, 0.176), 'Playa de la Malvarrosa': (2805, 0.392)
        }
        self.VALENCIA_DISTRICT_DATA = {
            'Ciutat Vella': (3982, 0.217), 'L\'Eixample': (4160, 0.151), 'Extramurs': (3260, 0.171),
            'Campanar': (3099, 0.026), 'Patraix': (2394, 0.197), 'Quatre Carreres': (2913, 0.306),
            'Algirós': (2869, 0.174), 'Poblats Marítims': (2725, 0.221), 'Camins al Grau': (3046, 0.239)
        }

    def get_min_dist(self, lat, lon, points):
        return min([haversine_distance(lat, lon, p[0], p[1]) for p in points])

    def load_all_json(self):
        all_files = list(self.raw_dir.glob("*.json"))
        if not all_files:
            return pd.DataFrame()
        dfs = [pd.DataFrame(json.load(open(f, 'r', encoding='utf-8'))['elementList']) for f in all_files if 'elementList' in json.load(open(f, 'r', encoding='utf-8'))]
        full_df = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=['propertyCode'])
        print(f"📦 Total : {len(full_df)} annonces uniques collectées.")
        return full_df

    def add_dynamic_trends(self, df):
        """
        Calcule la croissance en temps réel et le score de Momentum.
        Sécurise les divisions par zéro pour éviter les 'inf' sur le dashboard.
        """
        # 1. Récupération du prix de référence (Mars 2025)
        # On tente par quartier, sinon par district
        df['ref_price_m2'] = df['neighborhood'].map(lambda x: self.VALENCIA_MARKET_DATA.get(x, (0,0))[0])

        mask_ref = (df['ref_price_m2'] <= 0)
        df.loc[mask_ref, 'ref_price_m2'] = df.loc[mask_ref, 'district'].map(
            lambda x: self.VALENCIA_DISTRICT_DATA.get(x, (2919, 0))[0] # 2919 = moyenne Valence
        )

        # 2. Évolution Temps Réel (Prix Actuel / Prix Réf) - 1
        df['realtime_growth'] = (df['priceByArea'] / df['ref_price_m2']) - 1

        # 3. Récupération de la croissance historique (Variation annuelle %)
        df['historical_growth'] = df['neighborhood'].map(
            lambda x: float(self.VALENCIA_MARKET_DATA.get(x, (0, 0))[1])
        )

        # Si quartier inconnu (0), on prend le district
        mask_hist = (df['historical_growth'] <= 0)
        df.loc[mask_hist, 'historical_growth'] = df.loc[mask_hist, 'district'].map(
            lambda x: float(self.VALENCIA_DISTRICT_DATA.get(x, (0, 0.21))[1]) # 0.21 = +21% moyenne Valence
        )

        # 4. SÉCURITÉ ANTI-INF : On s'assure que historical_growth n'est jamais 0
        # Une valeur de 0.1 (10%) est une base saine pour éviter la division par zéro
        df['historical_growth'] = df['historical_growth'].replace(0, 0.1)
        df['historical_growth'] = df['historical_growth'].fillna(0.1)

        # 5. Calcul du Momentum Score
        # Un score de 1.0 signifie que le quartier monte au même rythme que l'an dernier
        df['momentum_score'] = df['realtime_growth'] / df['historical_growth']

        # On limite entre -5 et +10 pour garder des graphiques lisibles
        df['momentum_score'] = df['momentum_score'].replace([np.inf, -np.inf], 0)
        df['momentum_score'] = df['momentum_score'].clip(-5, 10).fillna(0)

        return df

    def clean_for_ml(self, df):
        if 'description' not in df.columns: df['description'] = ""
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['size'] = pd.to_numeric(df['size'], errors='coerce')
        df['priceByArea'] = pd.to_numeric(df['priceByArea'], errors='coerce')
        df['bathrooms'] = pd.to_numeric(df['bathrooms'], errors='coerce').fillna(1)
        df['rooms'] = pd.to_numeric(df['rooms'], errors='coerce').fillna(1)

        for poi_name, coords in self.VALENCE_POI.items():
            df[poi_name] = haversine_distance(df['latitude'], df['longitude'], coords[0], coords[1])

        df['dist_metro'] = df.apply(lambda r: self.get_min_dist(r['latitude'], r['longitude'], self.METRO_HUBS), axis=1)
        df['dist_turia'] = df.apply(lambda r: self.get_min_dist(r['latitude'], r['longitude'], self.TURIA_LINE), axis=1)
        df['dist_beach'] = df.apply(lambda r: self.get_min_dist(r['latitude'], r['longitude'], self.COAST_LINE), axis=1)

        df['bath_ratio'] = df['bathrooms'] / (df['rooms'] + 0.1)
        floor_map = {'bj': 0, 'en': 0.5, 'st': 0, 'ss': -1}
        df['floor_clean'] = df['floor'].replace(floor_map)
        df['floor_clean'] = pd.to_numeric(df['floor_clean'], errors='coerce').fillna(1)

        # Correction Warning Future Behavior
        df['hasLift'] = df['hasLift'].infer_objects(copy=False).fillna(False).astype(int)
        df['exterior'] = df['exterior'].infer_objects(copy=False).fillna(True).astype(int)

        # Recalcul de light_score (qui manquait dans ton erreur)
        df['light_score'] = df['floor_clean'] * df['exterior']

        df['is_house'] = df['propertyType'].apply(lambda x: 1 if x in ['chalet', 'house'] else 0)
        df['needs_reform'] = (df['status'] == 'renew').astype(int)
        df['is_ground_floor'] = df['floor'].apply(lambda x: 1 if x == 'bj' else 0)
        df['is_penthouse'] = (df['propertyType'] == 'penthouse').astype(int)
        df['has_parking'] = df['parkingSpace'].apply(lambda x: 1 if isinstance(x, dict) and x.get('hasParkingSpace') else 0)

        df = self.add_dynamic_trends(df)

        prohibited_terms = ['nuda propiedad', 'usufructo', 'persona mayor', 'inmueble sin posesión', 'subasta', 'judicial', 'ocupado']
        mask_prohib = df['description'].str.lower().str.contains('|'.join(prohibited_terms), na=False)
        df = df[~mask_prohib].copy()

        desc = df['description'].str.lower()
        df['has_terrace'] = desc.str.contains('terraza|atico|ático', na=False).astype(int)
        df['has_balcony'] = desc.str.contains('balcón|balcon', na=False).astype(int)
        df['is_last_floor'] = ((df['is_penthouse'] == 1) | desc.str.contains('última planta|ultima planta|sin vecinos arriba', na=False)).astype(int)
        df['is_south_facing'] = desc.str.contains('orientación sur|orientacion sur|soleado', na=False).astype(int)

        risk_terms = ['ocupado', 'okupa', 'sin posesión', 'inmueble ilegal', 'proindiviso', 'subasta']
        df['is_risky'] = desc.str.contains('|'.join(risk_terms), na=False).astype(int)
        df = df[df['is_risky'] == 0].copy()

        df = self.add_geo_clusters(df)

        poi_columns = [c for c in df.columns if c.startswith('dist_')]
        trend_columns = ['realtime_growth', 'momentum_score', 'historical_growth']

        # RÉINTÉGRATION DE 'exterior' et 'light_score'
        final_features = [
            'propertyCode', 'price', 'size', 'rooms', 'bathrooms', 'floor_clean',
            'hasLift', 'exterior', 'light_score', 'district', 'neighborhood',
            'latitude', 'longitude', 'bath_ratio', 'is_house', 'needs_reform',
            'is_ground_floor', 'has_parking', 'is_penthouse', 'geo_cluster',
            'has_terrace', 'has_balcony', 'is_last_floor', 'is_south_facing'
        ] + poi_columns + trend_columns

        return df[[c for c in final_features if c in df.columns]]

    def add_geo_clusters(self, df, n_clusters=15):
        coords = df[['latitude', 'longitude']]
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df['geo_cluster'] = kmeans.fit_predict(coords).astype(str)
        return df

    def save_processed(self, df):
        output_path = self.processed_dir / "valence_training_set.csv"
        df.to_csv(output_path, index=False)
        print(f"💾 Dataset prêt pour l'IA : {output_path}")

if __name__ == "__main__":
    processor = DataProcessor()
    raw_data = processor.load_all_json()
    if not raw_data.empty:
        clean_data = processor.clean_for_ml(raw_data)
        processor.save_processed(clean_data)
