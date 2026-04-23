import pandas as pd

df = pd.read_excel('Armas 2025.xls', header=None)
print("--- PRIMEIRAS 30 LINHAS ---")
for i, row in df.head(30).iterrows():
    vals = [str(x)[:20] if not pd.isna(x) else "" for x in row.tolist()]
    if any(vals):
        print(f"Row {i}: {vals}")
