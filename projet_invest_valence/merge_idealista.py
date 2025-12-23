import pandas as pd
from pathlib import Path

MASTER_PATH = Path("data/idealista_master.csv")
NEW_PATH = Path("data/idealista_valencia.csv")  # le dernier scraping
OUT_PATH = MASTER_PATH  # on écrase le master avec la version à jour

def main():
    if MASTER_PATH.exists():
        df_master = pd.read_csv(MASTER_PATH)
        print("Master existant :", df_master.shape)
    else:
        df_master = pd.DataFrame()
        print("Aucun master existant, on va en créer un.")

    df_new = pd.read_csv(NEW_PATH)
    print("Nouvelles données :", df_new.shape)

    # Concat master + nouveau scraping
    df_all = pd.concat([df_master, df_new], ignore_index=True)

    # Dédoublonnage sur le lien de l'annonce
    if "Lien annonce" in df_all.columns:
        df_all = df_all.drop_duplicates(subset=["Lien annonce"], keep="last")
    else:
        print("⚠️ Colonne 'Lien annonce' absente, dédoublonnage impossible sur cette clé.")

    print("Dataset après dédoublonnage :", df_all.shape)

    df_all.to_csv(OUT_PATH, index=False)
    print(f"✅ Master mis à jour dans {OUT_PATH}")

if __name__ == "__main__":
    main()
