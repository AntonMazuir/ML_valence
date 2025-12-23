import pandas as pd
import streamlit as st

PRIX_M2_QUARTIER = {
    "La Seu": 2739,
    "Sant Francesc": 4072,
    "El Carme": 3046,
    "El Mercat": 2701,
    "La Xerea": 4148,
    "El Pla del Remei": 4863,
    "Patraix": 2587,
}

@st.cache_data
def load_data(path: str = "data\dataset_valence_synthetique_1000.csv") -> pd.DataFrame:
    df = pd.read_csv(path, sep=",")
    return df.copy()