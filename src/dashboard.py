import pandas as pd
import os
from datetime import datetime
import numpy as np

def generate_html_dashboard(df, output_path="dashboard.html"):
    if df.empty:
        print("⚠️ Aucune donnée à afficher.")
        return

    # --- ÉTAPE 1 : TRI ET PRÉPARATION ---
    # On affiche les 30 meilleures opportunités selon l'Investment Score
    df = df.sort_values(by='investment_score', ascending=False).head(30)
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")

    # --- ÉTAPE 2 : STRUCTURE HTML & STYLES ---
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="referrer" content="no-referrer">
        <title>Invest Valence V5 - Business Intelligence</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{ background-color: #f4f7f6; font-family: 'Inter', sans-serif; }}
            .header-zone {{ background: #1a1a1a; color: white; padding: 40px 0; margin-bottom: 40px; }}
            .card {{ border: none; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.05); transition: 0.3s; height: 100%; }}
            .card:hover {{ transform: translateY(-10px); box-shadow: 0 15px 45px rgba(0,0,0,0.1); }}
            .img-container {{ height: 220px; position: relative; background: #222; }}
            .img-container img {{ width: 100%; height: 100%; object-fit: cover; opacity: 0.9; }}

            /* Badges Spéciaux */
            .score-badge {{ position: absolute; top: 15px; left: 15px; background: #ff4757; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; z-index: 10; }}
            .airbnb-badge {{ position: absolute; bottom: 15px; right: 15px; background: #FF385C; color: white; padding: 5px 12px; border-radius: 8px; font-weight: bold; font-size: 0.8rem; z-index: 10; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }}

            .price-main {{ font-size: 1.5rem; font-weight: 800; color: #2d3436; }}
            .yield-badge {{ background: #2ed573; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; }}
            .reno-text {{ color: #eb4d4b; font-weight: 700; font-size: 0.9rem; }}
        </style>
    </head>
    <body>
        <div class="header-zone text-center">
            <div class="container">
                <h1 class="display-4 fw-bold">🎯 Invest Valence V5</h1>
                <p class="lead opacity-75">IA Prédictive & Analyse de Rentabilité Réelle</p>
                <span class="badge bg-primary">Généré le {timestamp}</span>
            </div>
        </div>
        <div class="container"><div class="row g-4">
    """

    # --- ÉTAPE 3 : GÉNÉRATION DES CARTES BIENS ---
    for _, row in df.iterrows():
        # Gestion des photos via Proxy Google pour éviter le blocage Idealista
        raw_img = row.get('thumbnail', '')
        img_url = f"https://images1-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&refresh=2592000&url={raw_img}" if raw_img else "https://via.placeholder.com/400x250?text=Image+Indisponible"

        # Lien direct vers l'annonce
        prop_url = f"https://www.idealista.com/inmueble/{int(row['propertyCode'])}/"

        # Calculs financiers pour l'affichage
        total_invest = int(row.get('total_investment', 0))
        reno_cost = int(row.get('est_renovation_cost', 0))
        yield_val = row.get('best_yield', 0)
        is_airbnb = row.get('is_airbnb_ready', 0)

        # Badge Airbnb si licence détectée par le NLP
        airbnb_html = '<div class="airbnb-badge"><i class="fa-brands fa-airbnb"></i> LICENCE OK</div>' if is_airbnb == 1 else ""

        # Icônes de confort (Terrasse, Sud, etc.)
        icons = ""
        if row.get('has_terrace'): icons += ' <i class="fa-solid fa-tree text-success" title="Terrasse"></i>'
        if row.get('is_last_floor'): icons += ' <i class="fa-solid fa-arrow-up text-primary" title="Dernier étage"></i>'

        html_content += f"""
            <div class="col-md-4">
                <div class="card">
                    <div class="img-container">
                        <div class="score-badge">{int(row['investment_score'])}/100</div>
                        {airbnb_html}
                        <img src="{img_url}" alt="Propriété">
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="price-main">{int(row['price']):,} €</span>
                            <span class="yield-badge">{yield_val:.2f}% Net</span>
                        </div>

                        <h6 class="text-primary mb-3">
                            <i class="fa-solid fa-location-dot"></i> {row['neighborhood']} {icons}
                        </h6>

                        <div class="p-3 bg-light rounded-3 mb-3" style="font-size: 0.85rem;">
                            <div class="d-flex justify-content-between mb-1">
                                <span>🏗️ Travaux Est. :</span>
                                <span class="reno-text">+{reno_cost:,} €</span>
                            </div>
                            <div class="d-flex justify-content-between fw-bold border-top pt-1">
                                <span>💰 Budget Total :</span>
                                <span>{total_invest:,} €</span>
                            </div>
                        </div>

                        <div class="row text-muted mb-3" style="font-size: 0.85rem;">
                            <div class="col-6"><i class="fa-solid fa-ruler-combined"></i> {int(row['size'])} m²</div>
                            <div class="col-6"><i class="fa-solid fa-door-open"></i> {int(row['rooms'])} ch.</div>
                        </div>

                        <a href="{prop_url}" target="_blank" class="btn btn-dark w-100 py-2 fw-bold">ANALYSER L'AFFAIRE</a>
                    </div>
                </div>
            </div>
        """

    # --- ÉTAPE 4 : FINALISATION DU FICHIER ---
    html_content += """
            </div>
            <div class="text-center py-5 opacity-50">
                <p>Propulsé par Valence IA V5 - Stratégie & Rendement</p>
            </div>
        </div>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"🖥️ Dashboard BI généré : {os.path.abspath(output_path)}")
