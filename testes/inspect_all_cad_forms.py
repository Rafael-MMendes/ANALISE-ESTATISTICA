import requests
import bs4
from dotenv import load_dotenv
import os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

USER = os.getenv('CAD_USER')
PASS = os.getenv('CAD_PASS')

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

session.get('https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/', verify=False)
session.post('https://analisacad.seguranca.al.gov.br/app/cad/cad_blank_validar_login/cad_blank_validar_login.php', data={'login': USER, 'senha': PASS}, verify=False)

def inspect_app_form(app_name):
    url = f'https://analisacad.seguranca.al.gov.br/app/cad/{app_name}/{app_name}.php'
    r = session.get(url, verify=False)
    soup = bs4.BeautifulSoup(r.text, 'html.parser')
    form = soup.find('form', {'name': 'F1'})
    print(f"\n=======================================================")
    print(f"APLICAÇÃO: {app_name} (Status: {r.status_code})")
    print(f"=======================================================")
    if not form:
        print(f"Form F1 não encontrado em {app_name}!")
        return
    
    inputs = [inp.get('name') for inp in form.find_all('input') if inp.get('name')]
    print(f"Inputs ({len(inputs)}): {inputs[:15]}...")
    
    selects = form.find_all('select')
    print(f"Selects ({len(selects)}):")
    for sel in selects:
        s_name = sel.get('name')
        options = [(opt.get('value'), opt.text.strip()) for opt in sel.find_all('option')]
        # Mostra opções relevantes
        matches = [o for o in options if any(k in o[1] for k in ["9º BPM", "RECUPERADO", "MARIA DA PENHA", "TCO", "MANDADO", "VISITA", "POLÍCIA MILITAR", "Este ano"])]
        if matches or 'cond' in str(s_name) or 'orig' in str(s_name):
            print(f" - Select '{s_name}': total {len(options)}, matches: {matches}")

# 1. Drogas
inspect_app_form('cad_grid_droga_boletim')

# 2. Veículos
inspect_app_form('cad_grid_tb_ocor_despc_envl_veic_pesquisa')

# 3. Ocorrências
inspect_app_form('cad_grid_tb_ocor_consulta_com_cadastro')
