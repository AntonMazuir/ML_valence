import pandas as pd

REAL_PATH = "data/idealista_clean.csv"
SYNTH_PATH = "data/dataset_valence_synthetique_1000.csv"
OUT = "data/dataset_combine.csv"

def main():
    df_real = pd.read_csv(REAL_PATH)
    df_synth = pd.read_csv(SYNTH_PATH)

    print("Données réelles :", df_real.shape)
    print("Données synthétiques :", df_synth.shape)

    # Colonnes communes
    common_cols = [col for col in df_real.columns if col in df_synth.columns]
    df_real = df_real[common_cols]
    df_synth = df_synth[common_cols]

    df = pd.concat([df_real, df_synth], ignore_index=True)

    print("Dataset final combiné :", df.shape)

    df.to_csv(OUT, index=False)
    print(f"✅ Dataset combiné sauvegardé dans {OUT}")

if __name__ == "__main__":
    main()