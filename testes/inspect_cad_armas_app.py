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

# 1. Login
session.get('https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/', verify=False)
session.post('https://analisacad.seguranca.al.gov.br/app/cad/cad_blank_validar_login/cad_blank_validar_login.php', data={'login': USER, 'senha': PASS}, verify=False)

# 2. Acessar cad_grid_arma_boletim
url_armas = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_grid_arma_boletim/'
r = session.get(url_armas, verify=False)
print("Status Armas:", r.status_code)
print("Armas HTML (primeiros 600 chars):\n", r.text[:600])

soup = bs4.BeautifulSoup(r.text, 'html.parser')
iframes = soup.find_all('iframe')
print(f"\nIframes encontrados: {len(iframes)}")
for ifr in iframes:
    print("Iframe src:", ifr.get('src'), "name:", ifr.get('name'))

forms = soup.find_all('form')
print(f"\nForms encontrados: {len(forms)}")
for form in forms:
    print("Form action:", form.get('action'), "name:", form.get('name'))
    inputs = {inp.get('name'): inp.get('value', '') for inp in form.find_all('input') if inp.get('name')}
    print("Inputs:", inputs)
