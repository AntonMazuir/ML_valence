import pandas as pd
import numpy as np

def clean_data(df):
    """Nettoyage et Feature Engineering de base"""
    # 1. Sélection des colonnes essentielles
    cols_to_keep = [
        'propertyCode', 'price', 'size', 'rooms', 'bathrooms',
        'floor', 'exterior', 'hasLift', 'district', 'neighborhood',
        'latitude', 'longitude', 'status', 'propertyType'
    ]
    df_clean = df[cols_to_keep].copy()

    # 2. Gestion des types et valeurs manquantes
    # Conversion de l'étage en numérique (certains sont peut-être 'en' ou 'bj')
    df_clean['floor'] = pd.to_numeric(df['floor'], errors='coerce').fillna(0)

    # Remplissage des booléens
    df_clean['hasLift'] = df_clean['hasLift'].fillna(False)
    df_clean['exterior'] = df_clean['exterior'].fillna(True) # Majorité à Valence

    # 3. Feature Engineering (Le coeur du métier)
    df_clean['price_per_m2'] = df_clean['price'] / df_clean['size']

    # 4. Suppression des valeurs aberrantes (Outliers)
    # Ex: On ne veut pas de parkings ou de biens à 0€
    df_clean = df_clean[df_clean['price'] > 20000]
    df_clean = df_clean[df_clean['size'] > 10]

    return df_clean

if __name__ == "__main__":
    # Test rapide sur le dernier fichier chargé
    # (Tu pourras l'importer dans ton notebook plus tard)
    pass
