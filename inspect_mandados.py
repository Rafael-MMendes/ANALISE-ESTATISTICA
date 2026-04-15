import pandas as pd

file_name = 'Cumprimento de Mandados 2025.xls'
print("--- TESTANDO CALAMINE E HEADERS ---")
try:
    df = pd.read_excel(file_name, engine='calamine')
    print("Shape:", df.shape)
    print(df.head(5).to_string())
except Exception as e:
    print("Calamine falhou:", e)
    try:
        df = pd.read_excel(file_name)
        print("Normal Shape:", df.shape)
        print(df.head(5).to_string())
    except Exception as e2:
        print("Normal falhou:", e2)
