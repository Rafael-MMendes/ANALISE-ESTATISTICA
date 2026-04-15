import os
import pandas as pd
import numpy as np
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "dados", "2026", "MVI 2026.xls")
    df = pd.read_excel(file_path, header=9)
    print("Colunas encontradas:")
    print(df.columns.tolist())
    print("\nPrimeiras 5 linhas das colunas Data e Cidade:")
    cols = [c for c in df.columns if 'Data' in str(c) or 'Cidade' in str(c)]
    print(df[cols].head())
except Exception as e:
    print(f"Erro: {e}")
