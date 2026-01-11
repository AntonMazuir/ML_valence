import pandas as pd
import numpy as np
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import train_test_split

def tune_valence_model(csv_path='data/processed/valence_training_set.csv'):
    df = pd.read_csv(csv_path)

    # On reste sur nos 29 variables robustes (sans triche)
    features = [
        'size', 'rooms', 'bathrooms', 'floor_clean', 'hasLift', 'exterior',
        'district', 'neighborhood', 'latitude', 'longitude',
        'bath_ratio', 'light_score', 'geo_cluster',
        'dist_center', 'dist_beach', 'dist_turia', 'dist_arts_sciences',
        'dist_upv', 'dist_metro_xativa', 'dist_metro',
        'is_house', 'needs_reform', 'is_ground_floor',
        'has_parking', 'is_penthouse', 'has_terrace', 'has_balcony',
        'is_last_floor', 'is_south_facing'
    ]

    cat_features = ['district', 'neighborhood', 'geo_cluster']
    for col in cat_features:
        df[col] = df[col].fillna("Unknown").astype(str)

    X = df[features]
    y = np.log1p(df['price'])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 1. Définition de la grille de recherche
    model = CatBoostRegressor(
        loss_function='RMSE',
        eval_metric='MAE',
        early_stopping_rounds=100,
        verbose=False
    )

    grid = {
        'learning_rate': [0.01, 0.02, 0.03, 0.05],
        'depth': [4, 6, 8],
        'l2_leaf_reg': [1, 3, 5, 7], # Régularisation pour éviter l'overfitting
        'iterations': [1000, 2000, 3000]
    }

    print("🕵️ Lancement de la Grid Search sur ton dataset Valence...")
    print(f"Nombre de combinaisons à tester : {4 * 3 * 4 * 3}...")
    # 2. Exécution de la recherche
    # CatBoost a une fonction native 'grid_search' très efficace
    grid_search_result = model.grid_search(
        grid,
        X=Pool(X_train, y_train, cat_features=cat_features),
        cv=3, # 3-fold cross validation interne
        partition_random_seed=42,
        plot=False
    )

    print("\n🏆 MEILLEURS PARAMÈTRES TROUVÉS :")
    print(grid_search_result['params'])

    # 3. Test de la meilleure config
    best_params = grid_search_result['params']
    return best_params

if __name__ == "__main__":
    tune_valence_model()
