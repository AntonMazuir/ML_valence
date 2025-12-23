import requests
import base64
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class IdealistaClient:
    def __init__(self):
        self.api_key = os.getenv("IDEALISTA_API_KEY")
        self.api_secret = os.getenv("IDEALISTA_API_SECRET")
        self.base_url = "https://api.idealista.com/3.5/es"
        self.token = self._get_token()

    def _get_token(self):
        """Récupère le jeton d'accès OAuth2"""
        validation_64 = base64.b64encode(
            f"{self.api_key}:{self.api_secret}".encode("utf-8")
        ).decode("utf-8")

        headers = {
            "Authorization": f"Basic {validation_64}",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        }

        response = requests.post(
            "https://api.idealista.com/oauth/token",
            headers=headers,
            data={"grant_type": "client_credentials"}
        )
        return response.json().get("access_token")

    def search_valence(self, location_id="0-EU-ES-46-01-001-019"):
        """Effectue une recherche sur une zone précise de Valence"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        params = {
            "operation": "sale",
            "propertyType": "homes",
            "center": "39.4697,-0.3773", # Centre de Valence
            "distance": "5000",          # Rayon de 5km
            "maxItems": "50"
        }

        response = requests.post(
            f"{self.base_url}/search",
            headers=headers,
            params=params
        )
        return response.json()

if __name__ == "__main__":
    client = IdealistaClient()
    data = client.search_valence()
    print(data)
