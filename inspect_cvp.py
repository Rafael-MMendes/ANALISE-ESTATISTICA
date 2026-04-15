import pandas as pd

df = pd.read_excel('CVP Geral 2025.xls', header=None)

for i, row in df.iterrows():
    # conta valores não nulos
    num_validos = row.count()
    if num_validos > 3:
        valores = [str(x) for x in row.dropna().tolist()][:15]
        print(f"Linha {i}: {valores}")
