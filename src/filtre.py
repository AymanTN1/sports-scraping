import pandas as pd
from pathlib import Path

# Définir le chemin du dossier data
DATA_DIR = Path(__file__).parent.parent / "data" / "output"

keyword = "football"

try:
    input_file = DATA_DIR / "articles.csv"
    df = pd.read_csv(input_file)
    if "title" not in df.columns:
        raise ValueError("The CSV file does not contain a 'title' column.")
    filtered = df[df["title"].str.contains(keyword, case=False)]
    
    print(f"🔍 Résultats filtrés pour '{keyword}' : {len(filtered)} articles\n")
    print(filtered.to_string(index=False))
    
    output_file = DATA_DIR / "filtered_data.csv"
    filtered.to_csv(output_file, index=False)
    print(f"\n✅ Données filtrées sauvegardées : {output_file}")
except FileNotFoundError:
    print("Error: 'data.csv' not found. Please ensure the file exists in the current directory.")
except ValueError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")