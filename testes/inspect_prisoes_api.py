import requests
import os
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

USER = os.getenv('NEAC_USER')
PASS = os.getenv('NEAC_PASS')

session = requests.Session()
login_url = "https://neac.seguranca.al.gov.br/pentaho/j_spring_security_check"
session.post(login_url, data={"j_username": USER, "j_password": PASS}, verify=False)

repo_path = "%3APMAL%3ACAD%3APris%C3%B5es%3A04.2%20-%20Lista%20Nominal%20Autores%20-%20(OPM).prpt"
url_param = f"https://neac.seguranca.al.gov.br/pentaho/api/repos/{repo_path}/parameter"
r = session.post(url_param, data={"renderMode": "PARAMETER"}, verify=False)
print(f"Status Prisoes /parameter: {r.status_code}")

root = ET.fromstring(r.text)
for p in root.findall(".//parameter"):
    p_name = p.attrib.get("name")
    p_type = p.attrib.get("type")
    values = [v.attrib.get("value") for v in p.findall(".//value")]
    labels = [v.attrib.get("label") for v in p.findall(".//value")]
    print(f"\nParâmetro: '{p_name}' (tipo: {p_type}, total opções: {len(values)})")
    for v, l in zip(values, labels):
        if any(k in str(l) for k in ["9º BPM", "2026", "JANEIRO", "FEVEREIRO"]):
            print(f"   MATCH: value='{v}', label='{l}'")

# Testar download de 1 mês de Prisões
url_rep = f"https://neac.seguranca.al.gov.br/pentaho/api/repos/{repo_path}/report"
params = {
    "output-target": "table/excel;page-mode=flow",
    "opm": "9º BPM",
    "ano": "2026",
    "mes": "JANEIRO"
}
# Também vamos testar quais nomes exatos de parâmetros são usados
print("\nTestando download Prisões Janeiro 2026...")
r_rep = session.get(url_rep, params=params, verify=False)
print(f"Resultado: Status {r_rep.status_code}, Tamanho: {len(r_rep.content)} bytes, Content-Type: {r_rep.headers.get('Content-Type')}")
