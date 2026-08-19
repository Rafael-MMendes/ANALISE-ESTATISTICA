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

session.get('https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/', verify=False, timeout=15)
session.post('https://analisacad.seguranca.al.gov.br/app/cad/cad_blank_validar_login/cad_blank_validar_login.php', data={'login': USER, 'senha': PASS}, verify=False, timeout=15)

url_base = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_grid_tb_ocor_consulta_com_cadastro/cad_grid_tb_ocor_consulta_com_cadastro.php'
r_form = session.get(url_base, verify=False, timeout=20)
soup = bs4.BeautifulSoup(r_form.text, 'html.parser')

print("Buscando funções AJAX de recarregamento/cascata no HTML...")
for s in soup.find_all('script'):
    if s.text and any(k in s.text for k in ["ajax", "unid_id_orga_fk", "despc_id_orga_unid_fk", "nm_ajax"]):
        lines = [line.strip() for line in s.text.split('\n') if any(k in line for k in ["ajax", "unid_id_orga_fk", "despc_id_orga_unid_fk"])]
        print("\n".join(lines[:15]))
        break
