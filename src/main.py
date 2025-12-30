import sys
import os
from pathlib import Path

# On s'assure que le dossier racine est dans le path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ingestion import IdealistaClient
from processing import DataProcessor
from model import ValenceModel
from scan import detect_opportunities, print_report

def run_pipeline():
    print("🚀 DÉMARRAGE DU PIPELINE INVEST VALENCE\n")

    # Création des dossiers nécessaires s'ils manquent
    for folder in ['data/raw', 'data/processed', 'models']:
        os.makedirs(folder, exist_ok=True)

    # 1. INGESTION
    print("--- 📡 ÉTAPE 1 : RÉCUPÉRATION DES DONNÉES ---")
    # Le client récupère auto ses clés dans le .env
    client = IdealistaClient()
    if client.token:
        client.search_multi_zones_paginated()
    print("✅ Ingestion terminée.\n")

    # 2. PROCESSING
    print("--- 🧹 ÉTAPE 2 : NETTOYAGE ET PRÉPARATION ---")
    processor = DataProcessor()
    raw_df = processor.load_all_json()
    if not raw_df.empty:
        clean_df = processor.clean_for_ml(raw_df)
        processor.save_processed(clean_df)
    print("✅ Données traitées et dédupliquées.\n")

    # 3. TRAINING
    print("--- 🧠 ÉTAPE 3 : ENTRAÎNEMENT DE L'IA ---")
    ai = ValenceModel()
    ai.train()
    print("✅ Modèle mis à jour et sauvegardé.\n")

    # 4. SCANNER LE MARCHÉ
    print("--- 🎯 ÉTAPE 4 : DÉTECTION DES OPPORTUNITÉS ---")
    opportunities = detect_opportunities()

    if not opportunities.empty:
        print_report(opportunities)

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    opportunities.to_csv(f'data/opps_valence_{timestamp}.csv', index=False)

    print("🏁 PIPELINE TERMINÉ AVEC SUCCÈS !")

if __name__ == "__main__":
    run_pipeline()
