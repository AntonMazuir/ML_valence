import sys
import os
from pathlib import Path

# On s'assure que le dossier racine est dans le path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ingestion import IdealistaClient
from processing import DataProcessor
from model import ValenceModel
from scan import detect_opportunities, print_report
from dashboard import generate_html_dashboard

def run_pipeline():
    print("🚀 DÉMARRAGE DU PIPELINE INVEST VALENCE\n")

    # Création des dossiers nécessaires s'ils manquent
    for folder in ['data/raw', 'data/processed', 'models']:
        os.makedirs(folder, exist_ok=True)

    # 1. INGESTION
    print("--- 📡 ÉTAPE 1 : RÉCUPÉRATION DES DONNÉES ---")
    # Le client récupère auto ses clés dans le .env
    #client = IdealistaClient()
    #if client.token:
    #    client.search_multi_zones_paginated()
    #print("✅ Ingestion terminée.\n")
    print("✅ Ingestion sautée.\n")

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
    # On s'assure que le scanner pointe vers le dernier dataset traité
    opportunities = detect_opportunities(data_path='data/processed/valence_training_set.csv')

    if not opportunities.empty:
        print_report(opportunities)

        # Sauvegarde datée
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_file = f'data/opps_valence_{timestamp}.csv'
        opportunities.to_csv(output_file, index=False)
        print(f"✅ Liste sauvegardée : {output_file}")

        # 5. GÉNÉRATION DU DASHBOARD HTML
        print("\n--- 📊 ÉTAPE 5 : GÉNÉRATION DU DASHBOARD HTML ---")
        generate_html_dashboard(opportunities)
        print("✅ Dashboard HTML généré avec succès.\n")

    else:
        print("ℹ️ Aucune opportunité ne correspond aux critères de marge (>15%).")

    print("🏁 PIPELINE TERMINÉ AVEC SUCCÈS !")

if __name__ == "__main__":
    run_pipeline()
