import os
import pandas as pd
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "dados", "2026", "MVI 2026.xls")
    df = pd.read_excel(file_path, header=None)
    print("Conteúdo Bruto (Primeiras 15 linhas):")
    for i, row in df.head(15).iterrows():
        print(f"Linha {i}: {row.tolist()[:10]}")
except Exception as e:
    print(f"Erro: {e}")
