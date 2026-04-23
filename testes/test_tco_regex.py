import pandas as pd
import unicodedata

def remove_accents(input_str):
    if not isinstance(input_str, str): return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

cidades_9bpm = [
    'Água Branca', 'Canapi', 'Delmiro Gouveia', 'Inhapi', 
    'Mata Grande', 'Olho d Água do Casado', 'Pariconha', 'Piranhas'
]

norm_cities = {remove_accents(c.upper()): c for c in cidades_9bpm}

def extract_city(address):
    if pd.isna(address): return None
    addr_clean = remove_accents(str(address).upper())
    
    for norm_c, orig_c in norm_cities.items():
        if norm_c in addr_clean:
            return orig_c
            
    # Casos especiais
    if "OLHO D" in addr_clean and "CASADO" in addr_clean:
        return "Olho d Água do Casado"
    if "AGUA BRANCA" in addr_clean:
        return "Água Branca"
        
    return None

df = pd.read_excel('TCO 2025.xls', engine='calamine')
df = df.dropna(subset=['Nº Ocorrência', 'Endereço'])
df['Data Extracao'] = df['Nº Ocorrência'].astype(str).str.extract(r'(\d{2}/\d{2}/\d{4})')
df['Cidade_Clean'] = df['Endereço'].apply(extract_city)

print("TOTAL ROWS:", len(df))
print("CIDADES FOUND:")
print(df['Cidade_Clean'].value_counts(dropna=False))
