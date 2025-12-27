import sys
import os

# On s'assure que le dossier src est bien reconnu
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ingestion import IdealistaIngestion
from processing import process_data
from model import ValenceModel

def run_pipeline():
    print("🚀 DÉMARRAGE DU PIPELINE INVEST VALENCE\n")

    # 1. INGESTION
    print("--- 📡 ÉTAPE 1 : RÉCUPÉRATION DES DONNÉES ---")
    # Remplace par tes vrais identifiants ou utilise des variables d'env
    api_key = "TON_API_KEY"
    secret = "TON_SECRET"

    ingestor = IdealistaIngestion(api_key, secret)
    ingestor.search_multi_zones_paginated() # Ta version avec boucles
    print("✅ Ingestion terminée.\n")

    # 2. PROCESSING
    print("--- 🧹 ÉTAPE 2 : NETTOYAGE ET PRÉPARATION ---")
    process_data() # Ton script qui génère le CSV final
    print("✅ Données traitées et dédupliquées.\n")

    # 3. TRAINING
    print("--- 🧠 ÉTAPE 3 : ENTRAÎNEMENT DE L'IA ---")
    ai = ValenceModel()
    ai.train() # Il va lire data/processed/valence_training_set.csv
    print("✅ Modèle mis à jour et sauvegardé.\n")

    print("🏁 PIPELINE TERMINÉ AVEC SUCCÈS !")

if __name__ == "__main__":
    run_pipeline()
