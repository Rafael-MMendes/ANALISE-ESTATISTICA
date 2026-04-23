import pandas as pd

df = pd.read_excel('Prisões 2025.xlsx', header=None)

# 1. Forward fill na coluna 0 (Data) para lidar com células mescladas
df[0] = df[0].ffill()

# 2. Extract Data (format DD/MM/YYYY)
df['Data Extracao'] = df[0].astype(str).str.extract(r'(\d{2}/\d{2}/\d{4})')
df = df.dropna(subset=['Data Extracao'])
df['Data'] = pd.to_datetime(df['Data Extracao'], format='%d/%m/%Y', errors='coerce')
df = df.dropna(subset=['Data'])

# 3. Cidade is at index 11
df['Cidade_Raw'] = df[11]

# 4. Filter empty cities
df = df.dropna(subset=['Cidade_Raw'])

# 5. Print some counts to see if it makes sense
print(df[['Data', 'Cidade_Raw']].head(20).to_string())
print(f"Total de registros válidos com Data e Cidade: {len(df)}")
