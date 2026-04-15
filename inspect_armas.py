import pandas as pd

file_name = 'Armas 2025.xls'

print("--- EXCEL NORMAL ---")
try:
    df1 = pd.read_excel(file_name)
    print("Normal lido com sucesso", df1.shape)
    print(df1.columns)
    print(df1.head())
except Exception as e:
    print(f"Erro normal: {e}")

print("\n--- EXCEL HEADER=8 ---")
try:
    df2 = pd.read_excel(file_name, header=8)
    print("Header 8 lido com sucesso", df2.shape)
    print(df2.columns)
    print(df2.head())
except Exception as e:
    print(f"Erro header 8: {e}")

print("\n--- CALAMINE ---")
try:
    df3 = pd.read_excel(file_name, engine='calamine')
    print("Calamine lido com sucesso", df3.shape)
    print(df3.columns)
    print(df3.head())
except Exception as e:
    print(f"Erro calamine: {e}")
