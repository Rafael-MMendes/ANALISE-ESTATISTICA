import requests
import os
import json
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

def inspect_report(repo_path, sample_params=None):
    print(f"\n=======================================================")
    print(f"RELATÓRIO: {repo_path}")
    print(f"=======================================================")
    url_param = f"https://neac.seguranca.al.gov.br/pentaho/api/repos/{repo_path}/parameter"
    r = session.post(url_param, data={"renderMode": "PARAMETER"}, verify=False)
    if r.status_code != 200:
        print(f"Erro ao buscar parâmetros: {r.status_code} - {r.text}")
        return
    
    root = ET.fromstring(r.text)
    for p in root.findall(".//parameter"):
        p_name = p.attrib.get("name")
        p_type = p.attrib.get("type")
        values = [v.attrib.get("value") for v in p.findall(".//value")]
        labels = [v.attrib.get("label") for v in p.findall(".//value")]
        print(f" -> Parâmetro: '{p_name}' (tipo: {p_type}, total opções: {len(values)})")
        if values:
            for v, l in list(zip(values, labels))[:5]:
                print(f"     Ex: value='{v}', label='{l}'")
            # If has 9º BPM or 24 or 2026, show it
            for v, l in zip(values, labels):
                if any(k in str(l) for k in ["9º BPM", "24ª", "2026", "JANEIRO"]):
                    print(f"     MATCH: value='{v}', label='{l}'")

    if sample_params:
        url_rep = f"https://neac.seguranca.al.gov.br/pentaho/api/repos/{repo_path}/report"
        sample_params["output-target"] = "table/excel;page-mode=flow"
        print(f"\nTestando download com params: {sample_params}...")
        r_rep = session.get(url_rep, params=sample_params, verify=False)
        print(f"Resultado: Status {r_rep.status_code}, Tamanho: {len(r_rep.content)} bytes, Content-Type: {r_rep.headers.get('Content-Type')}")

# 1. CVLI
inspect_report("%3A4_RISP%3ACVLI%3A03.0%20-%20Rela%C3%A7%C3%A3o%20%20Nominal%20(Ano).prpt", {"ano": "2026"})

# 2. CVP (Find exact file first)
r_cvp = session.get("https://neac.seguranca.al.gov.br/pentaho/api/repo/files/:4_RISP:CVP/children", headers={"Accept": "application/json"}, verify=False).json()
for f in r_cvp.get("repositoryFileDto", []):
    if "07.2" in f["name"]:
        cvp_path = f["path"].replace("/", "%3A")
        inspect_report(cvp_path, {"ano": "2026", "aisp": "24"})

# 3. TENTATIVA
r_tent = session.get("https://neac.seguranca.al.gov.br/pentaho/api/repo/files/:4_RISP:TENTATIVA_HOMICIDIO/children", headers={"Accept": "application/json"}, verify=False).json()
for f in r_tent.get("repositoryFileDto", []):
    if "01.0" in f["name"]:
        tent_path = f["path"].replace("/", "%3A")
        inspect_report(tent_path, {"ano": "2026", "risp": "4", "aisp": "24"})

# 4. PRISÕES
r_pri = session.get("https://neac.seguranca.al.gov.br/pentaho/api/repo/files/:PMAL:CAD:Pris%C3%B5es/children", headers={"Accept": "application/json"}, verify=False).json()
for f in r_pri.get("repositoryFileDto", []):
    if "04.2" in f["name"]:
        pri_path = f["path"].replace("/", "%3A")
        inspect_report(pri_path)
