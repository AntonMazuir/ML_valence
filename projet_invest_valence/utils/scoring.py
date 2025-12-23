import pandas as pd
from .data_loader import PRIX_M2_QUARTIER

def compute_score_row(row: pd.Series) -> int:
    score = 0
    try:
        marge = float(row["Plus-value brute (€)"]) / float(row["Coût total (€)"])
        score += min(marge * 100, 40)
        if row["Quartier"] in PRIX_M2_QUARTIER:
            score += 10
    except Exception:
        pass
    return round(score)

def add_score_column(df: pd.DataFrame) -> pd.DataFrame:
    if "Score" not in df.columns:
        df["Score"] = df.apply(compute_score_row, axis=1)
    return df

def add_marge_and_ecart(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Marge (%)"] = (df["Plus-value brute (€)"] / df["Coût total (€)"]) * 100

    def ecart(row):
        q = row["Quartier"]
        if q not in PRIX_M2_QUARTIER:
            return None
        try:
            prix_m2 = row["Prix d’achat (€)"] / row["Surface (m²)"]
            return round(prix_m2 - PRIX_M2_QUARTIER[q])
        except Exception:
            return None

    df["Écart au marché (€/m²)"] = df.apply(ecart, axis=1)
    return df