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

def list_folder(path_id):
    url = f"https://neac.seguranca.al.gov.br/pentaho/api/repo/files/{path_id}/children"
    r = session.get(url, headers={"Accept": "application/json"}, verify=False)
    if r.status_code == 200:
        try:
            return r.json()
        except:
            return r.text
    return f"Erro {r.status_code}: {r.text}"

def get_report_params(repo_path):
    url = f"https://neac.seguranca.al.gov.br/pentaho/api/repos/{repo_path}/parameter"
    r = session.post(url, data={"renderMode": "PARAMETER"}, verify=False)
    if r.status_code == 200:
        # Parse XML
        root = ET.fromstring(r.text)
        params = []
        for p in root.findall(".//parameter"):
            p_name = p.attrib.get("name")
            p_type = p.attrib.get("type")
            values = [v.attrib.get("value") for v in p.findall(".//value")]
            labels = [v.attrib.get("label") for v in p.findall(".//value")]
            params.append({
                "name": p_name,
                "type": p_type,
                "values": list(zip(values, labels))[:10],
                "total_values": len(values)
            })
        return params
    return f"Erro {r.status_code}"

print("=== 1. Explorando 4_RISP ===")
tree_4risp = list_folder(":4_RISP")
print("Pastas/Arquivos em 4_RISP:")
if isinstance(tree_4risp, dict) and "repositoryFileDto" in tree_4risp:
    for item in tree_4risp["repositoryFileDto"]:
        print(f" - {item.get('name')} (Dir: {item.get('folder')}, Path: {item.get('path')})")

print("\n=== 2. Explorando 4_RISP / CVP ===")
cvp_files = list_folder(":4_RISP:CVP")
if isinstance(cvp_files, dict) and "repositoryFileDto" in cvp_files:
    for item in cvp_files["repositoryFileDto"]:
        print(f" - {item.get('name')} (Path: {item.get('path')})")

print("\n=== 3. Explorando 4_RISP / TENTATIVA_HOMICIDIO ===")
tent_files = list_folder(":4_RISP:TENTATIVA_HOMICIDIO")
if isinstance(tent_files, dict) and "repositoryFileDto" in tent_files:
    for item in tent_files["repositoryFileDto"]:
        print(f" - {item.get('name')} (Path: {item.get('path')})")

print("\n=== 4. Explorando PMAL / CAD / Prisões ===")
# Lets try to find where Prisoes is
pmal_files = list_folder(":PMAL")
print("PMAL:", pmal_files)
pmal_cad = list_folder(":PMAL:CAD")
print("PMAL/CAD:", pmal_cad)
pmal_prisoes = list_folder(":PMAL:CAD:Prisões")
if not isinstance(pmal_prisoes, dict):
    pmal_prisoes = list_folder(":PMAL:CAD:Prisoes")
print("PMAL/CAD/Prisoes:", pmal_prisoes)
