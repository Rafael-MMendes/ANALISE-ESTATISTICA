import pandas as pd
import glob
import os
import sys

def find_file(keyword, ano):
    path = f"d:/Nova pasta/Dashboard - Antigravity/dados/{ano}/*.*"
    all_files = glob.glob(path)
    files = [f for f in all_files if f.lower().endswith(('.xls', '.xlsx'))]
    matched_files = [f for f in files if keyword.upper() in f.upper() and 'TENTATIVA' not in f.upper()]
    return sorted(matched_files)[-1] if matched_files else None

file_path = find_file('MVI', 2026)
if not file_path:
    print("Arquivo MVI 2026 não encontrado.")
    sys.exit(1)

print(f"Lendo: {file_path}")

try:
    # Tenta ler com calamine para evitar problemas de corrupção comuns nesses arquivos
    raw_df = pd.read_excel(file_path, header=None, engine='calamine')
except:
    raw_df = pd.read_excel(file_path, header=None)

target_row = 0
for i, row in raw_df.head(25).iterrows():
    row_str = [str(c).upper().strip() for c in row]
    if 'DATA DO FATO' in row_str or 'DATA' in row_str:
        target_row = i
        break

df = pd.read_excel(file_path, header=target_row, engine='calamine' if 'engine' in locals() else None)
print("Colunas encontradas:")
print(df.columns.tolist())
print("\nExemplo de dados (primeira linha):")
print(df.iloc[0].to_dict())
