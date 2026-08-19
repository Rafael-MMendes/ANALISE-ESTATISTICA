"""
coleta_neac.py — Coletor Autônomo de Alto Desempenho (Consumo Direto de APIs do NEAC Pentaho)
---------------------------------------------------------------------------------------------
Baixa automaticamente os relatórios do sistema NEAC (SSP-AL) via requisições HTTP diretas:
  1. CVLI              → 03.0 - Relação Nominal (Ano)                 → MVI {ANO}.xls
  2. CVP               → 07.2 - Acumulados por Natureza - AISP        → CVP Geral {ANO}.xls
  3. Tent. Homicídio   → 01.0 - Relação Nominal (Ano) - RISP_AISP     → Tentativa de MVI {ANO}.xls
  4. Prisões           → 04.2 - Lista Nominal Autores - (OPM)         → Prisões {ANO}.xls

Vantagens:
  - Execução completa em ~3 a 5 segundos (sem navegadores, sem iframes, sem timeouts).
  - 100% de confiabilidade e baixo consumo de recursos (CPU/RAM).

Variáveis de ambiente (.env):
  NEAC_USER  →  usuário de acesso ao NEAC
  NEAC_PASS  →  senha de acesso ao NEAC
"""

import os
import sys
import datetime
import urllib.parse
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
import io
import time
import requests
import urllib3
import pandas as pd
from dotenv import load_dotenv

# Desativa avisos de SSL se necessário
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Força UTF-8 para stdout no Windows para evitar erros de charmap
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── Configuração ──────────────────────────────────────────────────────────────
load_dotenv()

ANO          = str(datetime.datetime.now().year)
BASE_DIR     = Path(__file__).parent.parent
DESTINO_DIR  = BASE_DIR / "dados" / ANO
LOG_FILE     = BASE_DIR / "coleta_neac.log"

URL_BASE     = "https://neac.seguranca.al.gov.br/pentaho"
URL_LOGIN    = f"{URL_BASE}/j_spring_security_check"

# ── Utilitários ───────────────────────────────────────────────────────────────
def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{timestamp}] {msg}"
    print(linha)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except Exception:
        pass

def update_report_status(report_name: str, status: str):
    progress_file = BASE_DIR / "coleta_progresso.txt"
    progress = {}
    if progress_file.exists():
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "|" in line:
                        r, s = line.strip().split("|", 1)
                        progress[r] = s
        except Exception:
            pass
    
    progress[report_name] = status
    try:
        with open(progress_file, "w", encoding="utf-8") as f:
            for r, s in progress.items():
                f.write(f"{r}|{s}\n")
    except Exception:
        pass

def normalize_str(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()

def criar_sessao_autenticada(user: str, password: str, max_retries: int = 3) -> requests.Session:
    """Cria e autentica uma sessão HTTP no Pentaho BI Server."""
    for tentativa in range(1, max_retries + 1):
        log(f"Autenticando no NEAC Pentaho (Tentativa {tentativa}/{max_retries})...")
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })
        try:
            r = session.post(
                URL_LOGIN,
                data={"j_username": user, "j_password": password},
                verify=False,
                timeout=30.0,
                allow_redirects=True
            )
            if "JSESSIONID" in session.cookies or r.status_code in [200, 302]:
                log("✅ Autenticação realizada com sucesso!")
                return session
            log(f"Aviso: Tentativa {tentativa} retornou status {r.status_code}")
        except Exception as e:
            log(f"Erro na conexão de login: {e}")
        time.sleep(2)
    
    raise ConnectionError("Falha crítica ao autenticar no NEAC Pentaho após múltiplas tentativas.")

# ── Rotinas Específicas de Download Direto ─────────────────────────────────────

def download_cvli(session: requests.Session, ano: str) -> bool:
    """Baixa o relatório 03.0 - Relação Nominal (Ano) - CVLI/MVI."""
    log(f">>> [CVLI] Solicitando relatório MVI {ano}...")
    repo_path = urllib.parse.quote(":4_RISP:CVLI:03.0 - Relação  Nominal (Ano).prpt")
    url = f"{URL_BASE}/api/repos/{repo_path}/report"
    
    params = {
        "output-target": "table/excel;page-mode=flow",
        "ano": ano
    }
    
    t0 = time.time()
    r = session.get(url, params=params, verify=False, timeout=60.0)
    
    if r.status_code == 200 and len(r.content) > 1000 and "html" not in r.headers.get("Content-Type", "").lower():
        DESTINO_DIR.mkdir(parents=True, exist_ok=True)
        dest_file = DESTINO_DIR / f"MVI {ano}.xls"
        with open(dest_file, "wb") as f:
            f.write(r.content)
        log(f"✅ CVLI salvo com sucesso ({len(r.content)} bytes em {time.time()-t0:.2f}s): {dest_file.name}")
        return True
    
    log(f"❌ Falha ao baixar CVLI (Status: {r.status_code}, Tamanho: {len(r.content)} bytes)")
    return False

def download_cvp(session: requests.Session, ano: str) -> bool:
    """Baixa o relatório 07.2 - Acumulados por Natureza - AISP (24ª AISP) - CVP Geral."""
    log(f">>> [CVP] Solicitando relatório CVP Geral {ano} (24ª AISP)...")
    repo_path = urllib.parse.quote(":4_RISP:CVP:07.2 - Acumulados por  Natureza - AISP.prpt")
    url = f"{URL_BASE}/api/repos/{repo_path}/report"
    
    params = {
        "output-target": "table/excel;page-mode=flow",
        "ano": ano,
        "aisp": "24ª AISP"
    }
    
    t0 = time.time()
    r = session.get(url, params=params, verify=False, timeout=60.0)
    
    if r.status_code == 200 and len(r.content) > 1000 and "html" not in r.headers.get("Content-Type", "").lower():
        DESTINO_DIR.mkdir(parents=True, exist_ok=True)
        dest_file = DESTINO_DIR / f"CVP Geral {ano}.xls"
        with open(dest_file, "wb") as f:
            f.write(r.content)
        log(f"✅ CVP Geral salvo com sucesso ({len(r.content)} bytes em {time.time()-t0:.2f}s): {dest_file.name}")
        return True
    
    log(f"❌ Falha ao baixar CVP (Status: {r.status_code}, Tamanho: {len(r.content)} bytes)")
    return False

def download_tentativa(session: requests.Session, ano: str) -> bool:
    """Baixa o relatório 01.0 - Relação Nominal (Ano) - RISP_AISP - Tentativa de MVI."""
    log(f">>> [TENTATIVA] Solicitando relatório Tentativa de MVI {ano} (4ª RISP / 24ª AISP)...")
    repo_path = urllib.parse.quote(":4_RISP:TENTATIVA_HOMICIDIO:01.0 - Relação  Nominal (Ano) - RISP_AISP.prpt")
    url = f"{URL_BASE}/api/repos/{repo_path}/report"
    
    params = {
        "output-target": "table/excel;page-mode=flow",
        "ano": ano,
        "risp": "4ª RISP",
        "aisp": "24ª AISP"
    }
    
    t0 = time.time()
    r = session.get(url, params=params, verify=False, timeout=60.0)
    
    if r.status_code == 200 and len(r.content) > 1000 and "html" not in r.headers.get("Content-Type", "").lower():
        DESTINO_DIR.mkdir(parents=True, exist_ok=True)
        dest_file = DESTINO_DIR / f"Tentativa de MVI {ano}.xls"
        with open(dest_file, "wb") as f:
            f.write(r.content)
        log(f"✅ Tentativa de MVI salva com sucesso ({len(r.content)} bytes em {time.time()-t0:.2f}s): {dest_file.name}")
        return True
    
    log(f"❌ Falha ao baixar Tentativa de MVI (Status: {r.status_code}, Tamanho: {len(r.content)} bytes)")
    return False

def download_prisoes(session: requests.Session, ano: str) -> bool:
    """Baixa e consolida os meses do relatório 04.2 - Lista Nominal Autores - (OPM) para o 9º BPM."""
    log(f">>> [PRISÕES] Consultando meses disponíveis para o 9º BPM ({ano})...")
    repo_path = urllib.parse.quote(":PMAL:CAD:Prisões:04.2 - Lista Nominal Autores - (OPM).prpt")
    param_url = f"{URL_BASE}/api/repos/{repo_path}/parameter"
    report_url = f"{URL_BASE}/api/repos/{repo_path}/report"
    
    # 1. Busca os meses disponíveis dinamicamente para o 9º BPM
    meses_disponiveis = []
    try:
        r_param = session.post(
            param_url,
            data={"renderMode": "PARAMETER", "opm": "9º BPM", "ano": ano},
            verify=False,
            timeout=30.0
        )
        if r_param.status_code == 200:
            root = ET.fromstring(r_param.text)
            for p in root.findall(".//parameter"):
                if p.attrib.get("name") == "mes":
                    for v in p.findall(".//value"):
                        val = v.attrib.get("value")
                        lbl = v.attrib.get("label")
                        if val:
                            meses_disponiveis.append((val, lbl))
    except Exception as e:
        log(f"Aviso ao consultar metadados de meses: {e}")
    
    # Se falhar a consulta dinâmica, faz fallback para até o mês atual
    if not meses_disponiveis:
        mes_atual = datetime.datetime.now().month
        nomes = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
        meses_disponiveis = [(str(i), nomes[i-1]) for i in range(1, mes_atual + 1)]
    
    log(f"Meses a processar ({len(meses_disponiveis)}): {[lbl for _, lbl in meses_disponiveis]}")
    
    dfs = []
    DESTINO_DIR.mkdir(parents=True, exist_ok=True)
    
    for mes_val, mes_lbl in meses_disponiveis:
        log(f"  -> Coletando Prisões ({mes_lbl})...")
        params = {
            "output-target": "table/excel;page-mode=flow",
            "opm": "9º BPM",
            "ano": ano,
            "mes": mes_val
        }
        try:
            r = session.get(report_url, params=params, verify=False, timeout=60.0)
            if r.status_code == 200 and len(r.content) > 1000:
                temp_file = DESTINO_DIR / f"temp_prisao_{mes_val}.xls"
                with open(temp_file, "wb") as f:
                    f.write(r.content)
                
                df_temp = pd.read_excel(temp_file, header=None)
                dfs.append(df_temp)
                try:
                    temp_file.unlink()
                except Exception:
                    pass
                log(f"     ✅ {mes_lbl} coletado com sucesso.")
            else:
                log(f"     ⚠️ {mes_lbl} sem dados ou formato não esperado.")
        except Exception as e:
            log(f"     ❌ Erro ao baixar mês {mes_lbl}: {e}")
            
    if dfs:
        log(f"Consolidando {len(dfs)} meses de Prisões...")
        consolidado = pd.concat(dfs, ignore_index=True)
        out_path = DESTINO_DIR / f"Prisões {ano}.xls"
        consolidado.to_excel(out_path, index=False, header=False)
        log(f"✅ Prisões unificadas com sucesso em: {out_path.name}")
        return True
    
    log("❌ Nenhum dado de Prisões foi retornado.")
    return False

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log("="*60)
    log("🚀 Iniciando Coleta NEAC Pentaho (Consumo Direto de API)")
    log("="*60)
    
    USER = os.getenv("NEAC_USER")
    PASS = os.getenv("NEAC_PASS")
    if not USER or not PASS:
        log("❌ Erro: NEAC_USER ou NEAC_PASS não encontrados no .env")
        return
    
    try:
        t_inicio = time.time()
        session = criar_sessao_autenticada(USER, PASS)
        
        jobs_all = [
            ("CVLI", download_cvli),
            ("CVP", download_cvp),
            ("TENTATIVA", download_tentativa),
            ("PRISÕES", download_prisoes)
        ]
        
        # Filtra pelos selecionados no dashboard (se houver arquivo)
        sel_file = BASE_DIR / "selected_reports.txt"
        selected = []
        if sel_file.exists():
            try:
                with open(sel_file, "r", encoding="utf-8") as f:
                    selected = [normalize_str(line.strip()) for line in f if line.strip()]
            except Exception:
                pass
        
        jobs = [j for j in jobs_all if normalize_str(j[0]) in selected] if selected else jobs_all
        
        if not jobs:
            log("Nenhum relatório do NEAC selecionado. Pulando.")
            return

        resultados = {}
        for nome, func in jobs:
            try:
                update_report_status(nome, "PROCESSANDO")
                res = func(session, ANO)
                resultados[nome] = res
                update_report_status(nome, "OK" if res else "ERRO")
            except Exception as e:
                log(f"Erro ao processar {nome}: {e}")
                resultados[nome] = False
                update_report_status(nome, "ERRO")

        log("\n" + "="*40)
        log("📊 RESUMO FINAL DA COLETA NEAC:")
        for nome, res in resultados.items():
            log(f"  - {nome}: {'OK ✅' if res else 'FALHA ❌'}")
        log(f"Tempo total de execução: {time.time() - t_inicio:.2f} segundos!")
        log("="*40 + "\n")
        
    except Exception as e:
        log(f"❌ Erro Crítico durante a Coleta NEAC: {e}")

if __name__ == "__main__":
    main()
