import pandas as pd

file_name = 'Prisões 2025.xlsx'

print("--- LENDO XLSX ---")
try:
    df = pd.read_excel(file_name)
    print("Normal lido com sucesso", df.shape)
    
    # Imprime os nomes das colunas e as 3 primeiras linhas
    for i, col in enumerate(df.columns):
        print(f"Index {i}: {col}")
        
    print(df.head(3).to_string())
except Exception as e:
    print(f"Erro normal: {e}")
