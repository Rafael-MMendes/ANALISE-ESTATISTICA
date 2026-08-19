import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

USER = os.getenv('NEAC_USER')
PASS = os.getenv('NEAC_PASS')

session = requests.Session()
# Ignora avisos de SSL se necessário
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("1. Efetuando login via HTTP POST...")
t0 = time.time()
login_url = "https://neac.seguranca.al.gov.br/pentaho/j_spring_security_check"
r_login = session.post(login_url, data={"j_username": USER, "j_password": PASS}, verify=False, allow_redirects=True)
print(f"Login finalizado em {time.time() - t0:.2f}s! Status: {r_login.status_code}, Cookies: {session.cookies.get_dict()}")

# 2. Consultar os parâmetros do relatório CVLI
print("\n2. Consultando parâmetros do relatório CVLI...")
param_url = "https://neac.seguranca.al.gov.br/pentaho/api/repos/%3A4_RISP%3ACVLI%3A03.0%20-%20Rela%C3%A7%C3%A3o%20%20Nominal%20(Ano).prpt/parameter"
r_param = session.post(param_url, data={"renderMode": "PARAMETER"}, verify=False)
print(f"Status do /parameter: {r_param.status_code}")
print(f"Resposta dos parâmetros (primeiros 500 chars):\n{r_param.text[:500]}")

# 3. Testar download direto via /report
print("\n3. Testando download direto via /report...")
report_url = "https://neac.seguranca.al.gov.br/pentaho/api/repos/%3A4_RISP%3ACVLI%3A03.0%20-%20Rela%C3%A7%C3%A3o%20%20Nominal%20(Ano).prpt/report"

# Teste com diferentes formatos de output
for out_target in ["application/vnd.ms-excel", "table/excel;page-mode=flow", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
    t1 = time.time()
    params = {
        "output-target": out_target,
        "ano": "2026",
        "Ano": "2026",
        "parmAno": "2026"
    }
    r_rep = session.get(report_url, params=params, verify=False)
    print(f"Formato: {out_target} -> Status: {r_rep.status_code}, Tamanho: {len(r_rep.content)} bytes, Content-Type: {r_rep.headers.get('Content-Type')}, Tempo: {time.time() - t1:.2f}s")
    if r_rep.status_code == 200 and len(r_rep.content) > 1000 and "html" not in r_rep.headers.get("Content-Type", "").lower():
        with open("teste_cvli_direto.xls", "wb") as f:
            f.write(r_rep.content)
        print(f"   -> Salvo com sucesso em teste_cvli_direto.xls ({len(r_rep.content)} bytes)")
        break

# Se o GET não funcionar, testamos POST
if not os.path.exists("teste_cvli_direto.xls"):
    print("\nTestando POST para /report...")
    data = {
        "output-target": "table/excel;page-mode=flow",
        "output-type": "application/vnd.ms-excel",
        "ano": "2026"
    }
    r_post = session.post(report_url, data=data, verify=False)
    print(f"Status POST /report: {r_post.status_code}, Tamanho: {len(r_post.content)} bytes, Content-Type: {r_post.headers.get('Content-Type')}")
    if r_post.status_code == 200:
        with open("teste_cvli_direto.xls", "wb") as f:
            f.write(r_post.content)
        print("   -> Salvo com sucesso via POST!")
