import pandas as pd
df = pd.read_excel('dados/2026/Armas 2026.xls', engine='calamine', header=None)
for i, col in enumerate(df.iloc[0]):
    print(f"Index {i}: {col}")
