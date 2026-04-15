import pandas as pd

file_path = '03.0 - Relação  Nominal (Ano).xls'
try:
    df = pd.read_excel(file_path, header=None)
    for i, row in df.head(40).iterrows():
        vals = [str(x)[:50] for x in row.dropna().tolist()]
        if vals:
            print(f"Row {i}: {vals}")
except Exception as e:
    print(f"Error: {e}")
