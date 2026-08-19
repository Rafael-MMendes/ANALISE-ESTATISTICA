import requests
import os
import bs4
import time
from dotenv import load_dotenv
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

USER = os.getenv('CAD_USER')
PASS = os.getenv('CAD_PASS')

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
})

print("1. Login...")
session.get('https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/', verify=False)
session.post('https://analisacad.seguranca.al.gov.br/app/cad/cad_blank_validar_login/cad_blank_validar_login.php', data={'login': USER, 'senha': PASS}, verify=False)

print("2. Acessando cad_grid_arma_boletim...")
url_base = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_grid_arma_boletim/cad_grid_arma_boletim.php'
r_form = session.get(url_base, verify=False)

soup = bs4.BeautifulSoup(r_form.text, 'html.parser')
form = soup.find('form', {'name': 'F1'})

form_data = {}
for inp in form.find_all('input'):
    name = inp.get('name')
    if name:
        form_data[name] = inp.get('value', '')

for sel in form.find_all('select'):
    name = sel.get('name')
    if name:
        form_data[name] = ''

# Configura os filtros
form_data['ocor_dt_ocor_cond'] = 'CY'
form_data['despc_id_orga_unid_fk'] = '32##@@9º BPM'
form_data['despc_id_orga_unid_fk_orig'] = '32##@@9º BPM'
form_data['despc_id_orga_unid_fk_dest'] = ['32##@@9º BPM']
form_data['bprocessa'] = 'pesq'
form_data['nmgp_opcao'] = 'busca'

print(f"3. Submetendo busca (script_case_init={form_data.get('script_case_init')})...")
t0 = time.time()
r_grid = session.post(url_base, data=form_data, verify=False)
print(f"Status da busca: {r_grid.status_code}, tamanho: {len(r_grid.text)} bytes (tempo: {time.time()-t0:.2f}s)")

# 4. Exportar XLS
print("4. Solicitando exportação XLS...")
t1 = time.time()
export_data = {
    'script_case_init': form_data.get('script_case_init'),
    'script_case_session': form_data.get('script_case_session'),
    'nmgp_opcao': 'xls',
    'nmgp_parms': '0'
}
r_xls = session.post(url_base, data=export_data, verify=False)
print(f"Status XLS: {r_xls.status_code}, tamanho: {len(r_xls.content)} bytes, Content-Type: {r_xls.headers.get('Content-Type')}")

# Se o Scriptcase redirecionar para um gerador de download (ex: cad_grid_arma_boletim_download.php ou cad_grid_arma_boletim_export.php)
if "html" in r_xls.headers.get('Content-Type', '').lower():
    soup_xls = bs4.BeautifulSoup(r_xls.text, 'html.parser')
    print("Página de exportação retornada. Links:")
    for a in soup_xls.find_all('a'):
        print(f" -> Link: {a.text} ({a.get('href')})")
    for ifr in soup_xls.find_all('iframe'):
        print(f" -> Iframe: {ifr.get('src')}")
    # Verifica botões/forms
    for f in soup_xls.find_all('form'):
        print(f" -> Form: action={f.get('action')}, inputs={[i.get('name') for i in f.find_all('input')]}")
else:
    with open("teste_armas.xls", "wb") as f:
        f.write(r_xls.content)
    print("Salvo com sucesso em teste_armas.xls!")
