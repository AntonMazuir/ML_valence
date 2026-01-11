import pandas as pd
import os
from datetime import datetime
import numpy as np

def generate_html_dashboard(df, output_path="dashboard.html"):
    if df.empty:
        print("⚠️ Aucune donnée à afficher.")
        return

    # On trie par l'Investment Score
    df = df.sort_values(by='investment_score', ascending=False).head(30)
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="referrer" content="no-referrer">
        <title>Invest Valence V5 - Terminal Pro</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{ background-color: #f4f7f6; font-family: 'Inter', sans-serif; }}
            .header-zone {{ background: #1a1a1a; color: white; padding: 40px 0; margin-bottom: 40px; }}
            .card {{ border: none; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.05); transition: 0.3s; height: 100%; }}
            .card:hover {{ transform: translateY(-10px); box-shadow: 0 15px 45px rgba(0,0,0,0.1); }}
            .img-container {{ height: 220px; position: relative; background: #222; }}
            .img-container img {{ width: 100%; height: 100%; object-fit: cover; opacity: 0.9; }}
            .score-badge {{ position: absolute; top: 15px; left: 15px; background: #ff4757; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; z-index: 10; }}
            .momentum-badge {{ position: absolute; top: 15px; right: 15px; background: rgba(255,255,255,0.9); color: #2f3542; padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 0.8rem; z-index: 10; }}
            .price-main {{ font-size: 1.6rem; font-weight: 800; color: #2d3436; }}
            .est-price {{ font-size: 0.9rem; color: #a4b0be; text-decoration: line-through; }}
            .invest-bar {{ height: 6px; background: #eee; border-radius: 3px; margin: 15px 0; }}
            .invest-progress {{ height: 100%; background: linear-gradient(90deg, #ff4757, #2ed573); border-radius: 3px; }}
        </style>
    </head>
    <body>
        <div class="header-zone text-center">
            <div class="container">
                <h1 class="display-4 fw-bold">🎯 Valence Real Estate V5</h1>
                <p class="lead opacity-75">Intelligence Artificielle & Momentum de Gentrification</p>
                <span class="badge bg-primary">Scan du {timestamp}</span>
            </div>
        </div>

        <div class="container">
            <div class="row g-4">
    """

    for _, row in df.iterrows():
        # --- LOGIQUE IMAGE (PROXY GOOGLE) ---
        raw_img = row.get('thumbnail', '')
        url = f"https://www.idealista.com/inmueble/{int(row['propertyCode'])}/"

        if raw_img and 'idealista.com' in raw_img:
            # Proxy Google Focus (le plus robuste contre le blocage Idealista)
            img = f"https://images1-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&refresh=2592000&url={raw_img}"
        else:
            img = 'https://via.placeholder.com/400x250?text=Image+Non+Disponible'

        # --- GESTION DU MOMENTUM (Affichage propre) ---
        mom = row.get('momentum_score', 0)
        mom_display = f"{mom:.2f}" if np.isfinite(mom) else "New Hotspot"

        # Icônes de confort
        comfort_icons = ""
        if row.get('has_terrace'): comfort_icons += ' <i class="fa-solid fa-tree text-success" title="Terrasse"></i>'
        if row.get('is_south_facing'): comfort_icons += ' <i class="fa-solid fa-sun text-warning" title="Sud"></i>'
        if row.get('is_last_floor'): comfort_icons += ' <i class="fa-solid fa-arrow-up-z text-primary" title="Dernier étage"></i>'
        if row.get('has_parking'): comfort_icons += ' <i class="fa-solid fa-car text-secondary" title="Parking"></i>'

        score = int(row.get('investment_score', 0))

        html_content += f"""
                <div class="col-md-4">
                    <div class="card">
                        <div class="img-container">
                            <div class="score-badge">Score: {score}/100</div>
                            <div class="momentum-badge">⚡ {mom_display}</div>
                            <img src="{img}" alt="Annonce" loading="lazy">
                        </div>
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <span class="price-main">{int(row['price']):,} €</span>
                                <span class="est-price">{int(row['estimated_price']):,} €</span>
                            </div>
                            <h6 class="text-primary mb-3">
                                <i class="fa-solid fa-location-dot"></i> {row['neighborhood']} {comfort_icons}
                            </h6>

                            <div class="row text-muted mb-2" style="font-size: 0.85rem;">
                                <div class="col-6"><i class="fa-solid fa-ruler-combined"></i> {int(row['size'])} m²</div>
                                <div class="col-6"><i class="fa-solid fa-door-open"></i> {int(row['rooms'])} ch.</div>
                            </div>

                            <div class="invest-bar">
                                <div class="invest-progress" style="width: {score}%"></div>
                            </div>

                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <span class="badge bg-success-subtle text-success">Marge: +{int(row['discount_pct'])}%</span>
                                <span class="fw-bold text-dark">+{int(row['profit_potential']):,} €</span>
                            </div>

                            <a href="{url}" target="_blank" class="btn btn-dark w-100 py-2 fw-bold">VOIR L'OPPORTUNITÉ</a>
                        </div>
                    </div>
                </div>
        """

    html_content += """
            </div>
            <div class="text-center py-5">
                <p class="text-muted">Généré par ton IA Valence V5 - Intelligence Immobilière Industrielle</p>
            </div>
        </div>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"🖥️ Dashboard V5 généré avec Proxy Google : {os.path.abspath(output_path)}")
