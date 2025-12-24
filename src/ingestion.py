import subprocess
import base64
import os
import json
from datetime import datetime
from dotenv import load_dotenv

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

    def search_valence(self):
        """Recherche via curl système pour éviter le blocage 406"""
        print("🔍 Recherche des biens à Valence via System Curl...")

        # On construit la commande exactement comme dans leur doc
        cmd = [
            "curl", "-s", "-X", "POST",
            "-H", f"Authorization: Bearer {self.token}",
            "-H", "Content-Type: multipart/form-data",
            "-F", "operation=sale",
            "-F", "propertyType=homes",
            "-F", "center=39.4697,-0.3773",
            "-F", "distance=5000",
            "-F", "maxItems=50",
            f"{self.base_url}/search"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        try:
            data = json.loads(result.stdout)

            # Sauvegarde du fichier
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"data/raw/valence_{timestamp}.json"

            # S'assurer que le dossier existe
            os.makedirs("data/raw", exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            num_items = len(data.get('elementList', []))
            print(f"✅ Succès ! {num_items} biens trouvés.")
            print(f"💾 Données sauvegardées dans : {path}")
            return data

        except Exception as e:
            print(f"❌ Échec de la lecture du JSON : {e}")
            print(f"Sortie brute : {result.stdout[:200]}...")
            return None

if __name__ == "__main__":
    client = IdealistaClient()
    if client.token:
        client.search_valence()
