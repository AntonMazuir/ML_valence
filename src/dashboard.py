import pandas as pd
import os
from datetime import datetime

def generate_html_dashboard(df, output_path="dashboard.html"):
    # On trie pour avoir les meilleures marges en haut
    df = df.sort_values(by='discount_pct', ascending=False).head(20)

    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Invest Valence - Top Opportunités</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <style>
            body {{ background-color: #f8f9fa; padding: 20px; }}
            .card {{ transition: transform 0.2s; margin-bottom: 20px; border: none; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .card:hover {{ transform: scale(1.02); }}
            .badge-profit {{ position: absolute; top: 10px; right: 10px; font-size: 1.2rem; padding: 10px; }}
            .img-container {{ height: 200px; overflow: hidden; background-color: #ddd; }}
            .img-container img {{ width: 100%; height: 100%; object-fit: cover; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="mb-4">🎯 Top 20 Opportunités Valence <small class="text-muted" style="font-size: 1rem;">Mise à jour : {timestamp}</small></h1>
            <div class="row">
    """

    for _, row in df.iterrows():
        # Reconstitution de l'URL photo (si dispo dans ton JSON original, sinon image par défaut)
        # Note : Si tu n'as pas gardé 'thumbnail' dans ton CSV, utilise une image placeholder
        img_url = row.get('thumbnail', 'https://via.placeholder.com/300x200?text=Appartement')
        url = f"https://www.idealista.com/inmueble/{int(row['propertyCode'])}/"

        # Couleur du badge selon la marge
        color = "bg-success" if row['discount_pct'] > 25 else "bg-warning text-dark"

        html_content += f"""
                <div class="col-md-4">
                    <div class="card">
                        <span class="badge {color} badge-profit">+{int(row['discount_pct'])}%</span>
                        <div class="img-container">
                            <img src="{img_url}" alt="Appartement">
                        </div>
                        <div class="card-body">
                            <h5 class="card-title">{int(row['price']):,} € <small class="text-muted">vs {int(row['estimated_price']):,} €</small></h5>
                            <p class="card-text">
                                📍 <strong>{row['neighborhood']}</strong><br>
                                📏 {int(row['size'])} m² | {int(row['rooms'])} ch. | Ét. {row['floor']}<br>
                                🚀 Gain est. : <strong>{int(row['profit_potential']):,} €</strong>
                            </p>
                            <a href="{url}" target="_blank" class="btn btn-primary w-100">Voir l'annonce</a>
                        </div>
                    </div>
                </div>
        """

    html_content += """
            </div>
        </div>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"🖥️ Dashboard généré : {output_path}")
