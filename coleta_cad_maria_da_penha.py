import asyncio
import os
import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

async def download_maria_da_penha_cad():
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
        
        log("Navegando: Pesquisar > Pesquisar Ocorrências...")
        await page.click('text=Pesquisar')
        await asyncio.sleep(4)
        
        # Localiza o CARD "Pesquisar Ocorrências"
        target_frame = None
        for f in page.frames:
            try:
                if await f.get_by_text("Pesquisar Ocorrências").is_visible():
                    target_frame = f
                    break
            except:
                continue

        log("Abrindo card 'Pesquisar Ocorrências'...")
        async with context.expect_page() as new_page_info:
            if target_frame is not None:
                await target_frame.get_by_text("Pesquisar Ocorrências").first.click()
            else:
                await page.get_by_text("Pesquisar Ocorrências").first.click()
                
        r_page = await new_page_info.value
        await r_page.wait_for_load_state()
        log("Nova aba 'Pesquisar Ocorrências' aberta.")
        await asyncio.sleep(5)
        
        # Localiza o frame de filtros
        f_filtros = None
        for frame in r_page.frames:
            if "cad_grid_tb_ocor_consulta_com_cadastro_fil.php" in frame.url:
                f_filtros = frame
                break
        if not f_filtros:
            f_filtros = r_page

        log("Configurando filtros...")

        # 1. Data da Ocorrência -> Este Ano (CY)
        try:
            log("Data: Este Ano (CY)...")
            await f_filtros.select_option('#SC_data_cond', value='CY')
            await asyncio.sleep(1)
        except Exception as e:
            log(f"Erro Data: {e}")

        # 2. Órgão -> POLÍCIA MILITAR (dispara AJAX que carrega Unidades)
        try:
            log("Órgão: POLÍCIA MILITAR...")
            await f_filtros.locator('#SC_unid_id_orga_fk_orig').select_option(value='2##@@POLÍCIA MILITAR')
            await f_filtros.locator('#SC_unid_id_orga_fk_orig option[value="2##@@POLÍCIA MILITAR"]').dblclick()
            await asyncio.sleep(3)  # Aguarda AJAX de Unidade carregar
        except Exception as e:
            log(f"Erro Órgão: {e}")

        # 3. Unidade -> 9º BPM
        try:
            log("Unidade: 9º BPM...")
            await f_filtros.wait_for_selector('#SC_despc_id_orga_unid_fk_orig option', timeout=15000)
            options = await f_filtros.locator('#SC_despc_id_orga_unid_fk_orig option').all()
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
                log("Aviso: '9º BPM' não encontrado.")
            await asyncio.sleep(1)
        except Exception as e:
            log(f"Erro Unidade: {e}")

        # 4. Natureza Geral -> Lei Maria da Penha
        try:
            log("Natureza Geral: Lei Maria da Penha...")
            sel_nat = '#SC_ocor_id_ocor_grup_fk_orig option'
            await f_filtros.wait_for_selector(sel_nat, timeout=15000)
            options = await f_filtros.locator(sel_nat).all()
            val_mp = None
            for opt in options:
                text = await opt.inner_text()
                if "MARIA DA PENHA" in text.upper() or "LEI  MARIA" in text.upper() or "LEI MARIA" in text.upper():
                    val_mp = await opt.get_attribute('value')
                    log(f"Encontrado: '{text.strip()}' = {val_mp}")
                    break
            
            if val_mp:
                await f_filtros.locator('#SC_ocor_id_ocor_grup_fk_orig').select_option(value=val_mp)
                await f_filtros.locator(f'#SC_ocor_id_ocor_grup_fk_orig option[value="{val_mp}"]').dblclick()
                await asyncio.sleep(1)
            else:
                log("Aviso: 'Lei Maria da Penha' não encontrada na Natureza Geral. Listando opções:")
                for opt in options:
                    t = await opt.inner_text()
                    if t.strip():
                        log(f"  - {t.strip()}")
        except Exception as e:
            log(f"Erro Natureza Geral: {e}")

        # Screenshot para validação
        await r_page.screenshot(path=os.path.join(WORKSPACE, 'debug_cad_maria_filtros.png'))

        # 5. Pesquisar
        log("Disparando Pesquisa...")
        try:
            await f_filtros.click('#sc_b_pesq_top', timeout=10000)
            log("Botão #sc_b_pesq_top acionado.")
        except Exception as e:
            log(f"Erro #sc_b_pesq_top: {e}. Tentando alternativas...")
            for sel in ['#sc_b_pesq_bot', 'text=Pesquisar']:
                try:
                    await f_filtros.click(sel, timeout=5000)
                    log(f"Clicado via: {sel}")
                    break
                except:
                    continue
        
        log("Aguardando resultados (15s)...")
        await asyncio.sleep(15)
        
        # Localiza o frame de resultados
        f_grid = r_page
        for frame in r_page.frames:
            if "cad_grid_tb_ocor_consulta_com_cadastro.php" in frame.url and "fil" not in frame.url:
                f_grid = frame
                break
        
        await r_page.screenshot(path=os.path.join(WORKSPACE, 'debug_cad_resultados_maria.png'))

        # 6. Exportação XLS
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

        # 7. Baixar
        log("Aguardando janela de download...")
        download = None
        
        try:
            async with context.expect_page(timeout=90000) as dl_page_info:
                pass
            dl_page = await dl_page_info.value
            await dl_page.wait_for_load_state()
            log("Janela aberta. Aguardando botão 'Baixar'...")
            await dl_page.wait_for_selector('text=Baixar, #id_img_bt_baixar', timeout=60000)
            async with dl_page.expect_download() as dl_info:
                try:
                    await dl_page.click('text=Baixar', timeout=10000)
                except:
                    await dl_page.click('#id_img_bt_baixar', timeout=10000)
            download = await dl_info.value
        except Exception as e:
            log(f"Fallback download: {e}")
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
            path_xls = os.path.join(DESTINO_DIR, "Maria da Penha 2026.xls")
            await download.save_as(path_xls)
            log(f"✅ Maria da Penha baixada com sucesso: {path_xls}")
        else:
            log("❌ Download não concluído.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(download_maria_da_penha_cad())
