import asyncio
import os
import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

async def download_armas_cad():
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
        
        log(f"Acessando login CAD...")
        await page.goto(url_login, wait_until='domcontentloaded', timeout=90000)
        
        log("Aguardando campos de login...")
        try:
            await page.wait_for_selector('#cpf', timeout=30000)
            await page.fill('#cpf', USER)
            await page.fill('#senha', PASS)
            await page.click('input[type="submit"]')
        except Exception as e:
            log(f"Aviso: Não consegui preencher o login automaticamente ({e}).")
        
        # Lógica de Token
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
        
        log("Navegando: Pesquisar > Pesquisar Armas na Base do CAD...")
        await page.click('text=Pesquisar')
        await asyncio.sleep(4)
        
        # Procura o CARD de Armas
        target_frame = None
        for f in page.frames:
            try:
                if await f.get_by_text("Pesquisar Armas na Base do CAD").is_visible():
                    target_frame = f
                    break
            except: continue

        log("Localizando o card 'Pesquisar Armas na Base do CAD'...")
        async with context.expect_page() as new_page_info:
            if target_frame is not None:
                await target_frame.get_by_text("Pesquisar Armas na Base do CAD").first.click()
            else:
                await page.get_by_text("Pesquisar Armas na Base do CAD").first.click()
                
        r_page = await new_page_info.value
        await r_page.wait_for_load_state()
        log("Nova aba 'Pesquisar Armas na Base do CAD' aberta.")
        await asyncio.sleep(8)
        
        # Localiza o frame de filtros
        f_filtros = None
        for frame in r_page.frames:
            if "fil.php" in frame.url or "fil" in frame.url.lower():
                f_filtros = frame
                break
        if not f_filtros: f_filtros = r_page

        log("Configurando filtros no ScriptCase...")
        
        # 1. Data do registro da ocorrência -> Este Ano
        try:
            log("Configurando Data: Este Ano (CY)...")
            await f_filtros.select_option('#SC_ocor_dt_ocor_cond', value='CY')
            await asyncio.sleep(1)
        except Exception as e: log(f"Erro Data: {e}")

        # 2. Unidade / Despacho -> 9º BPM
        try:
            log("Selecionando Unidade / Despacho: 9º BPM...")
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
                log(f"Valor encontrado para 9º BPM: {val_9bpm}")
                await f_filtros.locator('#SC_despc_id_orga_unid_fk_orig').select_option(value=val_9bpm)
                await f_filtros.locator(f'#SC_despc_id_orga_unid_fk_orig option[value="{val_9bpm}"]').dblclick()
            else: log("Aviso: '9º BPM' não encontrado.")
            await asyncio.sleep(1)
        except Exception as e: log(f"Erro Unidade: {e}")

        # Screenshot dos filtros para validação
        if f_filtros:
            await f_filtros.screenshot(path=os.path.join(WORKSPACE, 'debug_cad_armas_filtros_preenchidos.png'))

        # 4. Acionamento do botão 'Pesquisa Avançada'
        log("Disparando Pesquisa Avançada...")
        try:
            await f_filtros.click('text="Pesquisa Avançada"', timeout=5000)
        except:
            log("Botão text=Pesquisa Avançada não achado. Tentando via XPath...")
            try:
                # O botão pode ser sc_b_pesq_bot ou outra classe, mas no scriptcase o texto "Pesquisa Avançada" num span ou a
                await f_filtros.click('text=Pesquisa Avançada', timeout=5000)
            except:
                log("Tanto text='Pesquisa Avançada' quanto text=Pesquisa Avançada falharam. Tentando id sc_b_pesq_bot.")
                try:
                    await f_filtros.click('#sc_b_pesq_bot', timeout=5000)
                except Exception as inner_e:
                    log(f"Falha ao clicar no botão: {inner_e}")
                    raise inner_e

        log("Aguardando resultados...")
        await asyncio.sleep(15) 
        
        f_grid = None
        for frame in r_page.frames:
            if "cad_grid_arma_boletim.php" in frame.url and "fil" not in frame.url:
                f_grid = frame
                break
        if not f_grid: 
            for frame in r_page.frames:
                if "pesquisa.php" in frame.url and "fil" not in frame.url:
                    f_grid = frame
                    break
            if not f_grid:
                f_grid = r_page
            
        await f_grid.screenshot(path=os.path.join(WORKSPACE, 'debug_cad_resultados_armas.png'))
        
        # 5. Exportação -> XLS
        log("Disparando exportação XLS...")
        try:
            await f_grid.evaluate("nm_gp_move('xls', '0')")
            log("Comando exportação enviado via código.")
        except Exception as e:
            log(f"Erro exportação JS: {e}. Tentando click...")
            try:
                await f_grid.locator('#sc_b_xls_top').click()
            except:
                pass

        # 6. Baixar
        log("Aguardando janela de download...")
        try:
            async with context.expect_page(timeout=90000) as download_page_info: pass
            download_page = await download_page_info.value
            await download_page.wait_for_load_state()
            
            log("Aguardando botão 'Baixar'...")
            await download_page.wait_for_selector('text=Baixar, #id_img_bt_baixar', timeout=60000)
            
            async with download_page.expect_download() as download_info:
                try: await download_page.click('text=Baixar', timeout=10000)
                except: await download_page.click('#id_img_bt_baixar', timeout=10000)
            
            download = await download_info.value
            path_xls = os.path.join(DESTINO_DIR, "Armas 2026.xls")
            await download.save_as(path_xls)
            log(f"✅ Armas baixadas com sucesso: {path_xls}")
            
        except Exception as e:
            log(f"Aviso: Fallback para download na página principal... ({e})")
            try:
                async with r_page.expect_download(timeout=10000) as download_info:
                    await f_grid.click('text=Baixar')
                download = await download_info.value
                path_xls = os.path.join(DESTINO_DIR, "Armas 2026.xls")
                await download.save_as(path_xls)
                log(f"✅ Armas baixadas via fallback: {path_xls}")
            except: log("Erro final: Não foi possível baixar.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(download_armas_cad())
