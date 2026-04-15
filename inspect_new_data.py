import pandas as pd
import json

files = ['Tentativa de MVI 2025.xls', 'CVP Geral 2025.xls']

for f in files:
    print(f"\n--- ANALISANDO {f} ---")
    try:
        df = pd.read_excel(f, header=8)
        print("Colunas (após header=8):")
        print(df.columns.tolist())
        print("\nPrimeiras 3 linhas (Dataset real):")
        # Mostrar apenas colunas com algo para não poluir
        print(df.head(3).dropna(how='all', axis=1).to_json(orient='records', force_ascii=False))
    except Exception as e:
        print(f"Erro ao ler {f}: {e}")
