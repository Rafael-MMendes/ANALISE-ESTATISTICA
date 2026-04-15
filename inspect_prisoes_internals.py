import pandas as pd

df = pd.read_excel('Prisões 2025.xlsx', header=None)
print("--- PRIMEIRAS 40 LINHAS REAIS ---")
for i, row in df.head(40).iterrows():
    vals = [str(x)[:20] if not pd.isna(x) else "" for x in row.tolist()]
    if any(vals):
        print(f"Row {i}: {vals}")
