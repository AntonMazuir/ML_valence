import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
import os

class ValenceModel:
    def __init__(self, model_path='models/valence_model.cbm'):
        self.model_path = model_path
        self.model = CatBoostRegressor()

        if os.path.exists(self.model_path):
            self.model.load_model(self.model_path)
            print(f"🧠 Modèle chargé avec succès.")
        else:
            print("⚠️ Aucun modèle trouvé, il faut lancer l'entraînement.")

    def predict_one(self, property_dict):
        """Prédit le prix en gérant l'inversion du Log"""
        df_new = pd.DataFrame([property_dict])

        # Le modèle prédit un LOG, on le transforme en EUROS
        prediction_log = self.model.predict(df_new)[0]
        return np.expm1(prediction_log)

if __name__ == "__main__":
    ai = ValenceModel()

    # TEST DU CABANYAL (Version augmentée)
    # Note : on ajoute les colonnes que le modèle a apprises
    test_maison = {
        'size': 140,
        'rooms': 4,
        'bathrooms': 1,
        'floor': 0,
        'hasLift': 0,
        'exterior': 1,
        'district': "Poblats Marítims",  # Nom exact du CSV (attention à l'accent)
        'neighborhood': "El Cabanyal-El Canyamelar",
        'status': "renew",               # On simule l'état à rénover
        'latitude': 39.468,
        'longitude': -0.324,
        'dist_center': 4.2,
        'dist_beach': 0.5
    }

    prix = ai.predict_one(test_maison)

    print("\n--- RÉSULTAT DU TEST ---")
    print(f"📍 Quartier : {test_maison['district']}")
    print(f"🏠 Surface  : {test_maison['size']} m²")
    print(f"🛠️ État     : {test_maison['status']}")
    print(f"💰 Estimation IA : {prix:,.0f} €")
