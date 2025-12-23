import streamlit as st
import pandas as pd
import joblib
from pathlib import Path

MODEL_PATH = Path("data/modele_prix_m2.joblib")

@st.cache_resource
def load_price_model():
    if MODEL_PATH.exists():
        return joblib.load(MODEL_PATH)
    return None

def predict_prix_m2(modele, quartier: str, surface: float) -> float | None:
    if modele is None:
        return None

    df_input = pd.DataFrame([{
        "Quartier": quartier,
        "Surface (m²)": surface,
    }])
    try:
        return float(modele.predict(df_input)[0])
    except Exception:
        return None