import pandas as pd
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, "dados", "2026", "Prisões 2026.xls")
try:
    df = pd.read_excel(file_path, header=None)
    print("Sucesso na leitura!")
    print(f"Colunas: {len(df.columns)}")
    print(f"Linhas: {len(df)}")
    print(df.head())
except Exception as e:
    print(f"Erro na leitura: {e}")
