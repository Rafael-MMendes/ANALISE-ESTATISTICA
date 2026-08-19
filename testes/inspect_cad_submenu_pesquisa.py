import requests
import os
import bs4
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

# Login
session.get('https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/', verify=False)
session.post('https://analisacad.seguranca.al.gov.br/app/cad/cad_blank_validar_login/cad_blank_validar_login.php', data={'login': USER, 'senha': PASS}, verify=False)

# Menu Pesquisa
url_pesq = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_blank_sub_menu_metro/cad_blank_sub_menu_metro.php?var_tipo_menu=pesquisa'
r = session.get(url_pesq, verify=False)
print("Status pesquisa menu:", r.status_code)

soup = bs4.BeautifulSoup(r.text, 'html.parser')
for a in soup.find_all('a'):
    print(f"Link: '{a.text.strip()}' -> href='{a.get('href')}'")

for elem in soup.find_all(True):
    onclick = elem.get('onclick')
    if onclick and 'cad_' in onclick:
        print(f"Elem '{elem.text.strip()[:40]}' -> onclick='{onclick}'")
