import pandas as pd
import glob
import os
import json
from pathlib import Path
import numpy as np
from sklearn.cluster import KMeans

pd.set_option('future.no_silent_downcasting', True)

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

        self.VALENCIA_RENT_DATA = {
            'El Carme': 19.5, 'La Seu': 21.0, 'Sant Francesc': 22.0, 'Russafa': 18.5,
            'El Pla del Remei': 22.5, 'Gran Vía': 20.0, 'Arrancapins': 16.5,
            'Benimaclet': 15.0, 'El Cabanyal-El Canyamelar': 17.5, 'Aiora': 14.5,
            'Patraix': 13.5, 'Nou Moles': 13.0, 'La Petxina': 16.0, 'Campanar': 17.0,
            'Malilla': 14.0, 'En Corts': 14.5, 'Penya-Roja': 19.0, 'Algirós': 15.5
        }

        self.VALENCE_POI = {
            'dist_center': (39.470, -0.376), 'dist_beach': (39.470, -0.324),
            'dist_turia': (39.473, -0.364), 'dist_arts_sciences': (39.454, -0.350),
            'dist_upv': (39.479, -0.337), 'dist_metro_xativa': (39.467, -0.377)
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
        if not all_files: return pd.DataFrame()
        dfs = []
        for f in all_files:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if 'elementList' in data: dfs.append(pd.DataFrame(data['elementList']))
        full_df = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=['propertyCode'])
        print(f"📦 Total : {len(full_df)} annonces uniques.")
        return full_df

    def add_dynamic_trends(self, df):
        df['ref_price_m2'] = df['neighborhood'].map(lambda x: self.VALENCIA_MARKET_DATA.get(x, (0,0))[0])
        mask_ref = (df['ref_price_m2'] <= 0)
        df.loc[mask_ref, 'ref_price_m2'] = df.loc[mask_ref, 'district'].map(lambda x: self.VALENCIA_DISTRICT_DATA.get(x, (2919, 0))[0])
        df['realtime_growth'] = (df['priceByArea'] / df['ref_price_m2']) - 1
        df['historical_growth'] = df['neighborhood'].map(lambda x: float(self.VALENCIA_MARKET_DATA.get(x, (0, 0))[1]))
        mask_hist = (df['historical_growth'] <= 0)
        df.loc[mask_hist, 'historical_growth'] = df.loc[mask_hist, 'district'].map(lambda x: float(self.VALENCIA_DISTRICT_DATA.get(x, (0, 0.21))[1]))
        df['historical_growth'] = df['historical_growth'].replace(0, 0.1).fillna(0.1)
        df['momentum_score'] = df['realtime_growth'] / df['historical_growth']
        df['momentum_score'] = df['momentum_score'].replace([np.inf, -np.inf], 0).clip(-5, 10).fillna(0)
        return df

    def add_airbnb_logic(self, df):
        desc = df['description'].str.lower()
        tourist_keywords = [
            'licencia turística', 'licencia turistica', 'vft', 'apartamento turístico',
            'uso turístico', 'turístico', 'vacacional', 'airbnb', 'corta estancia',
            'compatibilidad turística', 'primer piso compatible'
        ]
        df['is_airbnb_ready'] = desc.str.contains('|'.join(tourist_keywords), na=False).astype(int)

        def estimate_airbnb_revenue(row):
            if row['is_airbnb_ready'] == 0: return 0
            base_adr = 140 if row['district'] in ['Ciutat Vella', 'L\'Eixample', 'Poblats Marítims'] else 95
            return (base_adr * 30 * 0.70) * 0.75

        df['est_monthly_airbnb_net'] = df.apply(estimate_airbnb_revenue, axis=1)
        return df

    def add_investment_math(self, df):
        def estimate_reno(row):
            size = row['size']
            if row.get('needs_reform') == 1: return size * 1850
            else: return size * 1150

        df['est_renovation_cost'] = df.apply(estimate_reno, axis=1)
        df['acquisition_costs'] = df['price'] * 0.125
        df['total_investment'] = df['price'] + df['acquisition_costs'] + df['est_renovation_cost']
        df['rent_m2'] = df['neighborhood'].map(lambda x: self.VALENCIA_RENT_DATA.get(x, 14.5))
        df['est_monthly_rent'] = df['size'] * df['rent_m2']

        df['net_yield'] = ((df['est_monthly_rent'] * 12) / df['total_investment']) * 100
        df['yield_airbnb'] = ((df['est_monthly_airbnb_net'] * 12) / df['total_investment']) * 100
        df['best_yield'] = df[['net_yield', 'yield_airbnb']].max(axis=1)
        return df

    def clean_for_ml(self, df):
        # --- ÉTAPE 1 : NETTOYAGE ET CONVERSION NUMÉRIQUE ---
        if 'description' not in df.columns: df['description'] = ""
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['size'] = pd.to_numeric(df['size'], errors='coerce')
        df['priceByArea'] = pd.to_numeric(df['priceByArea'], errors='coerce')
        df['bathrooms'] = pd.to_numeric(df['bathrooms'], errors='coerce').fillna(1)
        df['rooms'] = pd.to_numeric(df['rooms'], errors='coerce').fillna(1)

        # --- ÉTAPE 2 : CALCUL DES DISTANCES (POI) ---
        for poi_name, coords in self.VALENCE_POI.items():
            df[poi_name] = haversine_distance(df['latitude'], df['longitude'], coords[0], coords[1])

        df['dist_metro'] = df.apply(lambda r: self.get_min_dist(r['latitude'], r['longitude'], self.METRO_HUBS), axis=1)
        df['dist_turia'] = df.apply(lambda r: self.get_min_dist(r['latitude'], r['longitude'], self.TURIA_LINE), axis=1)
        df['dist_beach'] = df.apply(lambda r: self.get_min_dist(r['latitude'], r['longitude'], self.COAST_LINE), axis=1)

        # --- ÉTAPE 3 : CARACTÉRISTIQUES PHYSIQUES & WARNING FIXES ---
        df['bath_ratio'] = df['bathrooms'] / (df['rooms'] + 0.1)
        floor_map = {'bj': 0, 'en': 0.5, 'st': 0, 'ss': -1}
        df['floor_clean'] = df['floor'].replace(floor_map)
        df['floor_clean'] = pd.to_numeric(df['floor_clean'], errors='coerce').fillna(1)

        # On utilise infer_objects pour garder un code moderne et propre
        df['hasLift'] = df['hasLift'].infer_objects(copy=False).fillna(False).astype(int)
        df['exterior'] = df['exterior'].infer_objects(copy=False).fillna(True).astype(int)
        df['light_score'] = df['floor_clean'] * df['exterior']

        # --- ÉTAPE 4 : DÉFINITION DES TYPES (CRUCIAL POUR LE NLP) ---
        df['is_penthouse'] = (df['propertyType'] == 'penthouse').astype(int)
        df['is_ground_floor'] = df['floor'].apply(lambda x: 1 if x == 'bj' else 0)
        df['needs_reform'] = (df['status'] == 'renew').astype(int)
        # Extraction sécurisée du parking (format dictionnaire dans l'API)
        df['has_parking'] = df['parkingSpace'].apply(lambda x: 1 if isinstance(x, dict) and x.get('hasParkingSpace') else 0)

        # --- ÉTAPE 5 : ANALYSE DU MARCHÉ (MOMENTUM) ---
        df = self.add_dynamic_trends(df)

        # --- ÉTAPE 6 : NLP (DÉTECTION DANS LA DESCRIPTION) ---
        prohibited_terms = [
            # Occupation illégale / Squat
            'ocupado', 'ocupada', 'okupa', 'okupada', 'sin posesion',
            'sin posesión', 'inmueble ilegal', 'no visitable',
            'no se puede visitar', 'acto de ocupacion',

            # Juridique complexe / Viager
            'nuda propiedad', 'usufructo', 'persona mayor', 'renta vitalicia',
            'subasta', 'judicial', 'embargo', 'cesion de remate', 'proindiviso',

            # Ventes spéciales (Souvent sans garantie ou baux impayés)
            'solo inversores', 'sólo inversores'
        ]

        # Nettoyage de la description pour le filtrage
        # On enlève les accents et on met en minuscule pour ne rien rater
        desc_clean = df['description'].str.lower().str.normalize('NFKD')\
                        .str.encode('ascii', errors='ignore').str.decode('utf-8')

        pattern = '|'.join(prohibited_terms)
        mask_poison = desc_clean.str.contains(pattern, na=False)

        # Log pour le terminal
        nb_eliminated = mask_poison.sum()
        df = df[~mask_poison].copy()

        if nb_eliminated > 0:
            print(f"🛡️ BOUCLIER : {nb_eliminated} annonces toxiques éliminées (Ocupada, Viagers...).")

        desc = df['description'].str.lower()

        # Détection des atouts majeurs qui boostent la valeur
        df['has_terrace'] = desc.str.contains('terraza|atico|ático', na=False).astype(int)
        df['has_balcony'] = desc.str.contains('balcón|balcon', na=False).astype(int)
        # Un dernier étage est soit un penthouse, soit mentionné explicitement
        df['is_last_floor'] = ((df['is_penthouse'] == 1) | desc.str.contains('última planta|ultima planta|sin vecinos arriba', na=False)).astype(int)
        df['is_south_facing'] = desc.str.contains('orientación sur|orientacion sur|soleado', na=False).astype(int)

        # --- ÉTAPE 7 : LOGIQUE FINANCIÈRE (LOYERS, AIRBNB & TRAVAUX) ---
        # On calcule d'abord le potentiel Airbnb puis les maths globales
        df = self.add_airbnb_logic(df)
        df = self.add_investment_math(df)

        # --- ÉTAPE 8 : CLUSTERING ET EXPORT FINAL ---
        df = self.add_geo_clusters(df)

        # Sélection rigoureuse des colonnes pour l'IA et le Dashboard
        final_features = [
            'propertyCode', 'thumbnail', 'price', 'size', 'rooms', 'bathrooms', 'floor_clean',
            'hasLift', 'exterior', 'light_score', 'district', 'neighborhood',
            'latitude', 'longitude', 'momentum_score', 'needs_reform', 'geo_cluster',
            'is_airbnb_ready', 'total_investment', 'est_renovation_cost',
            'est_monthly_rent', 'est_monthly_airbnb_net',
            'net_yield', 'yield_airbnb', 'best_yield',
            'has_terrace', 'has_balcony', 'is_last_floor', 'is_south_facing'
        ]

        # On ajoute dynamiquement les distances (dist_center, dist_beach, etc.)
        final_features += [c for c in df.columns if c.startswith('dist_')]

        # Sécurité : on ne garde que les colonnes qui ont survécu au traitement
        existing_cols = [c for c in final_features if c in df.columns]

        return df[existing_cols]

    def add_geo_clusters(self, df, n_clusters=15):
        coords = df[['latitude', 'longitude']]
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df['geo_cluster'] = kmeans.fit_predict(coords).astype(str)
        return df

    def save_processed(self, df):
        output_path = self.processed_dir / "valence_training_set.csv"
        df.to_csv(output_path, index=False)
        print(f"💾 Dataset prêt : {output_path}")

if __name__ == "__main__":
    processor = DataProcessor()
    raw_data = processor.load_all_json()
    if not raw_data.empty:
        clean_data = processor.clean_for_ml(raw_data)
        processor.save_processed(clean_data)
