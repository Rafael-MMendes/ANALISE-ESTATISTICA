print("DEBUG: Carregando script CAD...")
import asyncio
import os
import datetime
import unicodedata
from dotenv import load_dotenv
import sys
import io
from playwright.async_api import async_playwright

# Força UTF-8 para stdout no Windows para evitar erros de charmap
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def update_report_status(report_name, status):
    progress_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "coleta_progresso.txt")
    progress = {}
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "|" in line:
                        r, s = line.strip().split("|")
                        progress[r] = s
        except: pass
    
    progress[report_name] = status
    with open(progress_file, "w", encoding="utf-8") as f:
        for r, s in progress.items():
            f.write(f"{r}|{s}\n")

async def handle_download(context, page, f_grid, filename, destino_dir):
    log(f"Iniciando exportação XLS para '{filename}'...")
    
    # Lista de seletores possíveis para o botão XLS
    xls_selectors = ['#sc_b_xls_top', '#sc_b_xls_bot', 'text=XLS', '.scButton_default:has-text("XLS")']
    
    try:
        # Tenta disparar o comando JS de exportação (mais rápido se o contexto permitir)
        await f_grid.evaluate("nm_gp_move('xls', '0')")
    except Exception as e:
        log(f"Aviso: Erro ao disparar JS ({e}). Tentando clique direto...")
        clicked = False
        for sel in xls_selectors:
            try:
                if await f_grid.locator(sel).first.is_visible():
                    await f_grid.locator(sel).first.click(timeout=5000)
                    clicked = True
                    break
            except: continue
        if not clicked:
            log("Não foi possível acionar o botão XLS por JS ou Clique.")

    log("Aguardando janela de processamento/download...")
    dl_page = None
    try:
        # Tenta capturar a nova página que abre
        async with context.expect_page(timeout=60000) as dl_page_info:
            pass
        dl_page = await dl_page_info.value
    except:
        # Se falhou, verifica se já existe uma nova página aberta (fallback)
        pages = context.pages
        if len(pages) > 1:
            dl_page = pages[-1] # Assume que a última é a de download
            log("Janela de download detectada via lista de páginas.")

    if dl_page:
        try:
            await dl_page.wait_for_load_state('domcontentloaded', timeout=30000)
            log(f"Janela aberta: '{await dl_page.title()}'. Localizando botão de download...")
            
            # Tenta múltiplos seletores e padrões
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
                except: continue
            
            # Se não achou de cara, espera um pouco (o processamento do CAD pode ser lento)
            if not target_btn:
                log("Botão não visível de imediato. Aguardando até 120s...")
                try:
                    await dl_page.locator('text=Baixar, text=DOWNLOAD, #id_img_bt_baixar').first.wait_for(state="visible", timeout=120000)
                    target_btn = dl_page.locator('text=Baixar, text=DOWNLOAD, #id_img_bt_baixar').first
                except:
                    log("❌ DEBUG: Botão não apareceu após 120s.")
                    # Loga o HTML para diagnóstico
                    html_snippet = await dl_page.content()
                    log(f"DEBUG: HTML da página (primeiros 1000 chars): {html_snippet[:1000]}...")

            if target_btn:
                async with dl_page.expect_download(timeout=60000) as dl_info:
                    await target_btn.click()
                download = await dl_info.value
                path_xls = os.path.join(destino_dir, filename)
                await download.save_as(path_xls)
                log(f"✅ {filename} salvo com sucesso.")
                await dl_page.close()
                return True
            
            # Última tentativa: procurar qualquer link que pareça um arquivo
            links = await dl_page.locator('a').all()
            for link in links:
                href = await link.get_attribute('href')
                if href and ('.xls' in href.lower() or 'download' in href.lower()):
                    log(f"Tentando baixar via link direto: {href}")
                    async with dl_page.expect_download(timeout=60000) as dl_info:
                        await link.click()
                    download = await dl_info.value
                    path_xls = os.path.join(destino_dir, filename)
                    await download.save_as(path_xls)
                    log(f"✅ {filename} salvo via link direto.")
                    await dl_page.close()
                    return True

        except Exception as e:
            log(f"Erro ao processar download na nova janela: {e}")
            try: await dl_page.close()
            except: pass

    # Fallback final na página principal
    log("Tentando fallback final na aba principal...")
    try:
        async with page.expect_download(timeout=20000) as dl_info:
            # Tenta clicar em qualquer coisa que pareça um link de download gerado
            await f_grid.locator('text=Baixar, #id_img_bt_baixar, a[href*="download"]').first.click(timeout=5000)
        download = await dl_info.value
        path_xls = os.path.join(destino_dir, filename)
        await download.save_as(path_xls)
        log(f"✅ {filename} salvo com sucesso (fallback final).")
        return True
    except:
        log(f"❌ Falha crítica: Não foi possível baixar '{filename}'.")
        return False

async def script_coleta_consolidada():
    log("Iniciando script_coleta_consolidada...")
    try:
        # LER CREDENCIAIS DO ARQUIVO GERADO PELO APP
        cred_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cad_credentials.txt")
        USER, PASS, TOKEN = None, None, None
        
        if os.path.exists(cred_file):
            try:
                with open(cred_file, "r", encoding="utf-8") as f:
                    parts = f.read().strip().split("|")
                    if len(parts) == 3:
                        USER, PASS, TOKEN = parts
            except: pass

        if not USER or not PASS:
            log("❌ Erro: Credenciais CAD não encontradas ou inválidas.")
            return

        WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        DESTINO_DIR = os.path.join(WORKSPACE, "dados", "2026")
        os.makedirs(DESTINO_DIR, exist_ok=True)
        
        url_login = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/'
        
        tasks_all = [
            {"name": "Veiculos Recuperados", "card_text": "Pesquisar Veículos na Base do CAD", "filename": "Veiculo Recuperado 2026.xls", "type": "veiculos"},
            {"name": "Armas Apreendidas", "card_text": "Pesquisar Armas na Base do CAD", "filename": "Armas 2026.xls", "type": "armas"},
            {"name": "Drogas Apreendidas", "card_text": "Pesquisar Drogas na Base do CAD", "filename": "Drogas 2026.xls", "type": "drogas"},
            {"name": "Maria da Penha", "card_text": "Pesquisar Ocorrências", "filename": "Maria da Penha 2026.xls", "type": "maria_da_penha"},
            {"name": "TCO", "card_text": "Pesquisar Ocorrências", "filename": "TCO 2026.xls", "type": "tco"},
            {"name": "Mandados de Prisão", "card_text": "Pesquisar Ocorrências", "filename": "Cumprimento de Mandados 2026.xls", "type": "mandados"},
            {"name": "Visitas Comunitárias", "card_text": "Pesquisar Ocorrências", "filename": "Visita Comunitária 2026.xls", "type": "visitas"}
        ]

        def normalize_str(s):
            return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()

        # Filtra pelos selecionados
        sel_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "selected_reports.txt")
        selected = []
        if os.path.exists(sel_file):
            with open(sel_file, "r", encoding="utf-8") as f:
                selected = [normalize_str(line.strip()) for line in f if line.strip()]
            log(f"Relatórios selecionados para coleta: {selected}")
        else:
            log("Aviso: 'selected_reports.txt' não encontrado. Coletando todos.")
        
        tasks = [t for t in tasks_all if normalize_str(t['name']) in selected] if selected else tasks_all
        log(f"Total de tarefas CAD identificadas: {len(tasks)}")

        if not tasks:
            log("Nenhum relatório do CAD foi selecionado para esta execução.")
            return

        async with async_playwright() as p:
            log("Iniciando navegador Playwright...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
            page = await context.new_page()
            
            log(f"Acessando portal CAD: {url_login}")
            await page.goto(url_login, wait_until='domcontentloaded', timeout=90000)
            
            try:
                await page.wait_for_selector('#cpf', timeout=30000)
                await page.fill('#cpf', USER)
                await page.fill('#senha', PASS)
                await page.click('input[type="submit"]')
            except: pass
            
            try:
                await page.wait_for_selector('#token', timeout=10000)
                if TOKEN:
                    log("Token solicitado. Inserindo...")
                    await page.fill('#token', TOKEN)
                    await page.click('input[type="submit"]')
                    await asyncio.sleep(3)
            except: pass

            log("Aguardando carregamento do portal principal...")
            try:
                await page.wait_for_selector('text=Pesquisar', timeout=60000)
                log("Portal CAD carregado.")
            except Exception as e:
                log(f"❌ Erro ao carregar portal CAD: {e}")
                await browser.close()
                return

            for task in tasks:
                log(f"--- Iniciando indicador: {task['name']} ---")
                update_report_status(task['name'], "PROCESSANDO")
                
                try:
                    # Garantir que o menu Pesquisar está clicado/visível
                    try:
                        await page.click('text=Pesquisar', timeout=5000)
                        await asyncio.sleep(2)
                    except: pass

                    target_frame = None
                    for f in page.frames:
                        try:
                            if await f.get_by_text(task['card_text']).is_visible():
                                target_frame = f
                                break
                        except: continue

                    if not target_frame:
                        log(f"❌ Erro: Card '{task['card_text']}' não encontrado.")
                        update_report_status(task['name'], "ERRO")
                        continue

                    log(f"Abrindo relatório: {task['name']}")
                    async with context.expect_page() as new_page_info:
                        await target_frame.get_by_text(task['card_text']).first.click()
                    
                    t_page = await new_page_info.value
                    await t_page.wait_for_load_state()
                    await asyncio.sleep(5)

                    # Localizar Frame de Filtros
                    f_filtros = None
                    for frame in t_page.frames:
                        if "fil.php" in frame.url.lower():
                            f_filtros = frame
                            break
                    if not f_filtros: f_filtros = t_page

                    log("Preenchendo filtros...")
                    
                    if task['type'] in ['veiculos', 'armas', 'drogas']:
                        await f_filtros.select_option('#SC_ocor_dt_ocor_cond', value='CY')
                    else: 
                        await f_filtros.select_option('#SC_data_cond', value='CY')
                    
                    await asyncio.sleep(1)

                    sel_unid = ""
                    if task['type'] == 'veiculos': sel_unid = '#SC_veic_id_orga_unid_fk_orig'
                    elif task['type'] in ['armas', 'drogas']: sel_unid = '#SC_despc_id_orga_unid_fk_orig'
                    elif task['type'] in ['maria_da_penha', 'tco', 'mandados', 'visitas']: 
                        await f_filtros.select_option('#SC_unid_id_orga_fk_orig', value='2##@@POLÍCIA MILITAR')
                        await f_filtros.locator('#SC_unid_id_orga_fk_orig option[value="2##@@POLÍCIA MILITAR"]').dblclick()
                        await asyncio.sleep(3)
                        sel_unid = '#SC_despc_id_orga_unid_fk_orig'

                    if sel_unid:
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
                        await asyncio.sleep(1)

                    if task['type'] == 'veiculos':
                        await f_filtros.select_option('#SC_veic_id_ocor_envl_veic_sitc_fk_orig', label='RECUPERADO')
                        await f_filtros.locator('#SC_veic_id_ocor_envl_veic_sitc_fk_orig option').filter(has_text='RECUPERADO').dblclick()
                    elif task['type'] == 'maria_da_penha':
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
                        await asyncio.sleep(2)
                        tips = ["VISITA COMUNITÁRIA", "VISITA COMUNITÁRIA / MARIA DA PENHA", "VISITA PREVENTIVA"]
                        for t in tips:
                            try:
                                await f_filtros.select_option('#SC_ocor_id_ocor_sgrup_fk_orig', label=t)
                                await f_filtros.locator('#SC_ocor_id_ocor_sgrup_fk_orig option').filter(has_text=t).dblclick()
                            except: pass

                    await asyncio.sleep(1)
                    
                    log("Clicando em Pesquisar...")
                    btn_pesq = "#sc_b_pesq_top" if task['type'] not in ['veiculos', 'armas', 'drogas'] else "#sc_b_pesq_bot"
                    try: await f_filtros.click(btn_pesq, timeout=10000)
                    except: 
                        for alt in ["text=Pesquisa Avançada", "text=Filtrar", "text=Pesquisar"]:
                            try: 
                                await f_filtros.click(alt, timeout=5000)
                                break
                            except: pass
                    
                    wait_time = 45 if task['type'] in ['drogas', 'armas'] else 20
                    log(f"Aguardando processamento ({wait_time}s)...")
                    await asyncio.sleep(wait_time)

                    f_grid = None
                    for gr_frame in t_page.frames:
                        if "grid" in gr_frame.url.lower() and "fil" not in gr_frame.url.lower():
                            f_grid = gr_frame
                            break
                    if not f_grid: f_grid = t_page
                    
                    res = await handle_download(context, t_page, f_grid, task['filename'], DESTINO_DIR)
                    update_report_status(task['name'], "OK" if res else "ERRO")

                except Exception as loop_e:
                    log(f"⚠️ Erro no loop de '{task['name']}': {loop_e}")
                    update_report_status(task['name'], "ERRO")

                try: await t_page.close()
                except: pass
                await asyncio.sleep(2)

            log("🏁 Coleta Consolidada do CAD Finalizada!")
            await browser.close()
    except Exception as e:
        log(f"❌ ERRO CRÍTICO NO SCRIPT CAD: {e}")

if __name__ == "__main__":
    asyncio.run(script_coleta_consolidada())
