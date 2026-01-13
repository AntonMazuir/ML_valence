import sys
import os
from pathlib import Path
from datetime import datetime

# On s'assure que le dossier racine est dans le path pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ingestion import IdealistaClient
from processing import DataProcessor
from model import ValenceModel
from scan import detect_opportunities, print_report
from dashboard import generate_html_dashboard

def run_pipeline():
    print("🚀 DÉMARRAGE DU PIPELINE INVEST VALENCE V5 - ROBUSTE\n")

    # --- ÉTAPE 0 : PRÉPARATION ---
    # Création des dossiers nécessaires s'ils manquent pour éviter les erreurs d'écriture
    for folder in ['data/raw', 'data/processed', 'models']:
        os.makedirs(folder, exist_ok=True)

    # --- ÉTAPE 1 : INGESTION (Optionnelle) ---
    print("--- 📡 ÉTAPE 1 : RÉCUPÉRATION DES DONNÉES ---")
    # Note : Ingestion sautée pour préserver les crédits API (on travaille sur l'historique)
    print("✅ Utilisation des données JSON existantes dans data/raw/.\n")

    # --- ÉTAPE 2 : DATA PROCESSING (L'intelligence de ton père & NLP) ---
    print("--- 🧹 ÉTAPE 2 : NETTOYAGE, TRAVAUX ET RENDEMENTS ---")
    processor = DataProcessor()
    raw_df = processor.load_all_json()

    if not raw_df.empty:
        # Cette étape calcule : Travaux (1500€/m2), Frais, Loyers, Airbnb et Clusters
        clean_df = processor.clean_for_ml(raw_df)
        processor.save_processed(clean_df)
        print(f"✅ {len(clean_df)} annonces filtrées et enrichies financièrement.\n")
    else:
        print("❌ Erreur : Aucun fichier JSON trouvé dans data/raw/.")
        return

    # --- ÉTAPE 3 : TRAINING IA (Estimation de Valeur de Marché) ---
    print("--- 🧠 ÉTAPE 3 : ENTRAÎNEMENT DE L'IA (MODE ROBUSTE) ---")
    ai = ValenceModel()
    # L'IA apprend à estimer le prix SANS regarder les variables financières (Anti-Triche)
    ai.train()
    print("✅ Modèle V5 (Depth 4) mis à jour et sauvegardé.\n")

    # --- ÉTAPE 4 : SCANNER LE MARCHÉ (Détection des pépites) ---
    print("--- 🎯 ÉTAPE 4 : DÉTECTION DES OPPORTUNITÉS ---")
    # On utilise le score composite : Marge + Yield + Momentum + Bonus Confort
    opportunities = detect_opportunities(data_path='data/processed/valence_training_set.csv')

    if not opportunities.empty:
        # Affichage du Top 15 dans le terminal pour un check rapide
        print_report(opportunities)

        # Sauvegarde d'archive CSV avec la date du jour
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_file = f'data/opps_valence_{timestamp}.csv'
        opportunities.to_csv(output_file, index=False)
        print(f"✅ Archive CSV sauvegardée : {output_file}")

        # --- ÉTAPE 5 : GÉNÉRATION DU DASHBOARD VISUEL ---
        print("\n--- 📊 ÉTAPE 5 : GÉNÉRATION DU DASHBOARD HTML ---")
        # Création de la page web interactive avec photos et badges
        generate_html_dashboard(opportunities)
        print("✅ Dashboard HTML mis à jour (dashboard.html). Prêt pour l'analyse !\n")

    else:
        print("ℹ️ Aucune opportunité ne correspond aux critères de sécurité (Marge 10-50%).")

    print("🏁 PIPELINE TERMINÉ AVEC SUCCÈS ! Tu peux ouvrir dashboard.html.")

if __name__ == "__main__":
    run_pipeline()
