import pandas as pd
import numpy as np
import os
from pathlib import Path

base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, "dados", "2026", "Maria da Penha 2026.xls")

try:
    # Usando o engine calamine que o Dashboard já usa
    df = pd.read_excel(file_path, engine='calamine')
    print("--- Colunas Detectadas ---")
    for i, col in enumerate(df.columns):
        print(f"Col {i}: {col}")
    
    print("\n--- Amostra de Dados (Linhas 0-5) ---")
    print(df.head(5))
    
    # Usuário mencionou coluna AA (índice 26) para cidades
    if len(df.columns) > 26:
        print("\n--- Coluna AA (Cidades?) ---")
        print(df.iloc[0:10, 26])
    
    # Geralmente a data está na primeira coluna ou em "Data do Fato"
    # Vou procurar por colunas que pareçam ter datas.
except Exception as e:
    print(f"Erro ao processar: {e}")
    import traceback
    traceback.print_exc()
