import subprocess
import base64
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import time

load_dotenv()

class IdealistaClient:
    def __init__(self):
        self.api_key = os.getenv("IDEALISTA_API_KEY").strip()
        self.api_secret = os.getenv("IDEALISTA_API_SECRET").strip()
        self.base_url = "https://api.idealista.com/3.5/es"
        self.token = self._get_token()

    def _get_token(self):
        """Récupère le token via le curl système"""
        auth_pair = f"{self.api_key}:{self.api_secret}"
        auth_64 = base64.b64encode(auth_pair.encode('utf-8')).decode('utf-8')

        cmd = [
            "curl", "-s", "-X", "POST", "https://api.idealista.com/oauth/token",
            "-H", f"Authorization: Basic {auth_64}",
            "-H", "Content-Type: application/x-www-form-urlencoded",
            "-d", "grant_type=client_credentials"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            return json.loads(result.stdout).get("access_token")
        except:
            print(f"Erreur Auth: {result.stdout}")
            return None

    def search_multi_zones_paginated(self):
        """Balaye plusieurs zones sur plusieurs pages pour maximiser le dataset"""
        zones = [
            {"name": "Centro", "lat": "39.4739", "lon": "-0.3761"},
            {"name": "Cabanyal_Playa", "lat": "39.4686", "lon": "-0.3243"},
            {"name": "Benimaclet_Nord", "lat": "39.4822", "lon": "-0.3621"},
            {"name": "Quatre_Carreres_Sud", "lat": "39.4522", "lon": "-0.3636"},
            {"name": "Patraix_Ouest", "lat": "39.4622", "lon": "-0.3956"}
        ]

        # On définit le nombre de pages à scanner par zone
        nb_pages = 3

        for zone in zones:
            for page in range(1, nb_pages + 1):
                print(f"📡 Scan {zone['name']} | Page {page}/{nb_pages}...")

                cmd = [
                    "curl", "-s", "-X", "POST",
                    "-H", f"Authorization: Bearer {self.token}",
                    "-H", "Content-Type: multipart/form-data",
                    "-F", "operation=sale",
                    "-F", "propertyType=homes",
                    "-F", f"center={zone['lat']},{zone['lon']}",
                    "-F", "distance=2000",
                    "-F", f"numPage={page}", # Paramètre de pagination
                    "-F", "maxItems=50",
                    f"{self.base_url}/search"
                ]

                time.sleep(1.5)  # Pour éviter de spammer l'API trop vite

                result = subprocess.run(cmd, capture_output=True, text=True)

                try:
                    data = json.loads(result.stdout)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    # On inclut le numéro de page dans le nom du fichier
                    path = f"data/raw/valence_{zone['name']}_p{page}_{timestamp}.json"

                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)

                    found = len(data.get('elementList', []))
                    print(f"✅ {found} biens récupérés.")

                    # Si la page est vide ou contient moins de 50 biens,
                    # on peut arrêter de boucler sur cette zone
                    if found < 50:
                        break

                except Exception as e:
                    print(f"⚠️ Erreur page {page} zone {zone['name']}: {e}")

if __name__ == "__main__":
    client = IdealistaClient()
    if client.token:
        client.search_multi_zones_paginated()
