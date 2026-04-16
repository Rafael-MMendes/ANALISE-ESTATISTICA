import streamlit as st # Reload Forced at 2026-03-31 16:25
import pandas as pd
import numpy as np
import plotly.express as px

import glob
import subprocess
import time

@st.dialog("Autenticação CAD Restrita")
def open_token_dialog():
    st.warning("🔑 O robô do CAD solicitou o Token de Segurança.")
    token_input = st.text_input("Insira o Token do CAD (Cole ou digite):", key="cad_token", max_chars=12)
    if st.button("Confirmar Autenticação", use_container_width=True):
        if token_input:
            with open("token_response.txt", "w", encoding="utf-8") as f:
                f.write(token_input)
            with open("coleta_status.txt", "w", encoding="utf-8") as f:
                f.write("RUNNING_CAD")
            st.rerun()
import os
from io import BytesIO
import base64
from fpdf import FPDF, FontFace

# ----------------- CONSTANTS -----------------
MESES_LIST = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

# ----------------- EXPORT UTILS -----------------
class PDFRelatorio(FPDF):
    def __init__(self, title, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.doc_title = title

    def header(self):
        # Secção de Topo Azul
        self.set_fill_color(13, 56, 120)  # Azul PMAL Profundo
        self.rect(0, 0, 297, 26, 'F')
        
        # Faixas nas cores de Alagoas/Brasil
        self.set_fill_color(0, 156, 59) # Verde
        self.rect(0, 26, 297, 1.5, 'F')
        self.set_fill_color(255, 223, 0) # Amarelo
        self.rect(0, 27.5, 297, 1.5, 'F')

        # Posicionamento dos Brasões Oficiais
        if os.path.exists("brasao_municipio.png"):
            self.image("brasao_municipio.png", x=12, y=3, w=18)
        if os.path.exists("brasao_9bpm.png"):
            self.image("brasao_9bpm.png", x=267, y=3, w=18)

        # Inserção do Texto Institucional no Topo
        self.set_y(5)
        self.set_font("helvetica", "B", 14)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, "POLÍCIA MILITAR DE ALAGOAS", ln=True, align="C")
        
        self.set_font("helvetica", "", 10)
        self.cell(0, 5, "9º Batalhão de Polícia Militar - Batalhão de Divisas", ln=True, align="C")
        
        self.set_font("helvetica", "I", 9)
        self.set_text_color(200, 220, 255) # Azul mais claro
        self.cell(0, 5, "Análise de Dados - P3 do 9º Batalhão", ln=True, align="C")
        
        self.ln(15) # Espaço adicional para centralizar melhor o conteúdo
        
        # Título Específico do Relatório (Fundo Azul c/ Texto Branco)
        # Largura da página L: 297mm. Margens: 10mm cada lado = 277mm útil.
        self.set_fill_color(13, 56, 120)  # Azul PMAL Profundo
        self.rect(10, 42, 277, 10, 'F')
        
        self.set_y(43.5)
        self.set_font("helvetica", "B", 12)
        self.set_text_color(255, 255, 255) # Branco
        self.cell(0, 7.5, f"ESTATÍSTICA: {self.doc_title.upper()}", ln=True, align="C")
        self.ln(10)
        
        # Aplicação Sutil da Marca D'água no Corpo da Página
        try:
            if os.path.exists("brasao_9bpm.png"):
                with self.local_context(fill_opacity=0.08):
                    self.image("brasao_9bpm.png", x=108, y=55, w=80)
        except Exception:
            pass

    def footer(self):
        self.set_y(-12)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Página {self.page_no()} / {{nb}}  -  Dashboard MVI Gerencial (Criado por Inteligência Analítica)", align="C")


def convert_df_to_pdf(df, title, figs=None):
    """Converte um DataFrame Pandas para binário PDF com cabeçalho institucional e gráficos opcionais"""
    try:
        pdf = PDFRelatorio(title)
        pdf.add_page("L")
        pdf.set_font("helvetica", size=8.5)
        
        def format_val(val):
            if pd.isna(val): return ""
            if isinstance(val, (int, float)):
                if val == 0: return "0"
                return f"{val:,.0f}".replace(',', '.')
            if isinstance(val, str) and "↑" in val or "↓" in val:
                return val
            s_val = str(val)
            if s_val.endswith('.0'): return s_val[:-2]
            return s_val

        cols = list(df.columns)
        width_map = {
            'Indicador': 4.5, 
            'Janeiro': 1.6, 'Fevereiro': 1.6, 'Março': 1.6, 'Abril': 1.6, 
            'Maio': 1.6, 'Junho': 1.6, 'Julho': 1.6, 'Agosto': 1.6, 
            'Setembro': 1.6, 'Outubro': 1.6, 'Novembro': 1.6, 'Dezembro': 1.6, 
            'TOTAL': 1.6,
            'Nome da Vítima': 6.5, 'Nome': 6.5, 'Data do Fato': 2.5,
            'Data': 2.5, 'Idade': 1.2, 'Nº BOU': 2.6, 'Local (Bairro)': 3.8,
            'Bairro': 3.8, 'Subjetividade Complementar': 5.5, 'Natureza': 4.2,
            'Tipo de Morte': 4.2, 'Cidade': 2.8
        }
        col_widths = [width_map.get(c, 2.0) for c in cols] if cols else None
        hd_style = FontFace(emphasis="B", color=(255, 255, 255), fill_color=(13, 56, 120))

        with pdf.table(text_align="CENTER", col_widths=col_widths, headings_style=hd_style, line_height=5.5) as table:
            row = table.row()
            for col in cols: row.cell(str(col))
            for i, (_, df_row) in enumerate(df.iterrows()):
                fill_color = (255, 255, 255) if i % 2 == 0 else (232, 242, 250)
                row = table.row(style=FontFace(fill_color=fill_color, color=(0, 0, 0)))
                for col_name, item in zip(df.columns, df_row):
                    val = format_val(item)
                    if col_name == 'Indicador' and isinstance(val, str):
                        val = val.replace('(g)', '').strip()
                    cell_style = None
                    if isinstance(val, str) and '%' in val:
                        ind_str = str(df_row.get('Indicador', ''))
                        is_crim = any(c in ind_str for c in ['MVI', 'CVLI', 'Tentativa de MVI', 'CVP Geral'])
                        if val.startswith('+'):
                            cell_style = FontFace(color=(255, 0, 0) if is_crim else (0, 128, 0), fill_color=fill_color)
                        elif val.startswith('-'):
                            cell_style = FontFace(color=(0, 128, 0) if is_crim else (255, 0, 0), fill_color=fill_color)
                    if cell_style: row.cell(val, style=cell_style)
                    else: row.cell(val)
        
        # Inserção de Gráficos (Segunda Página em diante)
        if figs:
            for f_title, fig in figs.items():
                pdf.add_page("L")
                # Título da Seção Gráfica
                pdf.set_y(45)
                pdf.set_font("helvetica", "B", 14)
                pdf.set_text_color(13, 56, 120)
                pdf.cell(0, 10, f"ANÁLISE VISUAL: {f_title.upper()}", ln=True, align="C")
                pdf.ln(5)
                
                # Exportar gráfico para stream de memória
                try:
                    # Tenta usar to_image (requer kaleido) ou cai para mensagem informativa
                    img_bytes = fig.to_image(format="png", width=1200, height=600, scale=2)
                    img_buffer = BytesIO(img_bytes)
                    pdf.image(img_buffer, x=10, y=60, w=277)
                except Exception:
                    # Se falhar (provavelmente por falta do kaleido), mostra mensagem informativa
                    pdf.set_font("helvetica", "I", 10)
                    pdf.set_text_color(100, 100, 100)
                    pdf.cell(0, 10, "[Gráfico não disponível - instale 'kaleido' para habilitar]", ln=True, align="C")
                    pdf.ln(5)
                    # Ainda mostra um placeholder vazio onde o gráfico iria
                    pdf.rect(10, 60, 277, 150, style='D')

        return bytes(pdf.output())
    except Exception as e:
        print(f"Erro PDF: {str(e)}")
        return b""

@st.cache_data(show_spinner="Formatando Planilha Excel...")
def convert_df_to_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatorio_9BPM')
    return output.getvalue()

def _apply_table_style(df, highlight_row=None):
    st_df = df.style.set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#F1F5F9'), ('color', '#0D3878'), ('font-weight', 'bold'), ('text-align', 'center'), ('border', '1px solid #E2E8F0')]},
        {'selector': 'td', 'props': [('border', '1px solid #E2E8F0'), ('text-align', 'center'), ('font-size', '0.9rem')]}
    ]).set_properties(**{'background-color': 'white', 'color': '#1E293B'})
    if highlight_row is not None:
        def highlight_specific_row(x):
            return ['background-color: #EFF6FF; font-weight: bold; color: #1E40AF;' if x.name == highlight_row else '' for _ in x]
        st_df = st_df.apply(highlight_specific_row, axis=1)
    return st_df

def find_file(keyword, ano):
    all_files = glob.glob(f"dados/{ano}/*.*")
    files = [f for f in all_files if f.lower().endswith(('.xls', '.xlsx'))]
    
    matched_files = []
    for f in files:
        f_upper = f.upper()
        if keyword.upper() == 'MVI':
            if ('MVI' in f_upper or 'CVLI' in f_upper or 'NOMINAL' in f_upper) and 'TENTATIVA' not in f_upper:
                matched_files.append(f)
        else:
            if keyword.upper() in f_upper:
                matched_files.append(f)
                
    if matched_files:
        # Pega sempre o mais recente/último da pasta caso existam cópias (CVLI 1.xlsx, CVLI 2.xlsx)
        return sorted(matched_files)[-1]
    return None


st.set_page_config(
    page_title="Gestão de Dados 9º BPM - PMAL",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS - Light Modern Theme (9º BPM PMAL)
st.markdown("""
<style>
    /* === VARIÁVEIS DE COR === */
    :root {
        --azul-pmal: #0D3878;
        --azul-claro: #1E5AAF;
        --azul-bbb: #0047AB;
        --vermelho-al: #ED1C24;
        --branco: #FFFFFF;
        --fundo-principal: #F1F5F9;
        --fundo-card: #FFFFFF;
        --fundo-secundario: #F8FAFC;
        --texto-principal: #1E293B;
        --texto-secundario: #64748B;
        --texto-terciario: #94A3B8;
        --borda-clara: #E2E8F0;
        --borda-media: #CBD5E1;
        --sombra-xs: 0 1px 2px rgba(0,0,0,0.04);
        --sombra-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        --sombra-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05);
        --sombra-lg: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04);
        --raio-sm: 8px;
        --raio-md: 12px;
        --raio-lg: 16px;
        --verde-sucesso: #10B981;
        --amarelo-atencao: #F59E0B;
        --roxo-acento: #8B5CF6;
    }

    /* === FUNDO GLOBAL === */
    .stApp {
        background-color: var(--fundo-principal);
        color: var(--texto-principal);
        font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    }

    /* === HEADER INSTITUCIONAL === */
    .header-wrapper {
        margin-top: -4px;
        margin-bottom: 20px;
    }

    .flag-strip {
        height: 6px;
        width: 100%;
        display: flex;
        border-radius: var(--raio-md) var(--raio-md) 0 0;
        overflow: hidden;
    }
    .flag-red { background-color: var(--vermelho-al); flex: 1; }
    .flag-white { background-color: var(--branco); flex: 1; }
    .flag-blue { background-color: var(--azul-bbb); flex: 1; }

    .main-header {
        background: linear-gradient(135deg, rgba(13,56,120,0.85) 0%, rgba(30,90,175,0.85) 100%);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        padding: 24px 32px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: var(--sombra-md);
    }

    .header-left {
        display: flex;
        align-items: center;
        gap: 20px;
    }

    .header-logos {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .header-logo {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background: rgba(255,255,255,0.15);
        padding: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }

    .header-logo img {
        width: 56px;
        height: 56px;
        border-radius: 50%;
        object-fit: contain;
        display: block;
    }

    .header-text h1 {
        color: var(--branco) !important;
        font-size: 1.5rem !important;
        font-weight: 900 !important;
        margin: 0 !important;
        letter-spacing: 0.3px;
    }

    .header-text p {
        color: rgba(255,255,255,0.85) !important;
        font-size: 0.9rem !important;
        margin: 4px 0 0 0 !important;
        font-weight: 400;
    }

    .header-badge {
        background: rgba(255,255,255,0.12);
        padding: 8px 18px;
        border-radius: 24px;
        color: var(--branco);
        font-size: 0.82rem;
        font-weight: 500;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255,255,255,0.15);
    }

    /* === SIDEBAR OCULTA === */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"][aria-collapsed="true"],
    section[data-testid="stSidebar"][aria-collapsed="false"] {
        display: none !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
        overflow: hidden !important;
    }
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    button[data-testid="baseButton-header"],
    button[kind="header"] {
        display: none !important;
    }

    /* === SELECTBOX === */
    .stSelectbox label {
        color: var(--texto-secundario) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }

    /* === TABS MODERNAS - ESTILO CORPORATIVO MINIMALISTA === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 36px;
        background-color: transparent;
        padding: 0px 8px;
        border-bottom: 1px solid var(--borda-clara) !important;
        border-top: none !important;
        border-left: none !important;
        border-right: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        margin-bottom: 28px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 56px;
        background-color: transparent !important;
        border-radius: 0 !important;
        padding: 0 6px;
        font-weight: 600;
        font-size: 0.95rem;
        color: var(--texto-secundario);
        border: none !important;
        border-bottom: 2px solid transparent !important;
        transition: color 0.2s ease, border-color 0.2s ease;
        letter-spacing: 0.2px;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: transparent !important;
        color: var(--azul-pmal);
    }
    .stTabs [aria-selected="true"] {
        background: transparent !important;
        color: var(--azul-pmal) !important;
        box-shadow: none !important;
        border-bottom: 2px solid var(--azul-pmal) !important;
    }

    /* === ESPAÇAMENTO ENTRE SEÇÕES (GUTTER SYSTEM) === */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 2rem;
    }
    div[data-testid="stMetric"] {
        margin-bottom: 8px;
    }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stVerticalBlock"] > div:has(> [data-testid="stMetric"]) {
        padding-bottom: 12px;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        max-width: 100% !important;
    }
    hr {
        margin: 28px 0 !important;
    }
    h2 {
        margin-top: 1rem !important;
        margin-bottom: 1.25rem !important;
    }
    h3 {
        margin-top: 0.75rem !important;
        margin-bottom: 0.75rem !important;
    }
    /* === SUBTABS === */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1.5rem;
    }

    /* === CARDS KPI === */
    .kpi-card {
        background: var(--fundo-card);
        border-radius: var(--raio-md);
        padding: 22px 24px;
        box-shadow: var(--sombra-sm);
        margin-bottom: 12px;
        border: 1px solid var(--borda-clara);
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
    }
    .kpi-card.card-blue::before { background: linear-gradient(180deg, var(--azul-pmal), var(--azul-claro)); }
    .kpi-card.card-red::before { background: linear-gradient(180deg, var(--vermelho-al), #F87171); }
    .kpi-card.card-green::before { background: linear-gradient(180deg, var(--verde-sucesso), #34D399); }
    .kpi-card.card-orange::before { background: linear-gradient(180deg, var(--amarelo-atencao), #FBBF24); }
    .kpi-card.card-purple::before { background: linear-gradient(180deg, var(--roxo-acento), #A78BFA); }

    .kpi-card:hover {
        box-shadow: var(--sombra-md);
    }

    .kpi-title {
        color: var(--texto-secundario);
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 10px;
        letter-spacing: 0.6px;
    }

    .kpi-value {
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 6px;
        letter-spacing: -0.5px;
    }
    .kpi-value.val-blue { color: var(--azul-pmal); }
    .kpi-value.val-red { color: var(--vermelho-al); }
    .kpi-value.val-green { color: var(--verde-sucesso); }
    .kpi-value.val-orange { color: var(--amarelo-atencao); }
    .kpi-value.val-purple { color: var(--roxo-acento); }

    .kpi-delta {
        font-size: 0.8rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .kpi-delta.positive { color: var(--verde-sucesso); }
    .kpi-delta.negative { color: var(--vermelho-al); }

    /* === METRICS STREAMLIT === */
    div[data-testid="stMetric"] {
        background: var(--fundo-card);
        padding: 20px;
        border-radius: var(--raio-md);
        border: 1px solid var(--borda-clara);
        box-shadow: var(--sombra-xs);
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    div[data-testid="stMetricLabel"] {
        color: var(--texto-secundario) !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    div[data-testid="stMetricValue"] {
        color: var(--azul-pmal) !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
        line-height: 1.2 !important;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        margin-top: 4px !important;
    }

    /* === TÍTULOS === */
    h1, h2, h3 {
        font-weight: 700 !important;
        color: var(--azul-pmal) !important;
    }
    h2 {
        font-size: 1.4rem !important;
        margin-bottom: 0.75rem !important;
    }
    h3 {
        font-size: 1.1rem !important;
        color: var(--texto-principal) !important;
    }

    /* === PARÁGRAFOS E TEXTO === */
    p, .stMarkdown {
        color: var(--texto-principal);
    }

    /* === BOTÕES === */
    .stButton > button {
        background: linear-gradient(135deg, var(--azul-pmal) 0%, var(--azul-claro) 100%);
        color: var(--branco);
        border: none;
        border-radius: var(--raio-sm);
        padding: 10px 24px;
        font-weight: 600;
        font-size: 0.88rem;
        box-shadow: var(--sombra-sm);
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--azul-claro) 0%, var(--azul-pmal) 100%);
    }

    /* === DOWNLOAD BUTTONS === */
    .stDownloadButton > button {
        background: var(--fundo-card);
        color: var(--azul-pmal);
        border: 1.5px solid var(--borda-media);
        border-radius: var(--raio-sm);
        padding: 8px 18px;
        font-weight: 600;
        font-size: 0.84rem;
    }
    .stDownloadButton > button:hover {
        background: var(--azul-pmal);
        color: var(--branco);
        border-color: var(--azul-pmal);
        transform: translateY(-3px);
        box-shadow: var(--sombra-md);
    }

    /* === DATAFRAME === */
    div[data-testid="stDataFrame"] {
        border-radius: var(--raio-md);
        overflow: hidden;
        box-shadow: var(--sombra-sm);
        border: 1px solid var(--borda-clara);
    }
    div[data-testid="stDataFrame"] table {
        color: var(--texto-principal) !important;
        background-color: var(--fundo-card) !important;
    }
    div[data-testid="stDataFrame"] th {
        background-color: var(--azul-pmal) !important;
        color: var(--branco) !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    div[data-testid="stDataFrame"] td {
        color: var(--texto-principal) !important;
        background-color: var(--fundo-card) !important;
        font-size: 0.88rem !important;
    }
    div[data-testid="stDataFrame"] tr:nth-child(even) td {
        background-color: var(--fundo-secundario) !important;
    }
    div[data-testid="stDataFrame"] tr:hover td {
        background-color: #E0EAFF !important;
    }
    [data-testid="stDataFrameResizable"] {
        --theme-dataframe: var(--fundo-card);
    }

    /* === FORÇA COR TEXTO EM TODOS OS DATAFRAMES === */
    div[data-testid="stDataFrame"] td div,
    div[data-testid="stDataFrame"] td span,
    div[data-testid="stDataFrame"] td p,
    div[data-testid="stDataFrame"] th div,
    div[data-testid="stDataFrame"] th span {
        color: var(--texto-principal) !important;
    }
    div[data-testid="stDataFrame"] th div,
    div[data-testid="stDataFrame"] th span {
        color: var(--branco) !important;
    }

    /* AG Grid interno do Streamlit */
    .stDataFrame div[class*="StyledDataFrame"] td,
    .stDataFrame div[class*="StyledDataFrame"] span,
    .stDataFrame div[class*="StyledDataFrame"] div {
        color: var(--texto-principal) !important;
    }
    div[data-testid="stDataFrame"] .dvn-scroller div[class*="cell"],
    div[data-testid="stDataFrame"] .dvn-scroller span {
        color: var(--texto-principal) !important;
    }

    /* Tabelas styled (st.dataframe com style.map) */
    .stDataFrame table tbody tr td {
        color: var(--texto-principal) !important;
    }
    .stDataFrame table thead tr th {
        color: var(--branco) !important;
        background-color: var(--azul-pmal) !important;
    }

    /* === SEPARADORES === */
    hr {
        border: none !important;
        height: 1px !important;
        background-color: var(--borda-clara) !important;
        margin: 20px 0 !important;
    }

    /* === RADIO BUTTONS === */
    .stRadio > label {
        color: var(--texto-principal) !important;
        font-weight: 600;
        font-size: 0.88rem;
    }
    .stRadio [data-baseweb="radio"] span {
        color: var(--texto-principal);
    }

    /* === SPINNER === */
    .stSpinner > div {
        color: var(--azul-pmal);
    }

    /* === SELECTBOX CONTAINER === */
    div[data-baseweb="select"] {
        border-radius: var(--raio-sm) !important;
    }

    /* === WARNING / INFO / SUCCESS BOXES === */
    .stAlert {
        border-radius: var(--raio-sm) !important;
        border: none !important;
    }

    /* === CORREÇÃO GRÁFICOS PLOTLY === */
    .js-plotly-plot .plotly .modebar {
        display: none !important;
    }

    /* === MÉTRICAS INLINE (DELTA) === */
    [data-testid="stMetricDelta"] svg {
        display: none;
    }

    /* === BOTÕES INDICADORES OPERACIONAIS (CARDS) === */
    div[data-testid="stButton"] > button {
        background: var(--fundo-card);
        color: var(--texto-principal);
        border: 1.5px solid var(--borda-clara);
        border-radius: var(--raio-md);
        padding: 12px 14px;
        font-weight: 600;
        font-size: 0.85rem;
        box-shadow: var(--sombra-xs);
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        text-align: center;
        white-space: nowrap;
    }
    div[data-testid="stButton"] > button:hover {
        background: var(--azul-pmal);
        color: var(--branco);
        border-color: var(--azul-pmal);
        transform: translateY(-3px);
        box-shadow: var(--sombra-md);
    }

    /* === SCROLLBAR CUSTOMIZADA === */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: var(--fundo-secundario);
    }
    ::-webkit-scrollbar-thumb {
        background: var(--borda-media);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--texto-terciario);
    }
</style>
""", unsafe_allow_html=True)



# ----------------- RENDERING MODULES -----------------

def _img_to_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

def render_header():
    logo_9bpm_b64 = _img_to_base64("brasao_9bpm.png")
    logo_municipio_b64 = _img_to_base64("brasao_municipio.png")

    logo_9bpm_img = f'<img src="data:image/png;base64,{logo_9bpm_b64}" alt="9º BPM">' if logo_9bpm_b64 else ""
    logo_municipio_img = f'<img src="data:image/png;base64,{logo_municipio_b64}" alt="Município">' if logo_municipio_b64 else ""

    st.markdown(f"""
    <div class="header-wrapper">
        <div class="flag-strip">
            <div class="flag-red"></div>
            <div class="flag-white"></div>
            <div class="flag-blue"></div>
        </div>
        <div class="main-header">
            <div class="header-left">
                <div class="header-logos">
                    <div class="header-logo">{logo_municipio_img}</div>
                    <div class="header-logo">{logo_9bpm_img}</div>
                </div>
                <div class="header-text">
                    <h1>Dashboard Estatístico</h1>
                    <p>Polícia Militar de Alagoas &mdash; 9º Batalhão (Delmiro Gouveia)</p>
                </div>
            </div>
            <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
                <div class="header-badge">
                    Sistema de Gestão de Dados
                </div>
                <div style="color: rgba(255,255,255,0.85); font-size: 0.75rem; font-weight: 500; text-align: right;">
                    Fonte de Dados: NEAC / CAD / Pentaho
                </div>
                <div style="color: rgba(255,255,255,0.85); font-size: 0.75rem; font-weight: 500; text-align: right; margin-top: 4px;">
                    Created By 2&#186; Sgt PM Monteiro e 3&#186; Sgt PM Alan Kleber
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data_mvi(keyword, ano):
    file_path = find_file(keyword, ano)
    if not file_path: return pd.DataFrame()
    try:
        # Carrega sem header primeiro para encontrar a linha correta dinamicamente
        raw_df = pd.read_excel(file_path, header=None)
        
        target_row = 0
        found_header = False
        for i, row in raw_df.head(25).iterrows():
            row_str = [str(c).upper().strip() for c in row]
            if 'DATA DO FATO' in row_str or 'DATA' in row_str:
                target_row = i
                found_header = True
                break
        
        # Recarrega com o header correto
        df = pd.read_excel(file_path, header=target_row)
        
        # Limpa nomes de colunas (proteção contra espaços invisíveis)
        df.columns = [str(c).strip() for c in df.columns]
            
        # Normalização de nomes de colunas caso venham variados
        map_cols = {
            'Data': 'Data do Fato', 'DATA': 'Data do Fato', 'Data do fato': 'Data do Fato',
            'Município': 'Cidade', 'MUNICIPIO': 'Cidade', 'Município do Fato': 'Cidade'
        }
        df = df.rename(columns=map_cols)
            
        # Busca colunas essenciais via aproximação se não achou exato
        if 'Data do Fato' not in df.columns:
            for col in df.columns:
                if 'DATA' in col.upper() and 'FATO' in col.upper():
                    df = df.rename(columns={col: 'Data do Fato'})
                    break
        
        if 'Cidade' not in df.columns:
            for col in df.columns:
                if 'CIDADE' in col.upper() or 'MUNIC' in col.upper():
                    df = df.rename(columns={col: 'Cidade'})
                    break
        
        # Garante a existência da coluna Nome (Normalizado)
        if 'Nome' not in df.columns:
           for col in df.columns:
               if 'NOME' in col.upper() and 'VIT' in col.upper():
                   df = df.rename(columns={col: 'Nome'})
                   break

        if 'Data do Fato' not in df.columns or 'Cidade' not in df.columns:
            st.error(f"Colunas essenciais não encontradas no arquivo: {file_path}")
            return pd.DataFrame()

        df['Data do Fato'] = df['Data do Fato'].replace(r'^\s*$', np.nan, regex=True)
        df['Data do Fato'] = df['Data do Fato'].ffill()
        df = df.dropna(subset=['Cidade', 'Data do Fato'])
        df['Data do Fato'] = df['Data do Fato'].astype(str)
        df = df[~df['Data do Fato'].str.contains('Total|TOTAL', na=False)]
        df['Data'] = pd.to_datetime(df['Data do Fato'], format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=['Data'])
        df = df[df['Data'].dt.year == ano]
        
        cidades_9bpm = [
            'Água Branca', 'Canapi', 'Delmiro Gouveia', 'Inhapi', 
            'Mata Grande', 'Olho d Água do Casado', 'Pariconha', 'Piranhas'
        ]
        df['Cidade'] = df['Cidade'].str.strip()
        df = df[df['Cidade'].isin(cidades_9bpm)]
        
        meses_pt = {i+1: m for i, m in enumerate(MESES_LIST)}
        df['Mês'] = df['Data'].dt.month.map(meses_pt)
        df['Mes_Num'] = df['Data'].dt.month

        # Identificação unificada de BOU (Apenas BO PM solicitado)
        def format_bou(row):
            import re
            def get_7(val):
                if pd.isna(val): return ""
                nums = "".join(re.findall(r'\d', str(val)))
                return nums[:7] if len(nums) >= 7 else nums
            
            if 'BO PM' in df.columns and pd.notna(row.get('BO PM')):
                return get_7(row['BO PM'])
            return "N/A"
        
        df['Nº BOU'] = df.apply(format_bou, axis=1)

        # Formatação de Idade (Garantir Inteiro Limpo)
        if 'Idade' in df.columns:
            def clean_idade(val):
                try:
                    v = pd.to_numeric(val, errors='coerce')
                    if pd.isna(v): return "N/A"
                    return str(int(v))
                except: return "N/A"
            df['Idade'] = df['Idade'].apply(clean_idade)

        return df
    except Exception as e:
        st.error(f"Erro ao ler {file_path}: {e}")
        return pd.DataFrame()

@st.cache_data
def load_data_cvli(keyword, ano):
    df = load_data_mvi(keyword, ano)
    if df.empty: return df
    if 'Subjetividade Complementar' in df.columns:
        df = df[~df['Subjetividade Complementar'].astype(str).str.contains('Resistência', case=False, na=False)]
    return df

@st.cache_data
def load_data_tco(keyword, ano):
    file_path = find_file(keyword, ano)
    if not file_path: return pd.DataFrame()
    try:
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
            if "OLHO D" in addr_clean and "CASADO" in addr_clean:
                return "Olho d Água do Casado"
            if "AGUA BRANCA" in addr_clean:
                return "Água Branca"
            return None

        # TCO Requires "calamine" engine to bypass WB Corruption
        df = pd.read_excel(file_path, engine='calamine')
        df = df.dropna(subset=['Nº Ocorrência', 'Endereço'])
        
        # Extrair Data usando Regex (dd/mm/yyyy)
        df['Data Extracao'] = df['Nº Ocorrência'].astype(str).str.extract(r'(\d{2}/\d{2}/\d{4})')
        df = df.dropna(subset=['Data Extracao'])
        df['Data'] = pd.to_datetime(df['Data Extracao'], format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=['Data'])
        df = df[df['Data'].dt.year == ano]
        
        df['Cidade'] = df['Endereço'].apply(extract_city)
        df = df.dropna(subset=['Cidade'])
        
        meses_pt = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
                    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        df['Mês'] = df['Data'].dt.month.map(meses_pt)
        df['Mes_Num'] = df['Data'].dt.month
        return df
    except Exception as e:
        st.error(f"Erro ao ler TCO: {e}")
        return pd.DataFrame()

@st.cache_data
def load_data_veiculos(keyword, ano):
    file_path = find_file(keyword, ano)
    if not file_path: return pd.DataFrame()
    # Idêntico ao TCO (Mesma corrupção calamine e mesma complexidade de regex)
    try:
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
            if "OLHO D" in addr_clean and "CASADO" in addr_clean:
                return "Olho d Água do Casado"
            if "AGUA BRANCA" in addr_clean:
                return "Água Branca"
            return None

        # O novo formato de 'Veículos Recuperados' usa rotas dedicadas no CAD, mudando o padrão. 
        # Coluna G (índice 6) = Data da Ocorrência
        # Coluna O (índice 14) = Cidade
        df = pd.read_excel(file_path, engine='calamine', header=None)
        
        # Garantir que descartaremos cabeçalhos
        df = df.dropna(subset=[6, 14]) 
        
        # Converter para datetime (o Excel original já exporta como Date no formato novo)
        df['Data'] = pd.to_datetime(df[6], errors='coerce')
        df = df.dropna(subset=['Data'])
        df = df[df['Data'].dt.year == ano]
        
        # Extrair cidade
        df['Cidade'] = df[14].apply(extract_city)
        df = df.dropna(subset=['Cidade'])
        
        meses_pt = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
                    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        df['Mês'] = df['Data'].dt.month.map(meses_pt)
        df['Mes_Num'] = df['Data'].dt.month
        return df
    except Exception as e:
        st.error(f"Erro ao ler Veículos: {e}")
        return pd.DataFrame()

@st.cache_data
def load_data_maria_da_penha(keyword, ano):
    file_path = find_file(keyword, ano)
    if not file_path: return pd.DataFrame()
    try:
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
            if "OLHO D" in addr_clean and "CASADO" in addr_clean:
                return "Olho d Água do Casado"
            return None

        # Maria da Penha via calamine
        df = pd.read_excel(file_path, engine='calamine')
        df = df.dropna(subset=['Nº Ocorrência', 'Endereço'])
        
        # Extrair Data usando Regex (dd/mm/yyyy) da coluna Nº Ocorrência
        df['Data Extracao'] = df['Nº Ocorrência'].astype(str).str.extract(r'(\d{2}/\d{2}/\d{4})')
        df = df.dropna(subset=['Data Extracao'])
        df['Data'] = pd.to_datetime(df['Data Extracao'], format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=['Data'])
        df = df[df['Data'].dt.year == ano]
        
        df['Cidade'] = df['Endereço'].apply(extract_city)
        df = df.dropna(subset=['Cidade'])
        
        meses_pt = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
                    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        df['Mês'] = df['Data'].dt.month.map(meses_pt)
        df['Mes_Num'] = df['Data'].dt.month
        return df
    except Exception as e:
        st.error(f"Erro ao ler Maria da Penha: {e}")
        return pd.DataFrame()


@st.cache_data
def load_data_mandados(keyword, ano):
    file_path = find_file(keyword, ano)
    if not file_path: return pd.DataFrame()
    # Usa logicamente a mesma extração estrutural de TCO
    try:
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

        df_raw = pd.read_excel(file_path, engine='calamine')
        
        data = []
        date_pattern = re.compile(r'(\d{2}/\d{2}/\d{4})')
        
        for _, row in df_raw.iterrows():
            row_text = " ".join([str(x) for x in row.values if pd.notna(x)])
            if 'Gerado em:' in row_text or 'Pág:' in row_text:
                continue
            date_match = date_pattern.search(row_text)
            if date_match:
                data_fato = date_match.group(1)
                cidade = extract_city_from_text(row_text)
                if cidade:
                    data.append({'Data Extracao': data_fato, 'Cidade': cidade})
                    
        df = pd.DataFrame(data)
        if df.empty: return df
        
        df['Data'] = pd.to_datetime(df['Data Extracao'], format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=['Data'])
        df = df[df['Data'].dt.year == ano]
        
        meses_pt = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
                    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        df['Mês'] = df['Data'].dt.month.map(meses_pt)
        df['Mes_Num'] = df['Data'].dt.month
        return df
    except Exception as e:
        st.error(f"Erro ao ler Mandados: {e}")
        return pd.DataFrame()

@st.cache_data
def load_data_visita(keyword, ano):
    file_path = find_file(keyword, ano)
    if not file_path: return pd.DataFrame()
    # Usa logicamente a mesma extração estrutural de TCO
    try:
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

        df_raw = pd.read_excel(file_path, engine='calamine')
        
        data = []
        date_pattern = re.compile(r'(\d{2}/\d{2}/\d{4})')
        
        for _, row in df_raw.iterrows():
            row_text = " ".join([str(x) for x in row.values if pd.notna(x)])
            if 'Gerado em:' in row_text or 'Pág:' in row_text:
                continue
            date_match = date_pattern.search(row_text)
            if date_match:
                data_fato = date_match.group(1)
                cidade = extract_city_from_text(row_text)
                if cidade:
                    data.append({'Data Extracao': data_fato, 'Cidade': cidade})
                    
        df = pd.DataFrame(data)
        if df.empty: return df
        
        df['Data'] = pd.to_datetime(df['Data Extracao'], format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=['Data'])
        df = df[df['Data'].dt.year == ano]
        
        meses_pt = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
                    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        df['Mês'] = df['Data'].dt.month.map(meses_pt)
        df['Mes_Num'] = df['Data'].dt.month
        return df
    except Exception as e:
        st.error(f"Erro ao ler Visitas: {e}")
        return pd.DataFrame()

@st.cache_data
def load_data_armas(keyword, ano):
    file_path = find_file(keyword, ano)
    if not file_path: return pd.DataFrame()
    try:
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

        def clean_armas_city(addr):
            if pd.isna(addr): return None
            c = remove_accents(str(addr).upper())
            for norm_c, orig_c in norm_cities.items():
                if norm_c in c:
                    return orig_c
            if "OLHO D" in c and "CASAD" in c: return "Olho d Água do Casado"
            if "AGUA BRANCA" in c: return "Água Branca"
            if "DELMIRO" in c: return "Delmiro Gouveia"
            if "MATA GRANDE" in c: return "Mata Grande"
            if "INHAPI" in c: return "Inhapi"
            if "CANAPI" in c: return "Canapi"
            if "PIRANHAS" in c: return "Piranhas"
            if "PARICONHA" in c: return "Pariconha"
            return None

        # O novo arquivo vem corrompido, necessitando de Calamine, mas tem headers limpos.
        df = pd.read_excel(file_path, engine='calamine')
        
        # Filtra ocorrências sem data
        df = df.dropna(subset=['Data da Ocorrência'])
        
        # Extrair Data (Pode vir no formato DD/MM/YYYY HH:MM:SS)
        df['Data Extracao'] = df['Data da Ocorrência'].astype(str).str.extract(r'(\d{2}/\d{2}/\d{4})')
        df = df.dropna(subset=['Data Extracao'])
        df['Data'] = pd.to_datetime(df['Data Extracao'], format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=['Data'])
        df = df[df['Data'].dt.year == ano]
        
        df['Cidade'] = df['Cidade'].apply(clean_armas_city)
        df = df.dropna(subset=['Cidade'])
        df = df[df['Cidade'].isin(cidades_9bpm)]
        
        meses_pt = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
                    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        df['Mês'] = df['Data'].dt.month.map(meses_pt)
        df['Mes_Num'] = df['Data'].dt.month
        
        # Manter compatibilização de nome de coluna se necessário
        if 'Tipo' in df.columns:
            df['Tipo Arma'] = df['Tipo'].fillna('Desconhecido')
            
        return df
    except Exception as e:
        st.error(f"Erro ao ler Armas: {e}")
        return pd.DataFrame()

@st.cache_data
def load_data_prisoes(keyword, ano):
    file_path = find_file(keyword, ano)
    if not file_path: return pd.DataFrame()
    try:
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

        def clean_city(addr):
            if pd.isna(addr): return None
            c = remove_accents(str(addr).upper())
            for norm_c, orig_c in norm_cities.items():
                if norm_c in c:
                    return orig_c
            if "OLHO D" in c and "CASAD" in c: return "Olho d Água do Casado"
            if "AGUA BRANCA" in c: return "Água Branca"
            if "DELMIRO" in c: return "Delmiro Gouveia"
            if "MATA GRANDE" in c: return "Mata Grande"
            if "INHAPI" in c: return "Inhapi"
            if "CANAPI" in c: return "Canapi"
            if "PIRANHAS" in c: return "Piranhas"
            if "PARICONHA" in c: return "Pariconha"
            return None

        # Como os dados estao espalhados verticalmente, lemos raw para aplicar forward fill 
        df = pd.read_excel(file_path, header=None)
        
        # 1. Forward fill data do fato
        df[0] = df[0].ffill()
        
        # 2. Extract Data
        df['Data Extracao'] = df[0].astype(str).str.extract(r'(\d{2}/\d{2}/\d{4})')
        df = df.dropna(subset=['Data Extracao'])
        df['Data'] = pd.to_datetime(df['Data Extracao'], format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=['Data'])
        df = df[df['Data'].dt.year == ano]
        
        # 3. Cidade is at index 11
        df['Cidade'] = df[11].apply(clean_city)
        df = df.dropna(subset=['Cidade'])
        df = df[df['Cidade'].isin(cidades_9bpm)]
        
        meses_pt = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
                    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        df['Mês'] = df['Data'].dt.month.map(meses_pt)
        df['Mes_Num'] = df['Data'].dt.month
        
        return df
    except Exception as e:
        st.error(f"Erro ao ler Prisões: {e}")
        return pd.DataFrame()

@st.cache_data
def load_data_drogas(keyword, ano):
    file_path = find_file(keyword, ano)
    if not file_path: return pd.DataFrame()
    try:
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

        def clean_city(addr):
            if pd.isna(addr): return None
            c = remove_accents(str(addr).upper())
            for norm_c, orig_c in norm_cities.items():
                if norm_c in c:
                    return orig_c
            if "OLHO D" in c and "CASAD" in c: return "Olho d Água do Casado"
            if "AGUA BRANCA" in c: return "Água Branca"
            if "DELMIRO" in c: return "Delmiro Gouveia"
            if "MATA GRANDE" in c: return "Mata Grande"
            if "INHAPI" in c: return "Inhapi"
            if "CANAPI" in c: return "Canapi"
            if "PIRANHAS" in c: return "Piranhas"
            if "PARICONHA" in c: return "Pariconha"
            return None

        df = pd.read_excel(file_path, engine='calamine')
        
        # Filtra ocorrências sem data
        df = df.dropna(subset=['Data da Ocorrência'])
        
        # Extrair Data e filtrar ano
        df['Data Extracao'] = df['Data da Ocorrência'].astype(str).str.extract(r'(\d{2}/\d{2}/\d{4})')
        df = df.dropna(subset=['Data Extracao'])
        df['Data'] = pd.to_datetime(df['Data Extracao'], format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=['Data'])
        df = df[df['Data'].dt.year == ano]
        
        # Filtrar Cidades
        df['Cidade'] = df['Cidade'].apply(clean_city)
        df = df.dropna(subset=['Cidade'])
        df = df[df['Cidade'].isin(cidades_9bpm)]
        
        # Converter Quantidade para numérico (Gramas)
        df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0.0)
        
        # Padronizar Tipos
        if 'Tipo' in df.columns:
            df['Tipo Droga'] = df['Tipo'].astype(str).str.upper().str.strip()
        else:
            df['Tipo Droga'] = 'DESCONHECIDO'
            
        meses_pt = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
                    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        df['Mês'] = df['Data'].dt.month.map(meses_pt)
        df['Mes_Num'] = df['Data'].dt.month
        
        return df
    except Exception as e:
        st.error(f"Erro ao ler Drogas: {e}")
        return pd.DataFrame()


@st.cache_data
def load_data_cvp(keyword, ano):
    file_path = find_file(keyword, ano)
    if not file_path: return pd.DataFrame()
    try:
        df_raw = pd.read_excel(file_path, header=None)
        data = []
        for i, row in df_raw.iterrows():
            clean_row = [x for x in row.dropna().tolist()]
            # Linhas válidas de CVP possuem a Natureza + 12 Meses + Total + Incidência (15 colunas não-nulas)
            if len(clean_row) >= 14 and str(clean_row[0]).strip().upper() != 'NATUREZA':
                data.append(clean_row[:14])
                
        # Montar dataframe limpo
        colunas = ['NATUREZA', 'JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ', 'TOTAL']
        df = pd.DataFrame(data, columns=colunas)
        
        # Remover a linha que engloba o TOTAL GERAL e as que possam ser apenas índices
        df = df[~df['NATUREZA'].astype(str).str.contains('TOTAL|^\\d+$', regex=True, case=False)]
        
        # Converter meses e totais para float e depois inteiro
        for c in colunas[1:]:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
            
        return df
    except Exception as e:
        st.error(f"Erro ao ler CVP: {e}")
        return pd.DataFrame()

# ----------------- RENDERING MODULES -----------------

# Escala de cores: verde (baixo) -> amarelo (medio) -> vermelho (alto)
ESCALA_GRADIENTE = ['#DCFCE7', '#BBF7D0', '#86EFAC', '#FDE68A', '#FCA5A5', '#F87171']

def _apply_table_style(df, highlight_row=None):
    """Aplica estilo institucional (PDF-like) ao dataframe: cabeçalho azul PMAL, zebra striping, TOTAL GERAL destacado."""
    import pandas as pd

    def style_cell(val):
        try:
            if pd.isna(val):
                return "color: #94A3B8;"
        except (ValueError, TypeError):
            pass
        if isinstance(val, (int, float)):
            if val > 0:
                return "background-color: #F8FAFC; color: #1E293B; font-weight: 500;"
            else:
                return "color: #94A3B8;"
        return "font-weight: 600; color: #1E293B;"

    styler = df.style.map(style_cell)

    if highlight_row is not None:
        try:
            styler = styler.apply(
                lambda s: ['background-color: #0D3878; color: #FFFFFF; font-weight: 700;'] * len(s)
                if s.name == highlight_row else [''] * len(s),
                axis=1
            )
        except Exception:
            pass
    return styler


def _render_bar_chart(df, y_col, x_col, title=""):
    """Renderiza grafico de barras horizontal com escala verde (baixo) -> vermelho (alto)."""
    fig = px.bar(
        df, y=y_col, x=x_col, orientation='h',
        color=x_col, color_continuous_scale=ESCALA_GRADIENTE, text=x_col
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(
        plot_bgcolor='rgba(255,255,255,1)',
        paper_bgcolor='rgba(255,255,255,1)',
        font_color='#1E293B',
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_title="", yaxis_title="",
        coloraxis_showscale=False
    )
    return fig

def render_mvi_module(data, title, ano):
    st.markdown(f"<h2 style='text-align: center; color: #0D3878 !important; margin-bottom: 2rem;'>{title}</h2>", unsafe_allow_html=True)
    if data.empty:
        st.warning("Nenhum dado encontrado.")
        return

    total_mvi = len(data)
    cidade_critica = data['Cidade'].value_counts().index[0] if not data.empty else "N/A"
    mvi_cidade_critica = data['Cidade'].value_counts().iloc[0] if not data.empty else 0
    mes_critico = data['Mês'].value_counts().index[0] if not data.empty else "N/A"
    mvi_mes_critico = data['Mês'].value_counts().iloc[0] if not data.empty else 0

    col1, col2, col3 = st.columns(3)
    with col1: st.metric(f"Total de {title}", f"{total_mvi}")
    with col2: st.metric("Cidade mais Afetada", f"{cidade_critica}", f"{mvi_cidade_critica} casos", delta_color="inverse")
    with col3: st.metric("Mês mais Crítico", f"{mes_critico}", f"{mvi_mes_critico} casos", delta_color="inverse")

    st.markdown("<br><hr style='border-color: #E2E8F0;'><br>", unsafe_allow_html=True)

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown(f"<h3>Total por Cidade</h3>", unsafe_allow_html=True)
        mvi_por_cidade = data['Cidade'].value_counts().reset_index()
        mvi_por_cidade.columns = ['Cidade', 'Quantidade']
        mvi_por_cidade = mvi_por_cidade.sort_values(by='Quantidade', ascending=True)

        fig1 = _render_bar_chart(mvi_por_cidade, 'Cidade', 'Quantidade')
        st.plotly_chart(fig1, use_container_width=True)

    with col_chart2:
        st.markdown("<h3>Evolução Mensal</h3>", unsafe_allow_html=True)
        mvi_por_mes = data.groupby(['Mes_Num', 'Mês']).size().reset_index(name='Quantidade')
        mvi_por_mes = mvi_por_mes.sort_values(by='Mes_Num')

        fig2 = px.line(mvi_por_mes, x='Mês', y='Quantidade', markers=True, line_shape='spline')
        fig2.update_traces(line=dict(color='#0D3878', width=4), marker=dict(size=10, color='#0D3878'))
        fig2.update_layout(plot_bgcolor='rgba(255,255,255,1)', paper_bgcolor='rgba(255,255,255,1)', font_color='#1E293B', margin=dict(l=0, r=0, t=30, b=0), xaxis_title="", yaxis_title="Ocorrências", yaxis=dict(gridcolor='#E2E8F0'))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<br><hr style='border-color: #E2E8F0;'><br>", unsafe_allow_html=True)

    st.markdown("<h3>Matriz de Ocorrências (Cidade x Mês)</h3>", unsafe_allow_html=True)
    resumo = data.groupby(['Cidade', 'Mês', 'Mes_Num']).size().reset_index(name='Quantidade')
    pivot = resumo.pivot(index='Cidade', columns='Mês', values='Quantidade').fillna(0).astype(int)

    meses_pt = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
                7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
    for mes_num, mes_nome in meses_pt.items():
        if mes_nome not in pivot.columns:
            pivot[mes_nome] = 0

    cols_presentes = list(meses_pt.values())
    pivot = pivot[cols_presentes]
    pivot['TOTAL'] = pivot.sum(axis=1)
    pivot.loc['TOTAL GERAL'] = pivot.sum()

    st.dataframe(
        _apply_table_style(pivot, highlight_row='TOTAL GERAL'),
        use_container_width=True
    )
    
    st.markdown("<br><hr style='border-color: #E2E8F0;'><br>", unsafe_allow_html=True)
    
    # --- Botões de Exportação Separados ---
    st.markdown("<h3>📥 Exportar Relatório</h3>", unsafe_allow_html=True)
    
    df_export = pivot.reset_index()
    excel_data = convert_df_to_excel(df_export)
    
    # Preparar dicionário de gráficos para o PDF
    charts_dict = {
        "Distribuição Geográfica (Cidade)": fig1,
        "Evolução Temporal (Mensal)": fig2
    }
    pdf_data = convert_df_to_pdf(df_export, title, figs=charts_dict)
    
    col_btn1, col_btn2, _ = st.columns([1, 1, 2])
    with col_btn1:
        st.download_button(
            label=f"📥 Exportar Excel",
            data=excel_data,
            file_name=f"{title.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"btn_ex_mvi_{title}_{ano}"
        )
    with col_btn2:
        st.download_button(
            label=f"🖨️ Exportar PDF",
            data=pdf_data,
            file_name=f"{title.replace(' ', '_')}.pdf",
            mime="application/pdf",
            key=f"btn_pdf_mvi_{title}_{ano}"
        )

def render_analitico_mvi(data, title, ano):
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 25px;">
        <h2 style="color: #0D3878 !important; margin-bottom: 5px;">{title}</h2>
        <p style="color: #64748B; font-size: 1.1rem;">Análise detalhada de ocorrências e perfil das vítimas - <strong>{ano}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    if data.empty:
        st.warning("Nenhum dado encontrado para análise analítica.")
        return

    # Filtros de Refino na própria página
    with st.expander("🔍 Filtros de Pesquisa Avançada", expanded=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            meses_disp = sorted(data['Mês'].unique().tolist(), key=lambda x: MESES_LIST.index(x))
            meses_sel = st.multiselect("Filtrar por Meses", options=meses_disp, default=meses_disp)
        with c2:
            bairros_disp = sorted(data['Bairro'].dropna().unique().tolist())
            bairros_sel = st.multiselect("Filtrar por Bairros", options=bairros_disp, default=bairros_disp)
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Resetar Filtros", use_container_width=True):
                st.rerun()

    # Aplicação dos Filtros
    df_filtrado = data[data['Mês'].isin(meses_sel) & data['Bairro'].isin(bairros_sel)].copy()

    # KPI Rápido
    st.markdown("---")
    res_c1, res_c2, res_c3, res_c4 = st.columns(4)
    res_c1.metric("Ocorrências Filtradas", len(df_filtrado))
    res_c2.metric("Bairros Distintos", df_filtrado['Bairro'].nunique())
    
    # Idade média
    try:
        idade_media = pd.to_numeric(df_filtrado['Idade'], errors='coerce').mean()
        res_c3.metric("Idade Média", f"{idade_media:.1f}" if pd.notna(idade_media) else "N/A")
    except:
        res_c3.metric("Idade Média", "N/A")
        
    # Perfil Principal (Tipo de Morte ou Instrumento para Tentativa)
    natureza_col = 'Tipo de Morte' if 'Tipo de Morte' in df_filtrado.columns else ('Instrumento' if 'Instrumento' in df_filtrado.columns else 'Natureza')
    res_c4.metric("Natureza Principal", df_filtrado[natureza_col].mode()[0] if not df_filtrado.empty and natureza_col in df_filtrado.columns else "N/A")

    # Gráficos Analíticos
    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2 = st.columns([3, 2])
    
    with g1:
        st.markdown("### 📍 Ocorrências por Localidade (Bairro)")
        counts_bairro = df_filtrado['Bairro'].value_counts().reset_index()
        counts_bairro.columns = ['Bairro', 'Total']
        fig_bairro = px.bar(counts_bairro, x='Total', y='Bairro', orientation='h', 
                           color='Total', color_continuous_scale=ESCALA_GRADIENTE, text='Total')
        fig_bairro.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor='white', coloraxis_showscale=False)
        st.plotly_chart(fig_bairro, use_container_width=True)

    with g2:
        st.markdown(f"### 🏷️ Perfil: {natureza_col}")
        counts_tipo = df_filtrado[natureza_col].value_counts().reset_index()
        counts_tipo.columns = ['Tipo', 'Total']
        fig_tipo = px.pie(counts_tipo, values='Total', names='Tipo', hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_tipo.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_tipo, use_container_width=True)

    # Tabela Analítica de Dados
    st.markdown("### 📋 Listagem Nominal de Ocorrências")
    
    # Seleção das colunas para exibição na tabela analítica
    cols_analiticas = [
        'Data do Fato', 'Nº BOU', 'Nome', 'Idade', 'Bairro', 
        'Cidade', 'Subjetividade Complementar', natureza_col
    ]
    
    # Filtra colunas que realmente existem no DF
    cols_show = [c for c in cols_analiticas if c in df_filtrado.columns]
    
    df_tabela = df_filtrado[cols_show].copy()
    df_tabela = df_tabela.rename(columns={
        'Nome': 'Nome da Vítima',
        'Bairro': 'Local (Bairro)',
        natureza_col: 'Natureza'
    })

    st.dataframe(
        df_tabela.style.map(lambda x: "font-weight: bold; color: #0D3878;" if isinstance(x, str) and "/" in x else ""),
        use_container_width=True, hide_index=True
    )

    # --- Área de Exportação Estabilizada ---
    with st.expander(f"📥 Preparar Relatório Analítico ({title})", expanded=False):
        st.info("Gerando análise gráfica... Por favor, aguarde.")
        pdf_title = f"{title} - {ano}"
        
        # Preparar dicionário de gráficos para o PDF Analítico
        charts_dict = {
            "Distribuição por Localidade (Bairro)": fig_bairro,
            f"Perfil Geral Operacional ({natureza_col})": fig_tipo
        }
        pdf_analitico_data = convert_df_to_pdf(df_tabela, pdf_title, figs=charts_dict)
        
        st.download_button(
            label=f"🖨️ Baixar Relatório em PDF",
            data=pdf_analitico_data,
            file_name=f"{title.replace(' ', '_')}_{ano}.pdf",
            mime="application/pdf",
            key=f"btn_pdf_analitico_v2_{title.replace(' ', '_')}"
        )

def render_drogas_module(data):
    st.markdown("        <h2 style='text-align: center; color: #0D3878 !important; margin-bottom: 2rem;'>Estatísticas de Drogas Apreendidas (Gramas)</h2>", unsafe_allow_html=True)
    if data.empty:
        st.warning("Nenhum dado encontrado para Drogas.")
        return

    # Normalizar palavras-chave de drogas para os filtros
    data['Cat_Droga'] = 'Outros'
    data.loc[data['Tipo Droga'].str.contains('COCA'), 'Cat_Droga'] = 'Cocaína'
    data.loc[data['Tipo Droga'].str.contains('MACONHA'), 'Cat_Droga'] = 'Maconha'
    data.loc[data['Tipo Droga'].str.contains('CRACK'), 'Cat_Droga'] = 'Crack'

    tot_cocaina = data[data['Cat_Droga'] == 'Cocaína']['Quantidade'].sum()
    tot_maconha = data[data['Cat_Droga'] == 'Maconha']['Quantidade'].sum()
    tot_crack = data[data['Cat_Droga'] == 'Crack']['Quantidade'].sum()

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Maconha (Gramas)", f"{tot_maconha:,.0f}g")
    with col2: st.metric("Cocaína (Gramas)", f"{tot_cocaina:,.0f}g")
    with col3: st.metric("Crack (Gramas)", f"{tot_crack:,.0f}g")

    st.markdown("<br><hr style='border-color: #E2E8F0;'><br>", unsafe_allow_html=True)

    drogas_alvo = ['Maconha', 'Cocaína', 'Crack']
    cores = {'Maconha': '#3fb950', 'Cocaína': '#f0f6fc', 'Crack': '#d29922'}

    for droga in drogas_alvo:
        st.markdown(f"<h3>Matriz de Ocorrências: {droga} (g)</h3>", unsafe_allow_html=True)
        df_droga = data[data['Cat_Droga'] == droga]
        
        if df_droga.empty:
            st.info(f"Sem registros de {droga} para 2025.")
            continue
            
        resumo = df_droga.groupby(['Cidade', 'Mês', 'Mes_Num'])['Quantidade'].sum().reset_index()
        pivot = resumo.pivot(index='Cidade', columns='Mês', values='Quantidade').fillna(0).round(1)

        meses_pt = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
                    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        for mes_num, mes_nome in meses_pt.items():
            if mes_nome not in pivot.columns:
                pivot[mes_nome] = 0.0

        cols_presentes = list(meses_pt.values())
        pivot = pivot[cols_presentes]
        pivot['TOTAL'] = pivot.sum(axis=1)
        pivot.loc['TOTAL GERAL'] = pivot.sum()

        cor_hex = cores[droga]
        st.dataframe(
            _apply_table_style(pivot, highlight_row='TOTAL GERAL')
             .format("{:,.0f}"),
            use_container_width=True
        )
        
        # Export Buttons
        df_export = pivot.reset_index()
        excel_data = convert_df_to_excel(df_export)
        pdf_data = convert_df_to_pdf(df_export, f"Resultados Drogas - {droga}")
        
        col_btn1, col_btn2, _ = st.columns([1, 1, 2])
        with col_btn1:
            st.download_button(
                label=f"📥 Exportar {droga} (Excel)",
                data=excel_data,
                file_name=f"Drogas_{droga}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"btn_ex_droga_{droga}"
            )
        with col_btn2:
            st.download_button(
                label=f"🖨️ Exportar {droga} (PDF)",
                data=pdf_data,
                file_name=f"Drogas_{droga}.pdf",
                mime="application/pdf",
                key=f"btn_pdf_droga_{droga}"
            )
        st.markdown("<br>", unsafe_allow_html=True)

def render_cvp_module(data, ano):
    st.markdown("<h2 style='text-align: center; color: #f0883e !important; margin-bottom: 2rem;'>CVP Geral (Crimes Contra o Patrimônio)</h2>", unsafe_allow_html=True)
    if data.empty:
        st.warning("Nenhum dado encontrado para CVP.")
        return

    total_cvp = int(data['TOTAL'].sum())
    
    # Encontrar a natureza que mais ocorreu
    natureza_critica = data.loc[data['TOTAL'].idxmax()]['NATUREZA']
    qtd_natureza_critica = int(data['TOTAL'].max())
    
    # Encontrar mês crítico global
    meses_cols = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    totais_por_mes = data[meses_cols].sum()
    mes_critico = totais_por_mes.idxmax()
    qtd_mes_critico = int(totais_por_mes.max())

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total de CVP", f"{total_cvp}")
    with col2: st.metric("Natureza mais Frequente", f"{natureza_critica}", f"{qtd_natureza_critica} casos", delta_color="inverse")
    with col3: st.metric("Mês mais Crítico", f"{mes_critico}", f"{qtd_mes_critico} casos", delta_color="inverse")
    
    st.markdown("<br><hr style='border-color: #E2E8F0;'><br>", unsafe_allow_html=True)

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown(f"<h3>Ocorrências por Natureza</h3>", unsafe_allow_html=True)
        df_natureza = data[['NATUREZA', 'TOTAL']].sort_values(by='TOTAL', ascending=True)
        fig1 = _render_bar_chart(df_natureza, 'NATUREZA', 'TOTAL')
        st.plotly_chart(fig1, use_container_width=True)

    with col_chart2:
        st.markdown("<h3>Evolução Mensal Macro</h3>", unsafe_allow_html=True)
        df_meses = pd.DataFrame({'Mês': meses_cols, 'Quantidade': totais_por_mes.values})
        fig2 = px.line(df_meses, x='Mês', y='Quantidade', markers=True, line_shape='spline')
        fig2.update_traces(line=dict(color='#F59E0B', width=4), marker=dict(size=10, color='#F59E0B'))
        fig2.update_layout(plot_bgcolor='rgba(255,255,255,1)', paper_bgcolor='rgba(255,255,255,1)', font_color='#1E293B', margin=dict(l=0, r=0, t=30, b=0), xaxis_title="", yaxis_title="Ocorrências totais", yaxis=dict(gridcolor='#E2E8F0'))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<br><hr style='border-color: #E2E8F0;'><br>", unsafe_allow_html=True)
    st.markdown("<h3>Matriz de CVP por Natureza</h3>", unsafe_allow_html=True)
    
    # Adicionar TOTAL GERAL na matriz
    df_exibicao = data.copy()
    colunas_numericas = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ', 'TOTAL']
    total_row = df_exibicao[colunas_numericas].sum()
    total_row['NATUREZA'] = 'TOTAL GERAL'
    df_exibicao = pd.concat([df_exibicao, pd.DataFrame([total_row])], ignore_index=True)
    
    last_idx = len(df_exibicao) - 1

    st.dataframe(
        _apply_table_style(df_exibicao, highlight_row=last_idx),
        use_container_width=True, hide_index=True
    )

    # --- Área de Exportação Estabilizada ---
    with st.expander("📥 Preparar Relatório CVP (PDF/Excel)", expanded=False):
        st.info("O processamento analítico com gráficos pode levar alguns segundos.")
        df_export = df_exibicao
        excel_data = convert_df_to_excel(df_export)
        
        # Preparar dicionário de gráficos para o PDF CVP
        charts_dict = {
            "Ocorrências por Natureza (CVP)": fig1,
            "Evolução Mensal Macro (CVP)": fig2
        }
        pdf_cvp_data = convert_df_to_pdf(df_export, "Resultados CVP", figs=charts_dict)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.download_button(
                label=f"📥 Exportar Excel",
                data=excel_data,
                file_name=f"Resultados_CVP.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"btn_ex_cvp_{ano_selecionado}"
            )
        with col_btn2:
            st.download_button(
                label=f"🖨️ Exportar PDF",
                data=pdf_cvp_data,
                file_name=f"Resultados_CVP.pdf",
                mime="application/pdf",
                key=f"btn_pdf_cvp_{ano_selecionado}"
            )


def get_consolidado_data(ano, cidade_sel="Todas"):
    meses_ordem = MESES_LIST
    dados_consolidados = []
    
    def get_monthly_counts(df, row_name, is_sum=False):
        counts = {m: 0 for m in meses_ordem}
        df_f = df.copy()
        
        # Filtro de Cidade (Caso indicador tenha coluna de cidade)
        if cidade_sel != "Todas" and 'Cidade' in df_f.columns:
            df_f = df_f[df_f['Cidade'] == cidade_sel]
        elif cidade_sel != "Todas":
            # No caso do CVP, se pedir cidade específica, retorna vazio/zero
            return {**counts, 'Indicador': row_name}

        if not df_f.empty and 'Mês' in df_f.columns:
            if is_sum: # Para drogas (soma gramas)
                agg = df_f.groupby('Mês')['Quantidade'].sum().to_dict()
            else: # Para contagem de ocorrências
                agg = df_f['Mês'].value_counts().to_dict()
            
            for m, total in agg.items():
                if m in counts:
                    counts[m] = float(total) if is_sum else int(total)
                    
        counts['Indicador'] = row_name
        return counts

    df_mvi = load_data_mvi('MVI', ano)
    dados_consolidados.append(get_monthly_counts(df_mvi, 'MVI'))
    
    df_cvli = load_data_cvli('MVI', ano)
    dados_consolidados.append(get_monthly_counts(df_cvli, 'CVLI (Homicídios)'))
    
    df_tentativa = load_data_mvi('Tentativa', ano)
    dados_consolidados.append(get_monthly_counts(df_tentativa, 'Tentativa de MVI'))
    
    df_tco = load_data_tco('TCO', ano)
    dados_consolidados.append(get_monthly_counts(df_tco, 'TCO'))
    
    df_mandados = load_data_mandados('Mandado', ano)
    dados_consolidados.append(get_monthly_counts(df_mandados, 'Cumprimento de Mandados'))
    
    df_visita = load_data_visita('Visita Comun', ano)
    dados_consolidados.append(get_monthly_counts(df_visita, 'Visita Comunitária'))
    
    df_veiculos = load_data_veiculos('Recuperado', ano)
    dados_consolidados.append(get_monthly_counts(df_veiculos, 'Veículos Recuperados'))
    
    df_armas = load_data_armas('Armas', ano)
    dados_consolidados.append(get_monthly_counts(df_armas, 'Armas Apreendidas'))
    
    df_prisoes = load_data_prisoes('Pris', ano)
    dados_consolidados.append(get_monthly_counts(df_prisoes, 'Prisões'))
    
    df_mariap = load_data_maria_da_penha('Maria da Penha', ano)
    dados_consolidados.append(get_monthly_counts(df_mariap, 'Maria da Penha'))
    
    # Drogas Filtradas por Categorie (Maconha, Cocaina, Crack)
    df_drogas = load_data_drogas('Drogas', ano)
    if not df_drogas.empty:
        if cidade_sel != "Todas":
            df_drogas = df_drogas[df_drogas['Cidade'] == cidade_sel]
            
        df_drogas['Cat_Droga'] = 'Outros'
        df_drogas.loc[df_drogas['Tipo Droga'].str.contains('COCA'), 'Cat_Droga'] = 'Cocaína'
        df_drogas.loc[df_drogas['Tipo Droga'].str.contains('MACONHA'), 'Cat_Droga'] = 'Maconha'
        df_drogas.loc[df_drogas['Tipo Droga'].str.contains('CRACK'), 'Cat_Droga'] = 'Crack'
        for droga in ['Maconha', 'Cocaína', 'Crack']:
            df_droga_f = df_drogas[df_drogas['Cat_Droga'] == droga]
            dados_consolidados.append(get_monthly_counts(df_droga_f, f'Drogas Apreendidas - {droga} (g)', is_sum=True))
    else:
        for droga in ['Maconha', 'Cocaína', 'Crack']:
            dados_consolidados.append({**{m: 0.0 for m in meses_ordem}, 'Indicador': f'Drogas Apreendidas - {droga} (g)'})
            
    # CVP Geral (BPM Global)
    df_cvp = load_data_cvp('CVP', ano)
    if cidade_sel == "Todas":
        cvp_counts = {m: 0 for m in meses_ordem}
        cvp_counts['Indicador'] = 'CVP Geral'
        if not df_cvp.empty:
            mapa_cvp = {
                'JAN': 'Janeiro', 'FEV': 'Fevereiro', 'MAR': 'Março', 'ABR': 'Abril', 
                'MAI': 'Maio', 'JUN': 'Junho', 'JUL': 'Julho', 'AGO': 'Agosto', 
                'SET': 'Setembro', 'OUT': 'Outubro', 'NOV': 'Novembro', 'DEZ': 'Dezembro'
            }
            for col, mes in mapa_cvp.items():
                if col in df_cvp.columns:
                    cvp_counts[mes] = int(df_cvp[col].sum())
        dados_consolidados.append(cvp_counts)
    else:
        # CVP não possui dados por cidade no momento
        dados_consolidados.append({**{m: 0 for m in meses_ordem}, 'Indicador': 'CVP Geral (BPM Global)'})
    
    df_final = pd.DataFrame(dados_consolidados)
    cols_display = ['Indicador'] + meses_ordem
    df_final = df_final[[c for c in cols_display if c in df_final.columns]].copy()
    df_final = df_final.fillna(0)
    
    return df_final, meses_ordem

def render_consolidado_module(ano_selecionado):
    # Inicialização de Estado da Aba
    if "cons_view" not in st.session_state:
        st.session_state.cons_view = "Anual"

    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 5px;">
        <h2 style="color: #0D3878 !important; margin-bottom: 0px;">📑 Relatório Consolidado</h2>
        <p style="color: #64748B; font-size: 1rem; margin: 0;">Visão mensal de todos os indicadores - <strong>{ano_selecionado}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sub-Navegação
    c1, c2 = st.columns(2)
    with c1:
        ativo = st.session_state.cons_view == "Anual"
        label = f"{'✓ ' if ativo else ''}Relatório Anual"
        if st.button(label, icon=":material/calendar_month:", key="btn_cons_anual", use_container_width=True):
            st.session_state.cons_view = "Anual"
            st.rerun()
    with c2:
        ativo = st.session_state.cons_view == "Mensal"
        label = f"{'✓ ' if ativo else ''}Análise Mensal / Cidade"
        if st.button(label, icon=":material/location_city:", key="btn_cons_mensal", use_container_width=True):
            st.session_state.cons_view = "Mensal"
            st.rerun()

    st.markdown("---")

    # Filtros e Lógica baseada no Cartão Ativo
    if st.session_state.cons_view == "Anual":
        cidade_sel = "Todas"
        meses_sel = MESES_LIST
        st.markdown(f"<p style='color: #64748B; text-align: center; margin-top: -15px;'>Exibindo Relatório Consolidado Anual para {ano_selecionado}</p>", unsafe_allow_html=True)
    else:
        # Filtros de Refino (Expostos apenas no modo Mensal/Cidade)
        with st.expander("🔍 Filtros de Refino Territorial e Temporal", expanded=True):
            f1, f2 = st.columns([1.5, 2.5])
            with f1:
                cidade_lista = ["Todas"] + sorted(['Água Branca', 'Canapi', 'Delmiro Gouveia', 'Inhapi', 'Mata Grande', 'Olho d Água do Casado', 'Pariconha', 'Piranhas'])
                cidade_sel = st.selectbox("Cidade", cidade_lista, key="cons_cidade")
            with f2:
                meses_sel = st.multiselect("Filtrar Meses (impacta na coluna TOTAL)", options=MESES_LIST, default=MESES_LIST, key="cons_meses")

    df_raw, meses_ordem = get_consolidado_data(ano_selecionado, cidade_sel)

    if cidade_sel != "Todas":
        st.info(f"⚠️ Indicador CVP exibido como **BPM GLOBAL** (filtro por cidade indisponível).")

    # Processamento Final
    df_final = df_raw[['Indicador']].copy()
    for m in meses_sel:
        if m in df_raw.columns:
            df_final[m] = df_raw[m]
            
    df_final['TOTAL'] = df_final[meses_sel].sum(axis=1)

    def format_val(x):
        try: return f"{int(round(x))}"
        except: return str(x)

    styled_df = _apply_table_style(df_final).format(format_val, subset=meses_sel + ['TOTAL'])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Exportação Final com Filtros
    excel_data = convert_df_to_excel(df_final)
    
    # Título do PDF dinâmico conforme a visão
    title_doc = f"Relatório Consolidado {ano_selecionado}" if st.session_state.cons_view == "Anual" else f"Relatório {cidade_sel} - {ano_selecionado}"
    pdf_data = convert_df_to_pdf(df_final, title_doc)
    
    col_btn1, col_btn2, _ = st.columns([1, 1, 2])
    with col_btn1:
        st.download_button(
            label=f"📥 Exportar Excel",
            data=excel_data,
            file_name=f"Relatorio_{cidade_sel.replace(' ', '_')}_{ano_selecionado}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="btn_ex_cons"
        )
    with col_btn2:
        st.download_button(
            label=f"🖨️ Exportar PDF",
            data=pdf_data,
            file_name=f"Relatorio_{cidade_sel.replace(' ', '_')}_{ano_selecionado}.pdf",
            mime="application/pdf",
            key="btn_pdf_cons"
        )


def render_comparativo_module():
    # Inicialização de Estado da Aba
    if "comp_view" not in st.session_state:
        st.session_state.comp_view = "Anual"

    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 5px;">
        <h2 style='color: #0D3878 !important; margin-bottom: 0px;'>Comparativo de Performance (Ano a Ano)</h2>
        <p style='color: #64748B; font-size: 1rem; margin: 0;'>Acompanhe a evolução percentual da Criminalidade vs Produtividade Policial.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sub-Navegação
    c1, c2 = st.columns(2)
    with c1:
        ativo = st.session_state.comp_view == "Anual"
        label = f"{'✓ ' if ativo else ''}Comparativo Anual"
        if st.button(label, icon=":material/balance:", key="btn_comp_anual", use_container_width=True):
            st.session_state.comp_view = "Anual"
            st.rerun()
    with c2:
        ativo = st.session_state.comp_view == "Mensal"
        label = f"{'✓ ' if ativo else ''}Análise Temporal Personalizada"
        if st.button(label, icon=":material/tune:", key="btn_comp_mensal", use_container_width=True):
            st.session_state.comp_view = "Mensal"
            st.rerun()

    st.markdown("---")

    # Filtros e Lógica baseada no Cartão Ativo
    with st.expander("🔍 Configuração do Período de Comparação", expanded=True):
        f1, f2, f3 = st.columns([1, 1, 2])
        with f1:
            ano1 = st.selectbox("Ano Base", [2024, 2025, 2026], index=1)
        with f2:
            ano2 = st.selectbox("Ano Comp.", [2024, 2025, 2026], index=2)
        with f3:
            cidade_lista = ["Todas"] + sorted(['Água Branca', 'Canapi', 'Delmiro Gouveia', 'Inhapi', 'Mata Grande', 'Olho d Água do Casado', 'Pariconha', 'Piranhas'])
            cidade_sel = st.selectbox("Cidade", cidade_lista, key="comp_cidade")
        
        if st.session_state.comp_view == "Mensal":
            meses_sel = st.multiselect("Filtrar Meses Específicos", options=MESES_LIST, default=MESES_LIST, key="comp_meses")
        else:
            meses_sel = MESES_LIST
            st.info("📌 Comparando o Ciclo Anual Completo (Jan-Dez)")

    if ano1 == ano2:
        st.warning("Selecione anos diferentes para o comparativo.")
        return
        
    df_raw1, _ = get_consolidado_data(ano1, cidade_sel)
    df_raw2, _ = get_consolidado_data(ano2, cidade_sel)
    
    # Filtro de Meses e Recálculo de Totais
    df1 = df_raw1[['Indicador']].copy()
    df1['TOTAL'] = df_raw1[meses_sel].sum(axis=1)
    for m in meses_sel: df1[m] = df_raw1[m]
    
    df2 = df_raw2[['Indicador']].copy()
    df2['TOTAL'] = df_raw2[meses_sel].sum(axis=1)
    for m in meses_sel: df2[m] = df_raw2[m]
    
    # Constrói DataFrame Comparativo YoY
    df_comp = df1[['Indicador']].copy()
    
    for c in meses_sel:
        v1 = df1[c].astype(float)
        v2 = df2[c].astype(float)
        df_comp[c] = np.where(v1 == 0, np.where(v2 > 0, 100.0, 0.0), ((v2 - v1) / v1) * 100)
    
    # Calc variação do TOTAL
    tot1 = df1['TOTAL'].astype(float)
    tot2 = df2['TOTAL'].astype(float)
    df_comp['TOTAL'] = np.where(tot1 == 0, np.where(tot2 > 0, 100.0, 0.0), ((tot2 - tot1) / tot1) * 100)
    
    if cidade_sel != "Todas":
        st.info(f"⚠️ Nota: CVP e Drogas baseados em indicadores disponíveis para {cidade_sel}. CVP Geral permanece global.")
    
    # Motor Semântico de Estilo
    # Criminalidade (Aumento = Ruim/Vermelho)
    ind_crim = ['MVI', 'CVLI', 'Tentativa de MVI', 'CVP Geral', 'Maria da Penha']
    # Produtividade (Aumento = Bom/Verde)
    ind_prod = ['Cumprimento de Mandados', 'Visita Comunitária', 'Veículos Recuperados', 'Armas Apreendidas', 'Prisões']
    # Todos demais contém TCO e Drogas: Assumiremos Drogas/TCO como Aumento = Verde
    
    def stylize_yoy(val, indicador):
        if not isinstance(val, (int, float)) or pd.isna(val):
            return "font-weight: bold; color: white"
            
        is_crime = False
        for c_ind in ind_crim:
            if c_ind in str(indicador):
                is_crime = True
                break
                
        if val > 0:
            if is_crime: return "background-color: #FEE2E2; color: #DC2626; font-weight: bold;" # Ruim
            else: return "background-color: #DCFCE7; color: #16A34A; font-weight: bold;" # Bom
        elif val < 0:
            if is_crime: return "background-color: #DCFCE7; color: #16A34A; font-weight: bold;" # Bom
            else: return "background-color: #FEE2E2; color: #DC2626; font-weight: bold;" # Ruim
        else:
            return "color: #64748B;" # Zero mudanca
            
    def format_yoy(val):
        if not isinstance(val, (int, float)) or pd.isna(val):
            return str(val)
        if val == 0:
            return "0%"
        elif val > 0:
            return f"↑ +{val:.0f}%"
        else:
            return f"↓ {val:.0f}%"
            
    # Devido à complexidade semântica (Estilo baseado na célula + indicador), aplicamos row-level mapping
    styled_df = df_comp.copy()
    
    # Format texto
    cols_format = meses_sel + ['TOTAL']
    for c in cols_format:
        df_comp[c] = df_comp[c].apply(format_yoy)
        
    s = df_comp.style
    
    def apply_color(row):
        indicador = row['Indicador']
        styles = ['font-weight: 700; color: #1E293B;']
        
        for c in cols_format:
            val_str = row[c]
            if val_str == "0%":
                styles.append("color: #64748B;")
            elif "↑" in val_str:
                is_crime = any(ci in indicador for ci in ind_crim)
                if is_crime: styles.append("background-color: #FEE2E2; color: #DC2626; font-weight: bold;")
                else: styles.append("background-color: #DCFCE7; color: #16A34A; font-weight: bold;")
            elif "↓" in val_str:
                is_crime = any(ci in indicador for ci in ind_crim)
                if is_crime: styles.append("background-color: #DCFCE7; color: #16A34A; font-weight: bold;")
                else: styles.append("background-color: #FEE2E2; color: #DC2626; font-weight: bold;")
            else:
                styles.append("")
        return styles

    s = s.apply(apply_color, axis=1)
    
    st.dataframe(s, use_container_width=True, hide_index=True)
    
    # Export Buttons
    df_export = df_comp.copy()
    
    # Clean PDF incompatible Unicode chars (Arrows)
    for c in cols_format:
        df_export[c] = df_export[c].apply(lambda x: str(x).replace('↑ +', '+').replace('↑ ', '+').replace('↓ ', '') if isinstance(x, str) else x)
        
    excel_data = convert_df_to_excel(df_export)
    pdf_data = convert_df_to_pdf(df_export, f"Comparativo YoY {ano1} vs {ano2}")
    
    col_btn1, col_btn2, _ = st.columns([1, 1, 2])
    with col_btn1:
        st.download_button(
            label=f"📥 Exportar Comparativo (Excel)",
            data=excel_data,
            file_name=f"Comparativo_YoY_{ano1}v{ano2}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="btn_ex_yoy"
        )
    with col_btn2:
        st.download_button(
            label=f"🖨️ Exportar Comparativo (PDF)",
            data=pdf_data,
            file_name=f"Comparativo_YoY_{ano1}v{ano2}.pdf",
            mime="application/pdf",
            key="btn_pdf_yoy"
        )


def render_home_dashboard(ano_selecionado):
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 25px;">
        <h2 style="color: #0D3878 !important; margin-bottom: 5px;">📊 Painel de Indicadores</h2>
        <p style="color: #64748B; font-size: 1rem; margin: 0;">Ano de Referência: <strong>{ano_selecionado}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    df_final, meses = get_consolidado_data(ano_selecionado)
    df_ant, _ = get_consolidado_data(ano_selecionado - 1)
    
    if meses is None or not meses:
        st.warning(f"Sem dados mensais registrados para {ano_selecionado}")
        return
        
    import datetime
    # Map for current month
    meses_pt_map = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
                    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
    meses_num_map = {v: k for k, v in meses_pt_map.items()}

    # Encontrar o último mês com dados (em vez de usar o mês atual do sistema)
    mes_atual = None
    for m in reversed(MESES_LIST):
        if m in df_final.columns:
            total_no_mes = df_final[m].sum()
            if total_no_mes > 0:
                mes_atual = m
                break
    if mes_atual is None:
        # Se nenhum mês tem dados, usa o mês do sistema
        mes_num_sys = datetime.datetime.now().month
        mes_atual = meses_pt_map.get(mes_num_sys, MESES_LIST[0])
    
    mes_num = meses_num_map.get(mes_atual, 1)
    
    if mes_num > 1:
        mes_ant = meses_pt_map[mes_num - 1]
    else:
        mes_ant = 'Dezembro'
        
    def get_val(df_fonte, indicador, mes):
        if not mes or df_fonte.empty: return 0
        try:
            row = df_fonte[df_fonte['Indicador'] == indicador]
            if not row.empty:
                return int(row[mes].sum())
        except:
            pass
        return 0

    st.markdown(f"<p style='color: #64748B; text-align: center; margin-top: -15px;'>Dados referentes a <strong>{mes_atual} de {ano_selecionado}</strong> | Comparação com {mes_ant}</p>", unsafe_allow_html=True)

    mvi_atual = get_val(df_final, "MVI", mes_atual)
    mvi_ant = get_val(df_final, "MVI", mes_ant) if mes_num > 1 else get_val(df_ant, "MVI", mes_ant)
    
    cvli_atual = get_val(df_final, "CVLI (Homicídios)", mes_atual)
    cvli_ant = get_val(df_final, "CVLI (Homicídios)", mes_ant) if mes_num > 1 else get_val(df_ant, "CVLI (Homicídios)", mes_ant)

    cvp_atual = get_val(df_final, "CVP Geral", mes_atual)
    cvp_ant = get_val(df_final, "CVP Geral", mes_ant) if mes_num > 1 else get_val(df_ant, "CVP Geral", mes_ant)

    armas_atual = get_val(df_final, "Armas Apreendidas", mes_atual)
    armas_ant = get_val(df_final, "Armas Apreendidas", mes_ant) if mes_num > 1 else get_val(df_ant, "Armas Apreendidas", mes_ant)

    prisoes_atual = get_val(df_final, "Prisões", mes_atual)
    prisoes_ant = get_val(df_final, "Prisões", mes_ant) if mes_num > 1 else get_val(df_ant, "Prisões", mes_ant)
    
    drogas_mac_atual = get_val(df_final, "Drogas Apreendidas - Maconha (g)", mes_atual)
    drogas_mac_ant = get_val(df_final, "Drogas Apreendidas - Maconha (g)", mes_ant) if mes_num > 1 else get_val(df_ant, "Drogas Apreendidas - Maconha (g)", mes_ant)
    
    def box_html(title, val, comp_val, mes_comp, color_class):
        val_str = f"{val:,.0f}".replace(',', '.')
        comp_str = f"{comp_val:,.0f}".replace(',', '.')
        
        diff = val - comp_val
        delta_icon = "↑" if diff > 0 else "↓"
        delta_class = "negative" if diff > 0 else "positive"
        
        if "Armas" in title or "Prisões" in title or "Maconha" in title or "Recuperado" in title:
            delta_class = "positive" if diff > 0 else "negative"
        
        return f"""
        <div class="kpi-card {color_class}">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value val-{color_class.split('-')[1]}">{val_str}</div>
            <div class="kpi-delta {delta_class}">
                {delta_icon} {abs(diff):,.0f} vs {mes_comp}
            </div>
        </div>
        """

    c1, c2, c3 = st.columns(3)
    mes_comp_str = mes_ant if mes_ant else "Ano Anterior"

    with c1:
        st.markdown(box_html("Homicídios (CVLI)", cvli_atual, cvli_ant, mes_comp_str, "card-red"), unsafe_allow_html=True)
        st.markdown(box_html("CVP Geral", cvp_atual, cvp_ant, mes_comp_str, "card-orange"), unsafe_allow_html=True)
    with c2:
        st.markdown(box_html("Armas Apreendidas", armas_atual, armas_ant, mes_comp_str, "card-green"), unsafe_allow_html=True)
        st.markdown(box_html("Total de MVI", mvi_atual, mvi_ant, mes_comp_str, "card-red"), unsafe_allow_html=True)
    with c3:
        st.markdown(box_html("Prisões Realizadas", prisoes_atual, prisoes_ant, mes_comp_str, "card-blue"), unsafe_allow_html=True)
        st.markdown(box_html("Maconha Ap. (g)", drogas_mac_atual, drogas_mac_ant, mes_comp_str, "card-purple"), unsafe_allow_html=True)

    # Gráfico de Tendência na Home (Opcional, mas melhora visual)
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Tendência Mensal de Criminalidade vs Produtividade")
    
    # Plotly Theme Setup
    st.markdown("""<style> .js-plotly-plot .plotly .modebar { display: none; } </style>""", unsafe_allow_html=True)


# ----------------- MAIN APP LOGIC -----------------

render_header()




# ---------------- NAVEGAÇÃO E SINC DE DADOS ----------------
_, col_ano, col_sync = st.columns([7.0, 1.5, 1.5])

with col_ano:
    ano_selecionado = st.selectbox("Ano", [2024, 2025, 2026], index=2, label_visibility="collapsed")


with col_sync:
    if 'sync_active' not in st.session_state:
        st.session_state.sync_active = False

    if not st.session_state.sync_active:
        if st.button("Sincronizar", icon=":material/sync:", use_container_width=True, type="primary"):
            st.session_state.sync_active = True
            if __import__('os').path.exists("coleta_status.txt"): __import__('os').remove("coleta_status.txt")
            if __import__('os').path.exists("token_response.txt"): __import__('os').remove("token_response.txt")
            if __import__('os').path.exists("coleta_automatica.log"): __import__('os').remove("coleta_automatica.log")
            
            st.session_state.sync_proc = __import__('subprocess').Popen(
                ["cmd.exe", "/c", "Iniciar_Coleta.bat"],
                cwd=__import__('os').path.dirname(__import__('os').path.abspath(__file__))
            )
            with open("coleta_status.txt", "w", encoding="utf-8") as f:
                f.write("STARTING")
            st.rerun()
    else:
        status = "STARTING"
        if __import__('os').path.exists("coleta_status.txt"):
            try:
                with open("coleta_status.txt", "r", encoding="utf-8") as f:
                    status = f.read().strip()
            except: pass
        
        if status == "WAITING_TOKEN":
            st.info("Aguardando Token...")
            open_token_dialog()
        elif status == "FINISHED":
            st.success("✅ Concluído")
            if st.button("OK", use_container_width=True):
                st.session_state.sync_active = False
                if __import__('os').path.exists("coleta_status.txt"): __import__('os').remove("coleta_status.txt")
                st.rerun()
        else:
            st.info(f"⏳ Processando... ({status})")
            if hasattr(st.session_state, 'sync_proc') and st.session_state.sync_proc.poll() is not None:
                if status != "FINISHED":
                    with open("coleta_status.txt", "w", encoding="utf-8") as f:
                        f.write("FINISHED")
                    st.rerun()
            
            __import__('time').sleep(2.5)
            st.rerun()

# ---------------- NAVEGAÇÃO PRINCIPAL (Botões com Material Icons) ----------------
nav_abas = [
    {"key": "Inicio",       "label": "Início",        "icon": ":material/home:"},
    {"key": "Consolidado",  "label": "Consolidado",   "icon": ":material/summarize:"},
    {"key": "Comparativo",  "label": "Comparativo",   "icon": ":material/trending_up:"},
    {"key": "Vida",         "label": "Crimes Vida",   "icon": ":material/favorite:"},
    {"key": "Patrimonio",   "label": "Patrimônio",    "icon": ":material/account_balance_wallet:"},
    {"key": "Operacional",  "label": "Operacional",   "icon": ":material/shield:"},
]

if "nav_aba" not in st.session_state:
    st.session_state.nav_aba = "Inicio"

nav_cols = st.columns(len(nav_abas))
for i, aba in enumerate(nav_abas):
    with nav_cols[i]:
        ativo = st.session_state.nav_aba == aba["key"]
        label = f"{'✓ ' if ativo else ''}{aba['label']}"
        if st.button(label, icon=aba["icon"], key=f"nav_btn_{aba['key']}", use_container_width=True):
            st.session_state.nav_aba = aba["key"]
            st.rerun()

st.markdown("---")

nav_sel = st.session_state.nav_aba

# -------------------- INÍCIO --------------------
if nav_sel == "Inicio":
    render_home_dashboard(ano_selecionado)

# -------------------- CONSOLIDADO --------------------
elif nav_sel == "Consolidado":
    render_consolidado_module(ano_selecionado)

# -------------------- COMPARATIVO --------------------
elif nav_sel == "Comparativo":
    render_comparativo_module()

# -------------------- CRIMES VIDA --------------------
elif nav_sel == "Vida":
    vida_indicadores = [
        {"key": "MVI",              "label": "MVI Geral",          "icon": ":material/bar_chart:"},
        {"key": "Analitico",        "label": "Analítico MVI",      "icon": ":material/assignment:"},
        {"key": "Tentativa",        "label": "Tentativa de MVI",   "icon": ":material/warning:"},
        {"key": "AnaliticoTentativa","label": "Analítico Tentativa","icon": ":material/find_in_page:"},
        {"key": "CVLI",             "label": "CVLI",               "icon": ":material/monitoring:"},
    ]

    if "vida_indicador" not in st.session_state:
        st.session_state.vida_indicador = "MVI"

    st.markdown("<h2 style='text-align: center; color: #0D3878 !important; margin-bottom: 1rem;'>Crimes contra a Vida</h2>", unsafe_allow_html=True)

    cols_vida = st.columns(len(vida_indicadores))
    for i, ind in enumerate(vida_indicadores):
        with cols_vida[i]:
            ativo = st.session_state.vida_indicador == ind["key"]
            btn_label = f"{'✓ ' if ativo else ''}{ind['label']}"
            if st.button(btn_label, icon=ind['icon'], key=f"vida_btn_{ind['key']}", use_container_width=True):
                st.session_state.vida_indicador = ind["key"]

    st.markdown("---")

    vida_sel = st.session_state.vida_indicador
    if vida_sel == "MVI":
        render_mvi_module(load_data_mvi('MVI', ano_selecionado), "Estatísticas de MVI", ano_selecionado)
    elif vida_sel == "Analitico":
        render_analitico_mvi(load_data_mvi('MVI', ano_selecionado), "Analítico de MVI", ano_selecionado)
    elif vida_sel == "CVLI":
        render_mvi_module(load_data_cvli('MVI', ano_selecionado), "Estatísticas de CVLI", ano_selecionado)
    elif vida_sel == "Tentativa":
        render_mvi_module(load_data_mvi('Tentativa', ano_selecionado), "Estatísticas de Tentativa de MVI", ano_selecionado)
    elif vida_sel == "AnaliticoTentativa":
        render_analitico_mvi(load_data_mvi('Tentativa', ano_selecionado), "Analítico de Tentativa de MVI", ano_selecionado)

# -------------------- PATRIMÔNIO --------------------
elif nav_sel == "Patrimonio":
    try:
        df_cvp = load_data_cvp('CVP', ano_selecionado)
        if df_cvp.empty:
            st.warning(f"⚠️ Nenhum dado de CVP encontrado para {ano_selecionado}.")
        else:
            render_cvp_module(df_cvp, ano_selecionado)
    except Exception as e:
        st.error(f"Erro ao carregar Patrimônio: {e}")

# -------------------- OPERACIONAL --------------------
elif nav_sel == "Operacional":
    indicadores = [
        {"key": "Drogas",       "label": "Drogas Apreendidas",    "icon": ":material/science:"},
        {"key": "Armas",        "label": "Armas Apreendidas",     "icon": ":material/shield:"},
        {"key": "Prisoes",      "label": "Prisões",               "icon": ":material/gavel:"},
        {"key": "Veiculos",     "label": "Veículos Recuperados",  "icon": ":material/search:"},
        {"key": "MariaDaPenha", "label": "Maria da Penha",        "icon": ":material/account_balance:"},
        {"key": "TCO",          "label": "TCO",                   "icon": ":material/description:"},
        {"key": "Mandados",     "label": "Mandados de Prisão",    "icon": ":material/assignment_ind:"},
        {"key": "Visita",       "label": "Visita Comunitária",    "icon": ":material/holiday_village:"},
    ]

    if "op_indicador" not in st.session_state:
        st.session_state.op_indicador = "Drogas"

    st.markdown("<h2 style='text-align: center; color: #0D3878 !important; margin-bottom: 1rem;'>Indicadores Operacionais</h2>", unsafe_allow_html=True)

    cols_btns = st.columns(len(indicadores))
    for i, ind in enumerate(indicadores):
        with cols_btns[i]:
            ativo = st.session_state.op_indicador == ind["key"]
            btn_label = f"{'✓ ' if ativo else ''}{ind['label']}"
            if st.button(btn_label, icon=ind['icon'], key=f"op_btn_{ind['key']}", use_container_width=True):
                st.session_state.op_indicador = ind["key"]

    st.markdown("---")

    op_sel = st.session_state.op_indicador
    try:
        if op_sel == "Drogas":
            render_drogas_module(load_data_drogas('Drogas', ano_selecionado))
        elif op_sel == "Armas":
            render_mvi_module(load_data_armas('Armas', ano_selecionado), "Estatísticas de Armas Apreendidas", ano_selecionado)
        elif op_sel == "Prisoes":
            render_mvi_module(load_data_prisoes('Pris', ano_selecionado), "Estatísticas de Prisões", ano_selecionado)
        elif op_sel == "Veiculos":
            render_mvi_module(load_data_veiculos('Recuperado', ano_selecionado), "Estatísticas de Veículos Recuperados", ano_selecionado)
        elif op_sel == "MariaDaPenha":
            render_mvi_module(load_data_maria_da_penha('Maria da Penha', ano_selecionado), "Estatísticas de Violência Doméstica (Maria da Penha)", ano_selecionado)
        elif op_sel == "TCO":
            render_mvi_module(load_data_tco('TCO', ano_selecionado), "Estatísticas de Termo Circunstanciado (TCO)", ano_selecionado)
        elif op_sel == "Mandados":
            render_mvi_module(load_data_mandados('Mandado', ano_selecionado), "Estatísticas de Cumprimento de Mandados", ano_selecionado)
        elif op_sel == "Visita":
            render_mvi_module(load_data_visita('Visita Comun', ano_selecionado), "Estatísticas de Visita Comunitária", ano_selecionado)
    except Exception as e:
        st.error(f"Erro ao carregar indicador operacional: {e}")

