import pandas as pd
df = pd.read_excel('dados/2026/Armas 2026.xls', engine='calamine', header=None)
print(df.head(10).to_string())
