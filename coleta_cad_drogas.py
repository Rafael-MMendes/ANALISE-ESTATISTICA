import asyncio
import os
import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

async def download_drogas_cad():
    USER = os.getenv('CAD_USER')
    PASS = os.getenv('CAD_PASS')
    WORKSPACE = os.path.dirname(os.path.abspath(__file__))
    DESTINO_DIR = os.path.join(WORKSPACE, "dados", "2026")
    os.makedirs(DESTINO_DIR, exist_ok=True)
    
    url_login = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
        page = await context.new_page()
        
        log("Acessando login CAD...")
        await page.goto(url_login, wait_until='domcontentloaded', timeout=90000)
        
        log("Aguardando campos de login...")
        try:
            await page.wait_for_selector('#cpf', timeout=30000)
            await page.fill('#cpf', USER)
            await page.fill('#senha', PASS)
            await page.click('input[type="submit"]')
        except Exception as e:
            log(f"Aviso: login automático falhou ({e}).")
        
        # Token MFA
        try:
            log("Verificando se pede Token...")
            await page.wait_for_selector('#token', timeout=20000)
            print("\n" + "="*50)
            print("🔑 TOKEN REQUERIDO PELO CAD!")
            print("Verifique seu e-mail e digite abaixo.")
            print("="*50)
            token = input("Digite o Token do CAD: ").strip()
            print("="*50 + "\n")
            await page.fill('#token', token)
            await page.click('input[type="submit"]')
        except:
            log("Token não solicitado ou timeout.")

        log("Aguardando Dashboard...")
        await page.wait_for_selector('text=Pesquisar', timeout=40000)
        
        log("Navegando: Pesquisar > Pesquisar Drogas na Base do CAD...")
        await page.click('text=Pesquisar')
        await asyncio.sleep(4)
        
        # Localiza o CARD de Drogas
        target_frame = None
        for f in page.frames:
            try:
                if await f.get_by_text("Pesquisar Drogas na Base do CAD").is_visible():
                    target_frame = f
                    break
            except:
                continue

        log("Abrindo card 'Pesquisar Drogas na Base do CAD'...")
        async with context.expect_page() as new_page_info:
            if target_frame is not None:
                await target_frame.get_by_text("Pesquisar Drogas na Base do CAD").first.click()
            else:
                await page.get_by_text("Pesquisar Drogas na Base do CAD").first.click()
                
        r_page = await new_page_info.value
        await r_page.wait_for_load_state()
        log("Nova aba 'Pesquisar Drogas na Base do CAD' aberta.")
        await asyncio.sleep(8)
        
        # Localiza o frame de filtros
        f_filtros = None
        for frame in r_page.frames:
            if "fil.php" in frame.url or "fil" in frame.url.lower():
                f_filtros = frame
                break
        if not f_filtros:
            f_filtros = r_page

        log("Configurando filtros...")

        # 1. Data da Ocorrência -> Este Ano (CY)
        try:
            log("Data: Este Ano (CY)...")
            await f_filtros.select_option('#SC_ocor_dt_ocor_cond', value='CY')
            await asyncio.sleep(1)
        except Exception as e:
            log(f"Erro Data: {e}")

        # 2. Unidade / Despacho -> 9º BPM (duplo clique)
        try:
            log("Unidade / Despacho: 9º BPM...")
            sel_unid = '#SC_despc_id_orga_unid_fk_orig option'
            await f_filtros.wait_for_selector(sel_unid, timeout=15000)
            options = await f_filtros.locator(sel_unid).all()
            val_9bpm = None
            for opt in options:
                text = await opt.inner_text()
                if "9º BPM" in text:
                    val_9bpm = await opt.get_attribute('value')
                    break
            
            if val_9bpm:
                log(f"9º BPM encontrado: {val_9bpm}")
                await f_filtros.locator('#SC_despc_id_orga_unid_fk_orig').select_option(value=val_9bpm)
                await f_filtros.locator(f'#SC_despc_id_orga_unid_fk_orig option[value="{val_9bpm}"]').dblclick()
            else:
                log("Aviso: '9º BPM' não encontrado na lista de Unidades.")
            await asyncio.sleep(1)
        except Exception as e:
            log(f"Erro Unidade: {e}")

        # Screenshot para validação
        await f_filtros.screenshot(path=os.path.join(WORKSPACE, 'debug_cad_drogas_filtros.png'))

        # 3. Pesquisa Avançada
        log("Disparando Pesquisa Avançada...")
        clicked = False
        for selector in ['text=Pesquisa Avançada', '#sc_b_pesq_bot', 'text=Pesquisar']:
            try:
                await f_filtros.click(selector, timeout=5000)
                clicked = True
                log(f"Clicado via: {selector}")
                break
            except:
                continue
        if not clicked:
            log("AVISO: não foi possível clicar no botão de pesquisa.")
        
        log("Aguardando resultados (15s)...")
        await asyncio.sleep(15)
        
        # Localiza o frame de resultados
        f_grid = r_page
        for frame in r_page.frames:
            url = frame.url
            if ("cad_grid" in url or "pesquisa" in url or "grid" in url) and "fil" not in url:
                f_grid = frame
                break
        
        await r_page.screenshot(path=os.path.join(WORKSPACE, 'debug_cad_resultados_drogas.png'))

        # 4. Exportação XLS
        log("Disparando exportação XLS...")
        try:
            await f_grid.evaluate("nm_gp_move('xls', '0')")
            log("Exportação enviada via JavaScript.")
        except Exception as e:
            log(f"Erro JS: {e}. Tentando clique direto...")
            try:
                await f_grid.locator('#sc_b_xls_top').click(timeout=5000)
            except:
                pass

        # 5. Baixar
        log("Aguardando janela de download...")
        download = None
        
        # Tenta nova aba de download (padrão CAD)
        try:
            async with context.expect_page(timeout=90000) as dl_page_info:
                pass
            dl_page = await dl_page_info.value
            await dl_page.wait_for_load_state()
            log("Janela de download aberta. Aguardando botão 'Baixar'...")
            await dl_page.wait_for_selector('text=Baixar, #id_img_bt_baixar', timeout=60000)
            async with dl_page.expect_download() as dl_info:
                try:
                    await dl_page.click('text=Baixar', timeout=10000)
                except:
                    await dl_page.click('#id_img_bt_baixar', timeout=10000)
            download = await dl_info.value
        except Exception as e:
            log(f"Fallback download (página principal): {e}")
            try:
                async with r_page.expect_download(timeout=15000) as dl_info:
                    try:
                        await f_grid.click('text=Baixar', timeout=5000)
                    except:
                        await f_grid.click('#id_img_bt_baixar', timeout=5000)
                download = await dl_info.value
            except Exception as e2:
                log(f"Erro final: {e2}")

        if download:
            path_xls = os.path.join(DESTINO_DIR, "Drogas 2026.xls")
            await download.save_as(path_xls)
            log(f"✅ Drogas baixadas com sucesso: {path_xls}")
        else:
            log("❌ Download não concluído.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(download_drogas_cad())
