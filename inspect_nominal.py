import os
import pandas as pd
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "dados", "2026", "MVI 2026.xls")
    df = pd.read_excel(file_path)
    print("Primeiras 15 linhas:")
    print(df.head(15))
except Exception as e:
    print(e)
