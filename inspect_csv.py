import pandas as pd

files = [
    'data/raw/resultats_Pi5_2026-06-19_05h16.csv',
    'data/raw/resultats_Pi5_2026-06-24_16h01.csv',
    'data/raw/prompt_size_Pi5_2026-06-17_11h22.csv',
]
for f in files:
    df = pd.read_csv(f)
    print(f"=== {f} ===")
    print(f"  shape: {df.shape}")
    print(f"  cols: {list(df.columns)}")
    if 'modele' in df.columns:       print(f"  modele: {df['modele'].unique()}")
    if 'quantification' in df.columns: print(f"  quantif: {df['quantification'].unique()}")
    if 'max_tokens' in df.columns:   print(f"  max_tokens: {sorted(df['max_tokens'].unique())}")
    if 'n_caracteres' in df.columns: print(f"  n_car: {df['n_caracteres'].min()} - {df['n_caracteres'].max()}")
    print()
