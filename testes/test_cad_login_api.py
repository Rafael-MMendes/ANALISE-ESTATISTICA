import requests
import os
from bs4 import BeautifulSoup
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

url_login_page = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/'

print("1. Acessando página inicial de login do CAD...")
r_init = session.get(url_login_page, verify=False)
print(f"Status inicial: {r_init.status_code}, Cookies: {session.cookies.get_dict()}")

soup = BeautifulSoup(r_init.text, 'html.parser')
form = soup.find('form')
if form:
    print(f"Form action: {form.get('action')}, method: {form.get('method')}")
    inputs = {inp.get('name'): inp.get('value', '') for inp in form.find_all('input') if inp.get('name')}
    print(f"Campos do formulário:\n{inputs}")
else:
    print("Nenhum <form> encontrado no HTML!")
    print(f"Primeiros 500 chars do HTML:\n{r_init.text[:500]}")
