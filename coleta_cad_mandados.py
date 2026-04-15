import asyncio
import os
import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

async def download_mandados_cad():
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
        
        log("Navegando: Pesquisar > Ocorrências...")
        await page.click('text=Pesquisar')
        await asyncio.sleep(4)
        
        target_frame = None
        for f in page.frames:
            try:
                if await f.get_by_text("Pesquisar Ocorrências").is_visible():
                    target_frame = f
                    break
            except: continue

        log("Tentando localizar 'Pesquisar Ocorrências'...")
        async with context.expect_page() as new_page_info:
            if target_frame is not None:
                await target_frame.get_by_text("Pesquisar Ocorrências").first.click()
            else:
                await page.get_by_text("Pesquisar Ocorrências").first.click()
        
        m_page = await new_page_info.value
        await m_page.wait_for_load_state()
        log("Nova aba 'Pesquisar Ocorrências' aberta.")
        await asyncio.sleep(5)
        
        f_filtros = None
        for frame in m_page.frames:
            if "cad_grid_tb_ocor_consulta_com_cadastro_fil.php" in frame.url:
                f_filtros = frame
                break
        
        if not f_filtros: f_filtros = m_page

        log("Configurando filtros no ScriptCase...")
        
        # 1. Data da Ocorrência -> Este Ano
        try:
            log("Configurando Data da Ocorrência: Este Ano (CY)...")
            await f_filtros.select_option('#SC_data_cond', value='CY')
            await asyncio.sleep(1)
        except Exception as e: log(f"Erro Data: {e}")

        # 2. Órgão -> POLÍCIA MILITAR
        try:
            log("Selecionando Órgão: POLÍCIA MILITAR...")
            await f_filtros.locator('#SC_unid_id_orga_fk_orig').select_option(value='2##@@POLÍCIA MILITAR')
            await f_filtros.locator('#SC_unid_id_orga_fk_orig option[value="2##@@POLÍCIA MILITAR"]').dblclick()
            await asyncio.sleep(2)
        except Exception as e: log(f"Erro Órgão: {e}")

        # 3. Unidade -> 9º BPM
        try:
            log("Selecionando Unidade: 9º BPM...")
            await f_filtros.wait_for_selector('#SC_despc_id_orga_unid_fk_orig option', timeout=15000)
            options = await f_filtros.locator('#SC_despc_id_orga_unid_fk_orig option').all()
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

        # 4. Tipo do Despacho no Geral -> CUMPRIMENTO DE MANDADO JUDICIAL
        try:
            log("Selecionando Tipo do Despacho: CUMPRIMENTO DE MANDADO JUDICIAL...")
            # ID: #SC_despc_id_ocor_despc_tip_fk_orig
            # Valor: 6##@@CUMPRIMENTO DE MANDADO JUDICIAL
            await f_filtros.locator('#SC_despc_id_ocor_despc_tip_fk_orig').select_option(value='6##@@CUMPRIMENTO DE MANDADO JUDICIAL')
            await f_filtros.locator('#SC_despc_id_ocor_despc_tip_fk_orig option[value="6##@@CUMPRIMENTO DE MANDADO JUDICIAL"]').dblclick()
            await asyncio.sleep(1)
        except Exception as e:
            log(f"Erro Tipo Despacho: {e}")

        # 5. Pesquisar
        log("Disparando Pesquisa...")
        try:
            await f_filtros.click('#sc_b_pesq_top', timeout=10000)
            log("Botão Pesquisar acionado.")
        except Exception as e:
            log(f"Erro Pesquisar: {e}. Tentando alternativa...")
            await f_filtros.click('text=Pesquisar', timeout=5000)
        
        log("Aguardando resultados...")
        await asyncio.sleep(15) 
        
        f_grid = None
        for frame in m_page.frames:
            if "cad_grid_tb_ocor_consulta_com_cadastro.php" in frame.url and "fil" not in frame.url:
                f_grid = frame
                break
        if not f_grid: f_grid = m_page
            
        await f_grid.screenshot(path=os.path.join(WORKSPACE, 'debug_cad_resultados_mandados.png'))
        
        # 6. Exportação -> XLS
        log("Disparando exportação XLS...")
        try:
            await f_grid.evaluate("nm_gp_move('xls', '0')")
            log("Comando exportação enviado.")
        except Exception as e:
            log(f"Erro exportação: {e}")

        # 7. Baixar
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
            path_xls = os.path.join(DESTINO_DIR, "Cumprimento de Mandados 2026.xls")
            await download.save_as(path_xls)
            log(f"✅ Mandados baixados com sucesso: {path_xls}")
            
        except Exception as e:
            log(f"Aviso: Fallback para download na página principal... ({e})")
            try:
                async with m_page.expect_download(timeout=10000) as download_info:
                    await f_grid.click('text=Baixar')
                download = await download_info.value
                path_xls = os.path.join(DESTINO_DIR, "Cumprimento de Mandados 2026.xls")
                await download.save_as(path_xls)
                log(f"✅ Mandados baixados via fallback: {path_xls}")
            except: log("Erro final: Não foi possível baixar.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(download_mandados_cad())
