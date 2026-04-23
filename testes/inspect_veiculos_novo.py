import pandas as pd
df = pd.read_excel('dados/2026/Veiculo Recuperado 2026.xls', engine='calamine', header=None)
print(df.head(15).to_string())
