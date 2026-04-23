import os
import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

find_file_code = """
import glob
import os

def find_file(keyword, ano):
    search_pattern = f"dados/{ano}/*{keyword}*.xls*"
    files = glob.glob(search_pattern)
    if not files:
        all_files = glob.glob(f"dados/{ano}/*.*")
        files = [f for f in all_files if keyword.lower() in f.lower() and f.lower().endswith(('.xls', '.xlsx'))]
        
    if 'MVI' in keyword.upper() and 'TENTATIVA' not in keyword.upper():
        files = [f for f in files if 'Tentativa' not in f and 'TENTATIVA' not in f.upper()]
        
    if files:
        return files[0]
    return None
"""

if "def find_file" not in text:
    text = text.replace("import plotly.express as px\n", "import plotly.express as px\n" + find_file_code + "\n")

# Replace function signatures
defs_to_replace = [
    'load_data_mvi', 'load_data_tco', 'load_data_mandados', 'load_data_visita',
    'load_data_veiculos', 'load_data_armas', 'load_data_prisoes', 'load_data_drogas', 'load_data_cvp'
]

for load_f in defs_to_replace:
    # Use re.sub to inject keyword and ano dynamically. Note the \n and \s* are carefully matched
    pattern = re.compile(r'(def ' + load_f + r')\(file_path\):(\s*)(try:|#|import)')
    replacement = r'\1(keyword, ano):\2file_path = find_file(keyword, ano)\2if not file_path: return pd.DataFrame()\2\3'
    text = pattern.sub(replacement, text)

# Replace hardcoded year for internal filtering
text = re.sub(r"df\['Data'\].dt.year == 2025", r"df['Data'].dt.year == ano", text)

# Routing specific changes
sidebar_code = """
st.sidebar.markdown("<h3>Filtro de Gestão Temporal</h3>", unsafe_allow_html=True)
ano_selecionado = st.sidebar.selectbox("Selecione o Ano Base", [2025, 2026], index=1)
"""

if "ano_selecionado = st.sidebar.selectbox" not in text:
    text = text.replace("render_header()\n", "render_header()\n" + sidebar_code)

# Specific data paths replace
text = text.replace("df_mvi = load_data_mvi('MVI 2025.xls')", "df_mvi = load_data_mvi('MVI', ano_selecionado)")
text = text.replace("df_tentativa = load_data_mvi('Tentativa de MVI 2025.xls')", "df_tentativa = load_data_mvi('Tentativa', ano_selecionado)")
text = text.replace("df_tco = load_data_tco('TCO 2025.xls')", "df_tco = load_data_tco('TCO', ano_selecionado)")
text = text.replace("df_mandados = load_data_mandados('Cumprimento de Mandados 2025.xls')", "df_mandados = load_data_mandados('Mandado', ano_selecionado)")
text = text.replace("df_visita = load_data_visita('Visita Comunitaria 2025.xls')", "df_visita = load_data_visita('Visita Comun', ano_selecionado)")
text = text.replace("df_veiculos = load_data_veiculos('Veiculo Recuperado 2025.xls')", "df_veiculos = load_data_veiculos('Recuperado', ano_selecionado)")
text = text.replace("df_armas = load_data_armas('Armas 2025.xls')", "df_armas = load_data_armas('Armas', ano_selecionado)")
text = text.replace("df_prisoes = load_data_prisoes('Prisões 2025.xlsx')", "df_prisoes = load_data_prisoes('Pris', ano_selecionado)")
text = text.replace("df_drogas = load_data_drogas('Drogas 2025.xls')", "df_drogas = load_data_drogas('Drogas', ano_selecionado)")
text = text.replace("df_cvp = load_data_cvp('CVP Geral 2025.xls')", "df_cvp = load_data_cvp('CVP', ano_selecionado)")

# Consolidado Update
text = text.replace("def render_consolidado_module():", "def render_consolidado_module(ano_selecionado):")
text = text.replace("render_consolidado_module()", "render_consolidado_module(ano_selecionado)")
text = text.replace("Relatório Consolidado 2025", "Relatório Consolidado")

# Fix missing title format
text = text.replace(
    "<h2 style='text-align: center; color: #a371f7 !important; margin-bottom: 2rem;'>Relatório Consolidado</h2>",
    "<h2 style='text-align: center; color: #a371f7 !important; margin-bottom: 2rem;'>Relatório Consolidado {ano_selecionado}</h2>"
)

text = text.replace(
    "<h1 style='text-align: center;'>🛡️ Dashboard Criminalidade (2025)</h1>",
    "<h1 style='text-align: center;'>🛡️ Dashboard Criminalidade</h1>"
)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Refactoring Done")
