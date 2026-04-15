import pandas as pd

try:
    df = pd.read_excel('TCO 2025.xls')
    print("--- COLUNAS ---")
    print(df.columns.tolist())
    
    print("\n--- AMOSTRA DE DADOS ---")
    cols = ['Nº da ocorrência', 'Endereço'] if 'Nº da ocorrência' in df.columns else df.columns[:5]
    print(df[cols].head(10).to_string())
except Exception as e:
    print(f"Erro ao ler TCO (tentativa inicial): {e}")

try:
    df = pd.read_excel('TCO 2025.xls', header=8)
    print("\n--- COLUNAS (HEADER=8) ---")
    print(df.columns.tolist())
    
    print("\n--- AMOSTRA DE DADOS (HEADER=8) ---")
    cols = [c for c in df.columns if 'ocorrência' in str(c).lower() or 'endereço' in str(c).lower() or 'numero' in str(c).lower()]
    if not cols:
        cols = df.columns[:5]
    print(df[cols].head(10).to_string())
except Exception as e:
    print(f"Erro ao ler TCO com header=8: {e}")
