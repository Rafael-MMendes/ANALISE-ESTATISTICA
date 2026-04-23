import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Regex para limpar emojis
emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]|\uD83C[\uDF00-\uDFFF]|\uD83D[\uDC00-\uDE4F\uDE80-\uDEFF]|[\u2600-\u26FF\u2700-\u27BF]')

# Mapeador de ícones por contexto na string do título
def get_icon(t):
    t_lower = t.lower()
    if 'matriz' in t_lower or 'listagem' in t_lower: return 'table_chart'
    if 'exportar' in t_lower: return 'download'
    if 'evolu' in t_lower or 'mensal' in t_lower: return 'monitoring'
    if 'cidade' in t_lower or 'localidade' in t_lower: return 'map'
    if 'natureza' in t_lower or 'perfil' in t_lower: return 'donut_large'
    if 'estatística' in t_lower: return 'query_stats'
    if 'indicadores' in t_lower: return 'dashboard'
    return 'label'

# Remover tags span antigas para limpar títulos que já têm o style antes de substituir
text = re.sub(r'<span class="material-symbols-rounded".*?>.*?</span>\s*', '', text)

def repl_h3(m):
    inner_text = m.group(1).strip()
    cleaned = emoji_pattern.sub('', inner_text).strip()
    if not cleaned: return m.group(0)
    icon = get_icon(cleaned)
    return f"<h3 style='color: #0D3878 !important; margin-bottom: 5px; display: flex; align-items: center; gap: 8px;'><span class='material-symbols-rounded' style='font-size: 1.8rem;'>{icon}</span> {cleaned}</h3>"

def repl_h2(m):
    inner_text = m.group(2).strip() # group 2 holds title content
    cleaned = emoji_pattern.sub('', inner_text).strip()
    if not cleaned: return m.group(0)
    icon = get_icon(cleaned)
    return f"<h2 style='text-align: center; color: #0D3878 !important; margin-bottom: 2rem; display: flex; justify-content: center; align-items: center; gap: 8px;'><span class='material-symbols-rounded' style='font-size: 2.2rem;'>{icon}</span> {cleaned}</h2>"

def repl_md3(m):
    prefix = m.group(1) # st.markdown(f" or "
    inner_text = m.group(2).strip()
    suffix = m.group(3) # ", unsafe_allow...)
    
    cleaned = emoji_pattern.sub('', inner_text).strip()
    if not cleaned: return m.group(0)
    icon = get_icon(cleaned)
    
    html = f"<h3 style='color: #0D3878 !important; margin-bottom: 5px; display: flex; align-items: center; gap: 8px;'><span class='material-symbols-rounded' style='font-size: 1.8rem;'>{icon}</span> {cleaned}</h3>"
    
    # If missing, add unsafe_allow_html=True
    if "unsafe_allow_html" not in suffix:
        suffix = suffix.replace(')', ', unsafe_allow_html=True)')
        
    return f'{prefix}{html}{suffix}'

# Run substitutions
text = re.sub(r'<h3>(.*?)</h3>', repl_h3, text)
text = re.sub(r'(<h2.*?>)\s*(.*?)\s*</h2>', repl_h2, text)
text = re.sub(r'(st\.markdown\([f]?["\'])###\s+(.*?)((?:["\']\s*,|["\']\s*\)).*?\))', repl_md3, text)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Restyled successfully!")
