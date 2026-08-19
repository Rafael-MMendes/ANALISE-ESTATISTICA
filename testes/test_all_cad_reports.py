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

print("1. Login CAD...")
session.get('https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/', verify=False)
r_log = session.post('https://analisacad.seguranca.al.gov.br/app/cad/cad_blank_validar_login/cad_blank_validar_login.php', data={'login': USER, 'senha': PASS}, verify=False)
print("Login status:", r_log.text)

def coletar_relatorio_scriptcase(app_name, custom_filters, output_filename):
    t0 = time.time()
    url_base = f'https://analisacad.seguranca.al.gov.br/app/cad/{app_name}/{app_name}.php'
    
    # 1. Carrega form de filtro
    r_form = session.get(url_base, verify=False)
    soup = bs4.BeautifulSoup(r_form.text, 'html.parser')
    form = soup.find('form', {'name': 'F1'})
    if not form:
        print(f"❌ Form F1 não encontrado em {app_name}")
        return False
        
    form_data = {inp.get('name'): inp.get('value', '') for inp in form.find_all('input') if inp.get('name')}
    for sel in form.find_all('select'):
        name = sel.get('name')
        if name: form_data[name] = ''
        
    # Aplica filtros customizados
    form_data.update(custom_filters)
    form_data['bprocessa'] = 'pesq'
    form_data['nmgp_opcao'] = 'busca'
    
    # 2. Submete a busca
    r_grid = session.post(url_base, data=form_data, verify=False)
    
    # 3. Dispara a exportação XLS
    export_data = {
        'script_case_init': form_data.get('script_case_init'),
        'script_case_session': form_data.get('script_case_session'),
        'nmgp_opcao': 'xls',
        'nmgp_parms': '0'
    }
    r_xls = session.post(url_base, data=export_data, verify=False)
    
    # 4. Localiza link do arquivo gerado
    soup_xls = bs4.BeautifulSoup(r_xls.text, 'html.parser')
    xls_actions = [f.get('action') for f in soup_xls.find_all('form') if '.xls' in f.get('action', '')]
    
    if not xls_actions:
        # Tenta procurar em links <a> ou iframes
        for a in soup_xls.find_all('a'):
            href = a.get('href', '')
            if '.xls' in href:
                xls_actions.append(href)
                
    if xls_actions:
        file_url = xls_actions[0]
        if not file_url.startswith('http'):
            file_url = 'https://analisacad.seguranca.al.gov.br' + file_url
        
        r_file = session.get(file_url, verify=False)
        if r_file.status_code == 200 and len(r_file.content) > 1000:
            os.makedirs("dados/2026", exist_ok=True)
            out_path = os.path.join("dados", "2026", output_filename)
            with open(out_path, 'wb') as f:
                f.write(r_file.content)
            print(f"✅ {output_filename} salvo com sucesso! ({len(r_file.content)} bytes em {time.time()-t0:.2f}s)")
            return True
            
    print(f"❌ Falha ao exportar {output_filename} (HTML retornado: {len(r_xls.text)} chars)")
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

# Teste 4: Maria da Penha
coletar_relatorio_scriptcase(
    'cad_grid_tb_ocor_consulta_com_cadastro',
    {
        'data_cond': 'CY',
        'unid_id_orga_fk': '2##@@POLÍCIA MILITAR',
        'unid_id_orga_fk_dest': ['2##@@POLÍCIA MILITAR'],
        'despc_id_orga_unid_fk': '32##@@9º BPM',
        'despc_id_orga_unid_fk_dest': ['32##@@9º BPM'],
        'ocor_id_ocor_grup_fk': '19##@@LEI MARIA DA PENHA',
        'ocor_id_ocor_grup_fk_dest': ['19##@@LEI MARIA DA PENHA']
    },
    'Maria da Penha 2026.xls'
)

# Teste 5: TCO
coletar_relatorio_scriptcase(
    'cad_grid_tb_ocor_consulta_com_cadastro',
    {
        'data_cond': 'CY',
        'unid_id_orga_fk': '2##@@POLÍCIA MILITAR',
        'unid_id_orga_fk_dest': ['2##@@POLÍCIA MILITAR'],
        'despc_id_orga_unid_fk': '32##@@9º BPM',
        'despc_id_orga_unid_fk_dest': ['32##@@9º BPM'],
        'despc_id_ocor_despc_soluc_tipo_fk': '9##@@ELABOROU TCO (PM)',
        'despc_id_ocor_despc_soluc_tipo_fk_dest': ['9##@@ELABOROU TCO (PM)']
    },
    'TCO 2026.xls'
)

# Teste 6: Mandados
coletar_relatorio_scriptcase(
    'cad_grid_tb_ocor_consulta_com_cadastro',
    {
        'data_cond': 'CY',
        'unid_id_orga_fk': '2##@@POLÍCIA MILITAR',
        'unid_id_orga_fk_dest': ['2##@@POLÍCIA MILITAR'],
        'despc_id_orga_unid_fk': '32##@@9º BPM',
        'despc_id_orga_unid_fk_dest': ['32##@@9º BPM'],
        'despc_id_ocor_despc_tip_fk': '6##@@CUMPRIMENTO DE MANDADO JUDICIAL',
        'despc_id_ocor_despc_tip_fk_dest': ['6##@@CUMPRIMENTO DE MANDADO JUDICIAL']
    },
    'Cumprimento de Mandados 2026.xls'
)
