import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score


DATA_PATH = "data/idealista_clean.csv"
MODEL_PATH = "data/modele_valence_real_only.joblib"

def derive_quartier_from_title(title):
    if not isinstance(title, str) or "," not in title:
        return None
    parts = [p.strip() for p in title.split(",")]
    if len(parts) >= 2:
        return parts[-2]
    return None

def prepare_df(df):
    quartiers = []
    for _, row in df.iterrows():
        q_val = row.get("Quartier", None)
        if isinstance(q_val, str) and q_val.strip():
            quartiers.append(q_val.strip())
        else:
            quartiers.append(derive_quartier_from_title(row.get("Titre du bien", None)))
    df["quartier_final"] = pd.Series(quartiers).fillna("Unknown")

    df["Surface (m²)"] = pd.to_numeric(df["Surface (m²)"], errors="coerce")
    df = df.dropna(subset=["Surface (m²)", "Prix/m2"])
    return df

def main():
    df = pd.read_csv(DATA_PATH)
    df = prepare_df(df)

    features = ["quartier_final", "Surface (m²)"]
    target = "Prix/m2"

    X = df[features]
    y = df[target]

    cat_features = ["quartier_final"]
    num_features = ["Surface (m²)"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_features),
            ("num", SimpleImputer(strategy="median"), num_features),
        ]
    )

    model = RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
        max_depth=18,
        min_samples_leaf=2,
    )

    pipe = Pipeline(steps=[
        ("preprocess", preprocessor),
        ("model", model),
    ])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print("=== PERFORMANCE SUR RÉEL (train/test sur idealista_clean) ===")
    print(f"MAE : {mae:.0f} €/m²")
    print(f"R²  : {r2:.3f}")

    joblib.dump(pipe, MODEL_PATH)
    print(f"✅ Modèle sauvegardé dans {MODEL_PATH}")

if __name__ == "__main__":
    main()
