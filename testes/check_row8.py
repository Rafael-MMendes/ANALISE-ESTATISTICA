import os
import pandas as pd
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "dados", "2026", "MVI 2026.xls")
    df = pd.read_excel(file_path, header=None)
    row_8 = df.iloc[8].tolist()
    print("Linha 8 completa:")
    print(row_8)
except Exception as e:
    print(f"Erro: {e}")
