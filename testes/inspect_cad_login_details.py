import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
})

url_login_page = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/'
r = session.get(url_login_page, verify=False)
soup = BeautifulSoup(r.text, 'html.parser')

print("Inputs na página:")
for inp in soup.find_all('input'):
    print(inp.attrs)

print("\nForms na página:")
for form in soup.find_all('form'):
    print("Form:", form.attrs)

print("\nScripts relevantes:")
for s in soup.find_all('script'):
    src = s.get('src')
    if src:
        print("Script src:", src)
    elif s.text and "login" in s.text.lower():
        print("Script inline (primeiros 300 chars):", s.text[:300])
