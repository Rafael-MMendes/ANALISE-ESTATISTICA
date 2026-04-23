import pandas as pd
import unicodedata
import re

def remove_accents(input_str):
    if not isinstance(input_str, str): return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

cidades_9bpm = [
    'Água Branca', 'Canapi', 'Delmiro Gouveia', 'Inhapi', 
    'Mata Grande', 'Olho d Água do Casado', 'Pariconha', 'Piranhas'
]
norm_cities = {remove_accents(c.upper()): c for c in cidades_9bpm}

def extract_city_from_text(text):
    text = remove_accents(str(text).upper())
    for norm_c, orig_c in norm_cities.items():
        if norm_c in text:
            return orig_c
    if "OLHO D" in text and "CASAD" in text: return "Olho d Água do Casado"
    if "AGUA BRANCA" in text: return "Água Branca"
    if "DELMIRO" in text: return "Delmiro Gouveia"
    if "MATA GRANDE" in text: return "Mata Grande"
    if "INHAPI" in text: return "Inhapi"
    if "CANAPI" in text: return "Canapi"
    if "PIRANHAS" in text: return "Piranhas"
    if "PARICONHA" in text: return "Pariconha"
    return None

file_path = 'Cumprimento de Mandados 2025.xls'
df_raw = pd.read_excel(file_path, engine='calamine')
data = []

# Regex para data DD/MM/YYYY
date_pattern = re.compile(r'(\d{2}/\d{2}/\d{4})')

for _, row in df_raw.iterrows():
    row_text = " ".join([str(x) for x in row.values if pd.notna(x)])
    
    # Ignora logs do sistema
    if 'Gerado em:' in row_text or 'Pág:' in row_text:
        continue
        
    date_match = date_pattern.search(row_text)
    if date_match:
        data_fato = date_match.group(1)
        cidade = extract_city_from_text(row_text)
        if cidade:
            data.append({'Data Extracao': data_fato, 'Cidade': cidade})

df = pd.DataFrame(data)
if not df.empty:
    df['Data'] = pd.to_datetime(df['Data Extracao'], format='%d/%m/%Y', errors='coerce')
    df = df.dropna(subset=['Data'])
    df = df[df['Data'].dt.year == 2025]

print("--- EXTRACAO FINAL ---")
print(df.head(20).to_string())
print(f"Total registros: {len(df)}")
