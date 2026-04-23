import pandas as pd
import numpy as np

try:
    df = pd.read_excel('TCO 2025.xls', engine='calamine', header=None)
    for i, row in df.head(15).iterrows():
        vals = [str(x)[:40] for x in row.tolist() if not pd.isna(x)]
        print(f"Row {i}: {len(vals)} itens -> {vals}")
except Exception as e:
    print(f"Erro: {e}")
