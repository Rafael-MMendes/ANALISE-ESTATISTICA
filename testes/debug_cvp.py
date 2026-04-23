import pandas as pd

df = pd.read_excel('CVP Geral 2025.xls', header=8)
print("COLUNAS ORIGINAIS:")
print([str(c) for c in df.columns])

cols_interesse = ['NATUREZA', 'JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ', 'TOTAL']
valid_cols = []
for c in df.columns:
    if str(c).strip().upper() in cols_interesse:
        valid_cols.append(c)

print("\nCOLUNAS VALIDAS FILTRADAS:")
print(valid_cols)

df = df[valid_cols]
df.columns = [str(c).strip().upper() for c in valid_cols]
print("\nANTES DO DROPNA NA NATUREZA:", len(df))
df = df.dropna(subset=['NATUREZA'])
print("DEPOIS DO DROPNA:", len(df))

print("\nVALORES NA NATUREZA:")
print(df['NATUREZA'].tolist())

# Remover a linha de TOTAL GERAL
df = df[~df['NATUREZA'].astype(str).str.contains('TOTAL|^\\d+$', regex=True, case=False)]
print("\nDEPOIS DA LIMPEZA DO TOTAL:", len(df))
print(df['NATUREZA'].tolist())
