import requests
import bs4
import time
import os
import sys
import io
from dotenv import load_dotenv
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

USER = os.getenv('CAD_USER')
PASS = os.getenv('CAD_PASS')

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

print("1. Login CAD...", flush=True)
session.get('https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/', verify=False, timeout=15)
r_log = session.post('https://analisacad.seguranca.al.gov.br/app/cad/cad_blank_validar_login/cad_blank_validar_login.php', data={'login': USER, 'senha': PASS}, verify=False, timeout=15)
print("Login status:", r_log.text, flush=True)

def coletar_ocorrencias(custom_filters, output_filename):
    print(f"\n--- Coletando {output_filename} (cad_grid_tb_ocor_consulta_com_cadastro) ---", flush=True)
    t0 = time.time()
    url_base = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_grid_tb_ocor_consulta_com_cadastro/cad_grid_tb_ocor_consulta_com_cadastro.php'
    
    # 1. Carrega form de filtro
    try:
        r_form = session.get(url_base, verify=False, timeout=20)
    except Exception as e:
        print(f"Erro no GET form: {e}", flush=True)
        return False

    soup = bs4.BeautifulSoup(r_form.text, 'html.parser')
    form = soup.find('form', {'name': 'F1'})
    if not form:
        print("❌ Form F1 não encontrado", flush=True)
        return False
        
    form_data = {inp.get('name'): inp.get('value', '') for inp in form.find_all('input') if inp.get('name')}
    for sel in form.find_all('select'):
        name = sel.get('name')
        if name: form_data[name] = ''
        
    # Filtros base comuns para PMAL + 9º BPM + Este Ano
    base_filters = {
        'data_cond': 'CY',
        'unid_id_orga_fk': '2##@@POLÍCIA MILITAR',
        'unid_id_orga_fk_dest': ['2##@@POLÍCIA MILITAR'],
        'despc_id_orga_unid_fk': '32##@@9º BPM',
        'despc_id_orga_unid_fk_dest': ['32##@@9º BPM'],
        'bprocessa': 'pesq',
        'nmgp_opcao': 'busca'
    }
    
    form_data.update(base_filters)
    form_data.update(custom_filters)
    
    print(f"Submetendo busca (script_case_init={form_data.get('script_case_init')})...", flush=True)
    try:
        r_grid = session.post(url_base, data=form_data, verify=False, timeout=30)
    except Exception as e:
        print(f"Erro no POST busca: {e}", flush=True)
        return False
    
    print("Solicitando exportação XLS...", flush=True)
    export_data = {
        'script_case_init': form_data.get('script_case_init'),
        'script_case_session': form_data.get('script_case_session'),
        'nmgp_opcao': 'xls',
        'nmgp_parms': '0'
    }
    try:
        r_xls = session.post(url_base, data=export_data, verify=False, timeout=40)
    except Exception as e:
        print(f"Erro no POST exportação: {e}", flush=True)
        return False
    
    soup_xls = bs4.BeautifulSoup(r_xls.text, 'html.parser')
    xls_actions = [f.get('action') for f in soup_xls.find_all('form') if '.xls' in f.get('action', '')]
    
    if not xls_actions:
        for a in soup_xls.find_all('a'):
            href = a.get('href', '')
            if '.xls' in href:
                xls_actions.append(href)
                
    if xls_actions:
        file_url = xls_actions[0]
        if not file_url.startswith('http'):
            file_url = 'https://analisacad.seguranca.al.gov.br' + file_url
        
        print(f"Baixando arquivo de {file_url}...", flush=True)
        try:
            r_file = session.get(file_url, verify=False, timeout=30)
            if r_file.status_code == 200 and len(r_file.content) > 1000:
                os.makedirs("dados/2026", exist_ok=True)
                out_path = os.path.join("dados", "2026", output_filename)
                with open(out_path, 'wb') as f:
                    f.write(r_file.content)
                print(f"✅ {output_filename} salvo com sucesso! ({len(r_file.content)} bytes em {time.time()-t0:.2f}s)", flush=True)
                return True
        except Exception as e:
            print(f"Erro no download do arquivo: {e}", flush=True)
            
    print(f"❌ Falha ao exportar {output_filename} (HTML retornado: {len(r_xls.text)} chars)", flush=True)
    return False

# 1. Maria da Penha
coletar_ocorrencias(
    {
        'ocor_id_ocor_grup_fk': '19##@@LEI MARIA DA PENHA',
        'ocor_id_ocor_grup_fk_dest': ['19##@@LEI MARIA DA PENHA']
    },
    'Maria da Penha 2026.xls'
)

# 2. TCO
coletar_ocorrencias(
    {
        'despc_id_ocor_despc_soluc_tipo_fk': '9##@@ELABOROU TCO (PM)',
        'despc_id_ocor_despc_soluc_tipo_fk_dest': ['9##@@ELABOROU TCO (PM)']
    },
    'TCO 2026.xls'
)

# 3. Mandados
coletar_ocorrencias(
    {
        'despc_id_ocor_despc_tip_fk': '6##@@CUMPRIMENTO DE MANDADO JUDICIAL',
        'despc_id_ocor_despc_tip_fk_dest': ['6##@@CUMPRIMENTO DE MANDADO JUDICIAL']
    },
    'Cumprimento de Mandados 2026.xls'
)

# 4. Visitas Comunitárias (Vamos verificar os subgrupos de Visitas)
coletar_ocorrencias(
    {
        'ocor_id_ocor_grup_fk': '18##@@OCORRÊNCIA SEM ILICITUDE',
        'ocor_id_ocor_grup_fk_dest': ['18##@@OCORRÊNCIA SEM ILICITUDE'],
        'ocor_id_ocor_sgrup_fk_dest': ['VISITA COMUNITÁRIA', 'VISITA COMUNITÁRIA / MARIA DA PENHA', 'VISITA PREVENTIVA']
    },
    'Visita Comunitária 2026.xls'
)
