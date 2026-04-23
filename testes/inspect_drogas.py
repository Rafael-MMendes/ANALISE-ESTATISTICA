import pandas as pd

file_name = 'Drogas 2025.xls'

print("--- CALAMINE ---")
try:
    df = pd.read_excel(file_name, engine='calamine')
    print("Shape:", df.shape)
    for i, col in enumerate(df.columns):
        print(f"Col {i}: {col}")
    print("\n--- Primeiras linhas ---")
    for i, row in df.head(20).iterrows():
        vals = [str(x)[:30] if not pd.isna(x) else "" for x in row.tolist()]
        if any(vals):
            print(f"Row {i}: {vals}")
except Exception as e:
    print(f"Erro calamine: {e}")

print("\n--- NORMAL ---")
try:
    df = pd.read_excel(file_name)
    print("Shape:", df.shape)
except Exception as e:
    print(f"Erro normal: {e}")
