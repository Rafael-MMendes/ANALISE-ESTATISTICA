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

def coletar_relatorio_scriptcase(app_name, custom_filters, output_filename):
    print(f"\n--- Coletando {output_filename} ({app_name}) ---", flush=True)
    t0 = time.time()
    url_base = f'https://analisacad.seguranca.al.gov.br/app/cad/{app_name}/{app_name}.php'
    
    # 1. Carrega form de filtro
    try:
        r_form = session.get(url_base, verify=False, timeout=15)
    except Exception as e:
        print(f"Erro no GET form: {e}", flush=True)
        return False

    soup = bs4.BeautifulSoup(r_form.text, 'html.parser')
    form = soup.find('form', {'name': 'F1'})
    if not form:
        print(f"❌ Form F1 não encontrado em {app_name}", flush=True)
        return False
        
    form_data = {inp.get('name'): inp.get('value', '') for inp in form.find_all('input') if inp.get('name')}
    for sel in form.find_all('select'):
        name = sel.get('name')
        if name: form_data[name] = ''
        
    # Aplica filtros customizados
    form_data.update(custom_filters)
    form_data['bprocessa'] = 'pesq'
    form_data['nmgp_opcao'] = 'busca'
    
    print(f"Submetendo busca (script_case_init={form_data.get('script_case_init')})...", flush=True)
    try:
        r_grid = session.post(url_base, data=form_data, verify=False, timeout=20)
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
        r_xls = session.post(url_base, data=export_data, verify=False, timeout=30)
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

# Teste 1: Armas
coletar_relatorio_scriptcase(
    'cad_grid_arma_boletim',
    {
        'ocor_dt_ocor_cond': 'CY',
        'despc_id_orga_unid_fk': '32##@@9º BPM',
        'despc_id_orga_unid_fk_dest': ['32##@@9º BPM']
    },
    'Armas 2026.xls'
)

# Teste 2: Drogas
coletar_relatorio_scriptcase(
    'cad_grid_droga_boletim',
    {
        'ocor_dt_ocor_cond': 'CY',
        'despc_id_orga_unid_fk': '32##@@9º BPM',
        'despc_id_orga_unid_fk_dest': ['32##@@9º BPM']
    },
    'Drogas 2026.xls'
)

# Teste 3: Veículos
coletar_relatorio_scriptcase(
    'cad_grid_tb_ocor_despc_envl_veic_pesquisa',
    {
        'ocor_dt_ocor_cond': 'CY',
        'veic_id_orga_unid_fk': '32##@@9º BPM',
        'veic_id_orga_unid_fk_dest': ['32##@@9º BPM'],
        'veic_id_ocor_envl_veic_sitc_fk': '3##@@RECUPERADO',
        'veic_id_ocor_envl_veic_sitc_fk_dest': ['3##@@RECUPERADO']
    },
    'Veiculo Recuperado 2026.xls'
)
