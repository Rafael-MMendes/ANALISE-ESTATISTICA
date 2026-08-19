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

# Let's inspect menu page
r_menu = session.get('https://analisacad.seguranca.al.gov.br/app/cad/cad_blank_menu_respons/cad_blank_menu_respons.php', verify=False)
print("Status menu:", r_menu.status_code)
print("Menu text length:", len(r_menu.text))

soup = bs4.BeautifulSoup(r_menu.text, 'html.parser')
print("\nLinks encontrados no menu:")
for a in soup.find_all('a'):
    href = a.get('href')
    text = a.text.strip()
    if href and ('cad_' in href or 'javascript' in href):
        print(f" - [{text}] -> {href}")

for card in soup.find_all(['div', 'span', 'h5', 'h4']):
    txt = card.text.strip()
    if any(k in txt for k in ["Armas", "Veículos", "Drogas", "Ocorrências", "Pesquisar"]):
        onclick = card.get('onclick') or (card.parent.get('onclick') if card.parent else None)
        if onclick:
            print(f"Card: {txt[:40]} -> onclick={onclick}")
