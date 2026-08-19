"""
coleta_cad_consolidada.py — Coletor Consolidado de Alto Desempenho do CAD (ScriptCase)
--------------------------------------------------------------------------------------
Arquitetura Híbrida Inteligente:
  - Fase 1 (HTTP Direto): Armas, Drogas, Veículos (~15 segundos total).
  - Fase 2 (Event-Driven Playwright): Maria da Penha, TCO, Mandados, Visitas.

Compatibilidade:
  - Lê credenciais de `cad_credentials.txt` ou `.env`.
  - Atualiza status em `coleta_progresso.txt`.
  - Respeita `selected_reports.txt`.
  - Salva em `dados/{ANO}/`.
"""

import os
import sys
import io
import time
import datetime
import unicodedata
from pathlib import Path
import requests
import bs4
import urllib3
from dotenv import load_dotenv
import asyncio
from playwright.async_api import async_playwright

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

ANO          = str(datetime.datetime.now().year)
BASE_DIR     = Path(__file__).parent.parent
DESTINO_DIR  = BASE_DIR / "dados" / ANO
LOG_FILE     = BASE_DIR / "logs" / "coleta_automatica.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

URL_BASE     = "https://analisacad.seguranca.al.gov.br/app/cad"

# ── Utilitários ───────────────────────────────────────────────────────────────

def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{timestamp}] {msg}"
    print(linha, flush=True)
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

def obter_credenciais():
    cred_file = BASE_DIR / "cad_credentials.txt"
    user, password, token = None, None, None
    if cred_file.exists():
        try:
            with open(cred_file, "r", encoding="utf-8") as f:
                parts = f.read().strip().split("|")
                if len(parts) >= 2:
                    user = parts[0]
                    password = parts[1]
                    token = parts[2] if len(parts) > 2 else ""
        except Exception:
            pass
    
    if not user or not password:
        user = os.getenv("CAD_USER")
        password = os.getenv("CAD_PASS")
        token = os.getenv("CAD_TOKEN", "")
        
    return user, password, token

# ── Motor HTTP Direto ─────────────────────────────────────────────────────────

def login_http_cad(session: requests.Session, user: str, password: str, token: str = "") -> bool:
    log("Autenticando sessão HTTP no CAD...")
    try:
        session.get(f"{URL_BASE}/cad_gestao_login/", verify=False, timeout=15)
        r_log = session.post(
            f"{URL_BASE}/cad_blank_validar_login/cad_blank_validar_login.php",
            data={"login": user, "senha": password},
            verify=False,
            timeout=15
        )
        if "cad_blank_menu" in r_log.text or "cad_gestao_token" in r_log.text:
            if token and "cad_gestao_token" in r_log.text:
                log("Validando Token 2FA via HTTP...")
                session.post(
                    f"{URL_BASE}/cad_blank_validar_token/cad_blank_validar_token.php",
                    data={"token": token},
                    verify=False,
                    timeout=15
                )
            log("✅ Autenticação HTTP no CAD confirmada.")
            return True
    except Exception as e:
        log(f"Erro na autenticação HTTP do CAD: {e}")
    return False

def coletar_relatorio_http(session: requests.Session, app_name: str, custom_filters: dict, filename: str) -> bool:
    log(f">>> [CAD-HTTP] Solicitando {filename}...")
    t0 = time.time()
    url_app = f"{URL_BASE}/{app_name}/{app_name}.php"
    
    try:
        r_form = session.get(url_app, verify=False, timeout=20)
        soup = bs4.BeautifulSoup(r_form.text, 'html.parser')
        form = soup.find('form', {'name': 'F1'})
        if not form:
            log(f"❌ Form F1 não encontrado em {app_name}")
            return False
            
        form_data = {inp.get('name'): inp.get('value', '') for inp in form.find_all('input') if inp.get('name')}
        for sel in form.find_all('select'):
            name = sel.get('name')
            if name: form_data[name] = ''
            
        form_data.update(custom_filters)
        form_data['bprocessa'] = 'pesq'
        form_data['nmgp_opcao'] = 'busca'
        
        session.post(url_app, data=form_data, verify=False, timeout=25)
        
        export_data = {
            'script_case_init': form_data.get('script_case_init'),
            'script_case_session': form_data.get('script_case_session'),
            'nmgp_opcao': 'xls',
            'nmgp_parms': '0'
        }
        r_xls = session.post(url_app, data=export_data, verify=False, timeout=35)
        
        soup_xls = bs4.BeautifulSoup(r_xls.text, 'html.parser')
        xls_actions = [f.get('action') for f in soup_xls.find_all('form') if '.xls' in f.get('action', '')]
        if not xls_actions:
            for a in soup_xls.find_all('a'):
                href = a.get('href', '')
                if '.xls' in href:
                    xls_actions.append(href)
                    
        if xls_actions:
            file_url = xls_actions[0]
            if not file_url.startswith('http'):
                file_url = "https://analisacad.seguranca.al.gov.br" + file_url
            
            r_file = session.get(file_url, verify=False, timeout=35)
            if r_file.status_code == 200 and len(r_file.content) > 1000:
                DESTINO_DIR.mkdir(parents=True, exist_ok=True)
                out_path = DESTINO_DIR / filename
                with open(out_path, 'wb') as f:
                    f.write(r_file.content)
                log(f"✅ {filename} salvo com sucesso ({len(r_file.content)} bytes em {time.time()-t0:.2f}s)!")
                return True
    except Exception as e:
        log(f"Erro ao coletar {filename} via HTTP: {e}")
        
    return False

# ── Motor Playwright Otimizado ───────────────────────────────────────────────

async def handle_download_pw(context, page, f_grid, filename):
    log(f"Iniciando exportação XLS para '{filename}'...")
    
    # 1. Dispara comando XLS
    try:
        await f_grid.evaluate("nm_gp_move('xls', '0')")
    except Exception:
        for sel in ['#sc_b_xls_top', '#sc_b_xls_bot', '.scButton_default:has-text("XLS")']:
            try:
                if await f_grid.locator(sel).first.is_visible():
                    await f_grid.locator(sel).first.click(timeout=3000)
                    break
            except Exception:
                pass

    log("Aguardando janela de download/processamento...")
    dl_page = None
    try:
        async with context.expect_page(timeout=60000) as dl_page_info:
            pass
        dl_page = await dl_page_info.value
    except Exception:
        pages = context.pages
        if len(pages) > 1:
            dl_page = pages[-1]

    if dl_page:
        try:
            await dl_page.wait_for_load_state('domcontentloaded', timeout=30000)
            
            btn_selectors = [
                'text=Baixar', 'text=DOWNLOAD', '#id_img_bt_baixar',
                '.scButton_default', 'a:has-text("Baixar")', 'a:has-text("DOWNLOAD")',
                'input[type="button"]', 'button'
            ]
            
            target_btn = None
            for sel in btn_selectors:
                try:
                    loc = dl_page.locator(sel).first
                    if await loc.is_visible(timeout=2000):
                        target_btn = loc
                        break
                except Exception:
                    continue
                    
            if not target_btn:
                log("Aguardando processamento SQL do servidor (até 120s)...")
                try:
                    await dl_page.locator('text=Baixar, text=DOWNLOAD, #id_img_bt_baixar').first.wait_for(state="visible", timeout=120000)
                    target_btn = dl_page.locator('text=Baixar, text=DOWNLOAD, #id_img_bt_baixar').first
                except Exception:
                    pass

            if target_btn:
                async with dl_page.expect_download(timeout=60000) as dl_info:
                    await target_btn.click()
                download = await dl_info.value
                DESTINO_DIR.mkdir(parents=True, exist_ok=True)
                path_xls = DESTINO_DIR / filename
                await download.save_as(str(path_xls))
                log(f"✅ {filename} salvo com sucesso!")
                await dl_page.close()
                return True
                
            # Fallback links diretos no popup
            links = await dl_page.locator('a').all()
            for link in links:
                href = await link.get_attribute('href')
                if href and ('.xls' in href.lower() or 'download' in href.lower()):
                    async with dl_page.expect_download(timeout=60000) as dl_info:
                        await link.click()
                    download = await dl_info.value
                    DESTINO_DIR.mkdir(parents=True, exist_ok=True)
                    path_xls = DESTINO_DIR / filename
                    await download.save_as(str(path_xls))
                    log(f"✅ {filename} salvo via link direto!")
                    await dl_page.close()
                    return True
                    
        except Exception as e:
            log(f"Aviso no processamento do download: {e}")
            try: await dl_page.close()
            except Exception: pass

    # Fallback na página principal
    try:
        async with page.expect_download(timeout=15000) as dl_info:
            await f_grid.locator('text=Baixar, #id_img_bt_baixar, a[href*="download"]').first.click(timeout=5000)
        download = await dl_info.value
        DESTINO_DIR.mkdir(parents=True, exist_ok=True)
        path_xls = DESTINO_DIR / filename
        await download.save_as(str(path_xls))
        log(f"✅ {filename} salvo via fallback!")
        return True
    except Exception:
        log(f"❌ Falha ao baixar '{filename}'.")
        return False

async def coletar_ocorrencias_playwright(browser, cookies, tasks):
    log(f"Iniciando navegador com sessão ativa para {len(tasks)} relatórios...")
    context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
    if cookies:
        await context.add_cookies(cookies)
        
    page = await context.new_page()
    url_menu = f"{URL_BASE}/cad_blank_menu_respons/cad_blank_menu_respons.php"
    
    try:
        await page.goto(url_menu, wait_until='domcontentloaded', timeout=45000)
        
        for task in tasks:
            log(f"--- Iniciando indicador: {task['name']} ---")
            update_report_status(task['name'], "PROCESSANDO")
            t_task = time.time()
            
            try:
                try:
                    await page.click('text=Pesquisar', timeout=4000)
                    await asyncio.sleep(1)
                except Exception:
                    pass
                    
                target_frame = None
                for f in page.frames:
                    try:
                        if await f.get_by_text("Pesquisar Ocorrências").is_visible():
                            target_frame = f
                            break
                    except Exception:
                        continue
                        
                if not target_frame: target_frame = page
                
                async with context.expect_page(timeout=30000) as new_page_info:
                    await target_frame.get_by_text("Pesquisar Ocorrências").first.click()
                t_page = await new_page_info.value
                await t_page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(2)
                
                f_filtros = None
                for f in t_page.frames:
                    if "fil.php" in f.url.lower():
                        f_filtros = f
                        break
                if not f_filtros: f_filtros = t_page
                
                # 1. Configura Data = Este Ano
                await f_filtros.select_option('#SC_data_cond', value='CY')
                
                # 2. Configura Órgão = POLÍCIA MILITAR e dispara AJAX
                await f_filtros.select_option('#SC_unid_id_orga_fk_orig', value='2##@@POLÍCIA MILITAR')
                await f_filtros.locator('#SC_unid_id_orga_fk_orig option[value="2##@@POLÍCIA MILITAR"]').dblclick()
                
                # 3. Aguarda 9º BPM
                sel_unid = '#SC_despc_id_orga_unid_fk_orig'
                await f_filtros.wait_for_selector(f"{sel_unid} option", timeout=15000)
                options = await f_filtros.locator(f"{sel_unid} option").all()
                val_9bpm = None
                for opt in options:
                    if "9º BPM" in await opt.inner_text():
                        val_9bpm = await opt.get_attribute('value')
                        break
                if val_9bpm:
                    await f_filtros.select_option(sel_unid, value=val_9bpm)
                    await f_filtros.locator(f"{sel_unid} option[value='{val_9bpm}']").dblclick()
                    
                # 4. Filtro específico
                if task['type'] == 'maria_da_penha':
                    await f_filtros.select_option('#SC_ocor_id_ocor_grup_fk_orig', label='LEI MARIA DA PENHA')
                    await f_filtros.locator('#SC_ocor_id_ocor_grup_fk_orig option').filter(has_text='LEI MARIA DA PENHA').dblclick()
                elif task['type'] == 'tco':
                    await f_filtros.select_option('#SC_despc_id_ocor_despc_soluc_tipo_fk_orig', value='9##@@ELABOROU TCO (PM)')
                    await f_filtros.locator('#SC_despc_id_ocor_despc_soluc_tipo_fk_orig option[value="9##@@ELABOROU TCO (PM)"]').dblclick()
                elif task['type'] == 'mandados':
                    await f_filtros.select_option('#SC_despc_id_ocor_despc_tip_fk_orig', value='6##@@CUMPRIMENTO DE MANDADO JUDICIAL')
                    await f_filtros.locator('#SC_despc_id_ocor_despc_tip_fk_orig option[value="6##@@CUMPRIMENTO DE MANDADO JUDICIAL"]').dblclick()
                elif task['type'] == 'visitas':
                    await f_filtros.select_option('#SC_ocor_id_ocor_grup_fk_orig', label='OCORRÊNCIA SEM ILICITUDE')
                    await f_filtros.locator('#SC_ocor_id_ocor_grup_fk_orig option').filter(has_text='OCORRÊNCIA SEM ILICITUDE').dblclick()
                    await asyncio.sleep(1)
                    for t in ["VISITA COMUNITÁRIA", "VISITA COMUNITÁRIA / MARIA DA PENHA", "VISITA PREVENTIVA"]:
                        try:
                            await f_filtros.select_option('#SC_ocor_id_ocor_sgrup_fk_orig', label=t)
                            await f_filtros.locator('#SC_ocor_id_ocor_sgrup_fk_orig option').filter(has_text=t).dblclick()
                        except Exception:
                            pass

                # 5. Clica em Pesquisar
                await f_filtros.click('#sc_b_pesq_top', timeout=5000)
                
                # 6. Aguarda Grid
                f_grid = None
                for _ in range(40):
                    for gr in t_page.frames:
                        if "grid" in gr.url.lower() and "fil" not in gr.url.lower():
                            f_grid = gr
                            break
                    if f_grid:
                        try:
                            if await f_grid.locator('#sc_b_xls_top, #sc_b_xls_bot').first.is_visible():
                                break
                        except Exception:
                            pass
                    await asyncio.sleep(1)
                    
                if not f_grid: f_grid = t_page
                
                # 7. Download
                res = await handle_download_pw(context, t_page, f_grid, task['filename'])
                update_report_status(task['name'], "OK" if res else "ERRO")
                log(f"Tempo do relatório {task['name']}: {time.time()-t_task:.2f}s")
                await t_page.close()
                
            except Exception as loop_e:
                log(f"⚠️ Erro no loop de '{task['name']}': {loop_e}")
                update_report_status(task['name'], "ERRO")
                try: await t_page.close()
                except Exception: pass
                
    finally:
        await context.close()

# ── Main ──────────────────────────────────────────────────────────────────────

async def main_async():
    log("="*60)
    log("🚀 Iniciando Coleta Consolidada do CAD (Híbrida Otimizada)")
    log("="*60)
    
    user, password, token = obter_credenciais()
    if not user or not password:
        log("❌ Erro: Credenciais CAD não encontradas.")
        return
        
    t_inicio = time.time()
    
    tasks_all = [
        {"name": "Armas Apreendidas", "app": "cad_grid_arma_boletim", "filename": f"Armas {ANO}.xls", "type": "armas", "engine": "http",
         "filters": {"ocor_dt_ocor_cond": "CY", "despc_id_orga_unid_fk": "32##@@9º BPM", "despc_id_orga_unid_fk_dest": ["32##@@9º BPM"]}},
        
        {"name": "Drogas Apreendidas", "app": "cad_grid_droga_boletim", "filename": f"Drogas {ANO}.xls", "type": "drogas", "engine": "http",
         "filters": {"ocor_dt_ocor_cond": "CY", "despc_id_orga_unid_fk": "32##@@9º BPM", "despc_id_orga_unid_fk_dest": ["32##@@9º BPM"]}},
        
        {"name": "Veiculos Recuperados", "app": "cad_grid_tb_ocor_despc_envl_veic_pesquisa", "filename": f"Veiculo Recuperado {ANO}.xls", "type": "veiculos", "engine": "http",
         "filters": {"ocor_dt_ocor_cond": "CY", "veic_id_orga_unid_fk": "32##@@9º BPM", "veic_id_orga_unid_fk_dest": ["32##@@9º BPM"], "veic_id_ocor_envl_veic_sitc_fk": "3##@@RECUPERADO", "veic_id_ocor_envl_veic_sitc_fk_dest": ["3##@@RECUPERADO"]}},
        
        {"name": "Maria da Penha", "filename": f"Maria da Penha {ANO}.xls", "type": "maria_da_penha", "engine": "playwright"},
        {"name": "TCO", "filename": f"TCO {ANO}.xls", "type": "tco", "engine": "playwright"},
        {"name": "Mandados de Prisão", "filename": f"Cumprimento de Mandados {ANO}.xls", "type": "mandados", "engine": "playwright"},
        {"name": "Visitas Comunitárias", "filename": f"Visita Comunitária {ANO}.xls", "type": "visitas", "engine": "playwright"}
    ]
    
    sel_file = BASE_DIR / "selected_reports.txt"
    selected = []
    if sel_file.exists():
        try:
            with open(sel_file, "r", encoding="utf-8") as f:
                selected = [normalize_str(line.strip()) for line in f if line.strip()]
        except Exception:
            pass
            
    tasks = [t for t in tasks_all if normalize_str(t['name']) in selected] if selected else tasks_all
    
    if not tasks:
        log("Nenhum relatório do CAD selecionado. Pulando.")
        return
        
    http_tasks = [t for t in tasks if t.get('engine') == 'http']
    pw_tasks = [t for t in tasks if t.get('engine') == 'playwright']
    
    cookies = []
    
    # 1. Fase HTTP
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    if login_http_cad(session, user, password, token):
        cookies = [{"name": k, "value": v, "domain": "analisacad.seguranca.al.gov.br", "path": "/"} for k, v in session.cookies.get_dict().items()]
        if http_tasks:
            log(f"\n--- Fase 1: Coleta HTTP Direta ({len(http_tasks)} relatórios) ---")
            for t in http_tasks:
                update_report_status(t['name'], "PROCESSANDO")
                res = coletar_relatorio_http(session, t['app'], t['filters'], t['filename'])
                update_report_status(t['name'], "OK" if res else "ERRO")
    else:
        log("Aviso: Falha no login HTTP. Executando todos no Playwright.")
        pw_tasks.extend(http_tasks)
        
    # 2. Fase Playwright Otimizada
    if pw_tasks:
        log(f"\n--- Fase 2: Coleta Playwright Otimizada ({len(pw_tasks)} relatórios) ---")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            await coletar_ocorrencias_playwright(browser, cookies, pw_tasks)
            await browser.close()

    log("\n" + "="*40)
    log(f"🏁 Coleta Consolidada do CAD Finalizada em {time.time() - t_inicio:.2f}s!")
    log("="*40)

if __name__ == "__main__":
    asyncio.run(main_async())
