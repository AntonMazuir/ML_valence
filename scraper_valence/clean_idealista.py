import pandas as pd
import numpy as np

INPUT_PATH = "data/idealista_master.csv"
OUTPUT_PATH = "data/idealista_clean.csv"

def extract_travaux(desc, surface):
    """
    Déduit les travaux estimés (€) en fonction de la description.
    Compatible anglais + espagnol.
    """
    if isinstance(desc, str):
        text = desc.lower()

        # Cas 1 : Travaux lourds (réforme intégrale)
        if any(x in text for x in [
            "to renovate", "needs renovation", "renovation needed", 
            "to reform", "to refurbish", "needs refurbishing",
            "reformar", "reforma", "reforma integral", "renovar"
        ]):
            return int(surface * np.random.randint(600, 1200))

        # Cas 2 : Travaux légers / récemment rénové
        if any(x in text for x in [
            "refurbished", "renovated", "fully renovated", 
            "recently renovated", "new", "like new",
            "reformado", "nuevo", "rehabilitado"
        ]):
            return int(surface * np.random.randint(50, 200))

    # Cas 3 : Description neutre → travaux intermédiaires
    return int(surface * np.random.randint(200, 600))

def main():
    df = pd.read_csv(INPUT_PATH)

    # --- Nettoyage de base ---
    df["Prix d’achat (€)"] = pd.to_numeric(df["Prix d’achat (€)"], errors="coerce")
    df["Surface (m²)"] = pd.to_numeric(df["Surface (m²)"], errors="coerce")
    df = df.dropna(subset=["Prix d’achat (€)", "Surface (m²)"]).copy()

    # Prix au m²
    df["Prix/m2"] = df["Prix d’achat (€)"] / df["Surface (m²)"]

    # Travaux estimés via description
    df["Travaux estimés (€)"] = df.apply(
        lambda row: extract_travaux(row.get("Description", ""), row["Surface (m²)"]),
        axis=1
    )

    n = len(df)

    # Coût total = achat + travaux + frais (3k à 12k)
    frais_fixes = np.random.randint(3000, 12000, size=n)
    df["Coût total (€)"] = df["Prix d’achat (€)"] + df["Travaux estimés (€)"] + frais_fixes

    # Valeur après travaux = coût total * (1 + marge aléatoire 5–20%)
    marge_pct = np.random.uniform(0.05, 0.20, size=n)
    df["Valeur estimée après travaux (€)"] = (df["Coût total (€)"] * (1 + marge_pct)).astype(int)

    # Prix m² à la revente
    df["prix m2 à la revente"] = (df["Valeur estimée après travaux (€)"] / df["Surface (m²)"]).astype(int)

    # Plus-value brute
    df["Plus-value brute (€)"] = df["Valeur estimée après travaux (€)"] - df["Coût total (€)"]

    # Loyer estimé 8–15 €/m²
    loyer_par_m2 = np.random.uniform(8, 15, size=n)
    df["Loyer espéré mensuel (€)"] = (df["Surface (m²)"] * loyer_par_m2).astype(int)

    # Rendement brut
    df["Rendement brut (%)"] = (df["Loyer espéré mensuel (€)"] * 12 / df["Coût total (€)"]) * 100

    # Taux d’occupation 80–95%
    df["Taux d’occupation estimé (%)"] = np.random.randint(80, 96, size=n)

    # Stratégie aléatoire mais typique
    strategies = ["Flip (revente rapide)", "Location long terme", "Colocation", "Airbnb", "Patrimonial"]
    df["Stratégie cible"] = np.random.choice(strategies, size=n)

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Dataset nettoyé & enrichi sauvegardé dans {OUTPUT_PATH}")
    print("Nombre de lignes :", len(df))

if __name__ == "__main__":
    main()