import pandas as pd

file_path = 'TCO 2025.xls'

print("--- TENTANDO LER COMO HTML ---")
try:
    dfs = pd.read_html(file_path, encoding='utf-8')
    df = dfs[0]
    print(f"Lido com sucesso como HTML. Shape: {df.shape}")
    print(df.columns.tolist()[:10])
    print(df.head(5).to_string())
except Exception as e:
    print(f"Erro ao ler como HTML (utf-8): {e}")
    try:
        dfs = pd.read_html(file_path, encoding='latin1')
        df = dfs[0]
        print(f"Lido com sucesso como HTML (latin1). Shape: {df.shape}")
        print(df.columns.tolist()[:10])
        print(df.head(5).to_string())
    except Exception as e2:
        print(f"Erro ao ler como HTML (latin1): {e2}")

print("\n--- TENTANDO LER COMO CSV ---")
try:
    df = pd.read_csv(file_path, sep='\t', encoding='utf-16')
    print(f"Lido com sucesso como CSV (utf-16). Shape: {df.shape}")
    print(df.columns.tolist()[:10])
    print(df.head(5).to_string())
except Exception as e:
    print(f"Erro ao ler como CSV (utf-16): {e}")
    try:
        df = pd.read_csv(file_path, sep='\t', encoding='latin1')
        print(f"Lido com sucesso como CSV (latin1). Shape: {df.shape}")
        print(df.columns.tolist()[:10])
        print(df.head(5).to_string())
    except Exception as e2:
        print(f"Erro ao ler como CSV (latin1): {e2}")

