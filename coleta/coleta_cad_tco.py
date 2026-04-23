import asyncio
import os
import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

async def download_tco_cad():
    USER = os.getenv('CAD_USER')
    PASS = os.getenv('CAD_PASS')
    WORKSPACE = os.path.dirname(os.path.abspath(__file__))
    # Pasta de destino relativa ao script
    DESTINO_DIR = os.path.join(WORKSPACE, "dados", "2026")
    os.makedirs(DESTINO_DIR, exist_ok=True)
    
    url_login = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # Visível para o usuário acompanhar se quiser
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
        page = await context.new_page()
        
        log(f"Acessando login CAD...")
        # Aumentar timeout e usar domcontentloaded para não travar em scripts lentos
        await page.goto(url_login, wait_until='domcontentloaded', timeout=90000)
        
        log("Aguardando campos de login...")
        try:
            await page.wait_for_selector('#cpf', timeout=30000)
            await page.fill('#cpf', USER)
            await page.fill('#senha', PASS)
            await page.click('input[type="submit"]')
        except Exception as e:
            log(f"Aviso: Não consegui preencher o login automaticamente ({e}). Tente preencher manualmente na janela que abriu.")
        
        # Lógica de Token
        try:
            log("Verificando se pede Token...")
            # Dá mais tempo para a página de login processar e mudar para o Token
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
            log("Token não solicitado ou timeout (você pode ter passado direto ou login falhou).")

        log("Aguardando Dashboard...")
        await page.wait_for_selector('text=Pesquisar', timeout=40000)
        
        # 1. Menu Pesquisar -> Card Pesquisar Ocorrências
        log("Navegando: Pesquisar > Ocorrências...")
        await page.click('text=Pesquisar')
        await asyncio.sleep(4)
        
        # Tirar print do menu aberto para debug
        await page.screenshot(path=os.path.join(WORKSPACE, 'debug_cad_menu_pesquisar.png'))
        
        # Listar sub-opções
        sub_links = await page.locator('a, button, [role="button"], h3, h4').all_inner_texts()
        log(f"Sub-elementos encontrados no DOM principal: {sub_links[:20]}")
        
        # Verificar iFrames
        frames = page.frames
        log(f"Encontrados {len(frames)} frames. Verificando conteúdo dos frames...")
        target_frame = None
        for f in frames:
            try:
                content = await f.get_by_text("Pesquisar Ocorrências").is_visible()
                if content:
                    log(f"Frame encontrado! Nome: {f.name}, URL: {f.url}")
                    target_frame = f
                    break
            except:
                continue

        # Clicar no Card "Pesquisar Ocorrências"
        log("Tentando localizar 'Pesquisar Ocorrências'...")
        async with context.expect_page() as new_page_info:
            if target_frame is not None:
                await target_frame.get_by_text("Pesquisar Ocorrências").first.click()
            else:
                # Tenta seletores mais amplos no page principal como fallback
                await page.get_by_text("Pesquisar Ocorrências").first.click()
        tco_page = await new_page_info.value
        await tco_page.wait_for_load_state()
        log("Nova aba 'Pesquisar Ocorrências' aberta.")
        
        # O formulário no ScriptCase geralmente fica em um iFrame dentro dessa aba.
        # Vamos tentar localizar o iFrame principal (geralmente name='nm_iframe_filtro' ou similar)
        # No dump, o frame_0 era o principal.
        await asyncio.sleep(5)
        
        # Tenta pegar o frame principal de filtros
        f_filtros = None
        for frame in tco_page.frames:
            if "cad_grid_tb_ocor_consulta_com_cadastro_fil.php" in frame.url:
                f_filtros = frame
                break
        
        if not f_filtros:
            log("Frame de filtros não encontrado nominalmente, usando aba principal...")
            f_filtros = tco_page

        # 2. Preenchimento dos Filtros
        log("Configurando filtros no ScriptCase...")
        
        # Data da Ocorrência -> Este Ano
        try:
            log("Configurando Data da Ocorrência: Este Ano (CY)...")
            # id="SC_data_cond" valor "CY" (Este Ano - conforme dump)
            await f_filtros.select_option('#SC_data_cond', value='CY')
            await asyncio.sleep(1)
        except Exception as e:
            log(f"Erro ao selecionar Data (CY): {e}")

        # Órgão -> POLÍCIA MILITAR
        try:
            log("Selecionando Órgão: POLÍCIA MILITAR...")
            await f_filtros.locator('#SC_unid_id_orga_fk_orig').select_option(value='2##@@POLÍCIA MILITAR')
            await f_filtros.locator('#SC_unid_id_orga_fk_orig option[value="2##@@POLÍCIA MILITAR"]').dblclick()
            await asyncio.sleep(2) # Aguarda o AJAX de Unidade
        except Exception as e:
            log(f"Erro ao selecionar Órgão: {e}")

        # Unidade -> 9º BPM
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
            else:
                log("Aviso: '9º BPM' não encontrado na lista de Unidades.")
            await asyncio.sleep(1)
        except Exception as e:
            log(f"Erro ao selecionar Unidade (9º BPM): {e}")

        # Sub Solução -> ELABOROU TCO (PM)
        try:
            log("Selecionando Sub Solução: ELABOROU TCO (PM)...")
            await f_filtros.locator('#SC_despc_id_ocor_despc_soluc_tipo_fk_orig').select_option(value='9##@@ELABOROU TCO (PM)')
            await f_filtros.locator('#SC_despc_id_ocor_despc_soluc_tipo_fk_orig option[value="9##@@ELABOROU TCO (PM)"]').dblclick()
            await asyncio.sleep(1)
        except Exception as e:
            log(f"Erro ao selecionar Sub Solução: {e}")

        # 3. Pesquisar
        log("Disparando Pesquisa (Botão Superior)...")
        try:
            await f_filtros.click('#sc_b_pesq_top', timeout=10000)
            log("Botão Pesquisar acionado.")
        except Exception as e:
            log(f"Erro ao clicar em Pesquisar: {e}. Tentando alternativa...")
            await f_filtros.click('text=Pesquisar', timeout=5000)
        
        log("Aguardando carregamento dos resultados...")
        await asyncio.sleep(15) 
        
        # O grid pode estar em um frame
        f_grid = None
        for frame in tco_page.frames:
            if "cad_grid_tb_ocor_consulta_com_cadastro.php" in frame.url and "fil" not in frame.url:
                f_grid = frame
                break
        
        if not f_grid:
            f_grid = tco_page
            
        await f_grid.screenshot(path=os.path.join(WORKSPACE, 'debug_cad_resultados_tco.png'))
        
        # 4. Exportação -> XLS
        log("Disparando exportação XLS via JavaScript direta...")
        try:
            # Em ScriptCase, nm_gp_move eh a funcao padrao para exportacao.
            # Chamamos via JS para evitar problemas de visibilidade/scroll do botao.
            await f_grid.evaluate("nm_gp_move('xls', '0')")
            log("Comando nm_gp_move('xls', '0') enviado.")
        except Exception as e:
            log(f"Erro ao disparar exportação via JS: {e}. Tentando clique manual...")
            try:
                await f_grid.click('#xls_top', timeout=5000, force=True)
            except:
                await f_grid.click('text=XLS', timeout=5000, force=True)

        # 5. Baixar
        log("Aguardando janela de download (pop-up do ScriptCase)...")
        try:
            # O ScriptCase costuma abrir uma nova janela que mostra o progresso e depois o botao Baixar
            async with context.expect_page(timeout=90000) as download_page_info:
                # O comando anterior deve ter disparado isso
                pass
            
            download_page = await download_page_info.value
            await download_page.wait_for_load_state()
            log("Janela de download/processamento aberta.")
            
            # Aguarda o link "Baixar" aparecer (pode demorar dependendo do tamanho do TCO)
            log("Aguardando botão 'Baixar' aparecer na nova janela...")
            await download_page.wait_for_selector('text=Baixar, #id_img_bt_baixar', timeout=60000)
            
            async with download_page.expect_download() as download_info:
                try:
                    await download_page.click('text=Baixar', timeout=10000)
                except:
                    await download_page.click('#id_img_bt_baixar', timeout=10000)
            
            download = await download_info.value
            path_xls = os.path.join(DESTINO_DIR, "TCO 2026.xls")
            await download.save_as(path_xls)
            log(f"✅ TCO baixado com sucesso: {path_xls}")
            
        except Exception as e:
            log(f"Aviso: Não detectei pop-up ou erro no download: {e}")
            log("Buscando link de download na página atual como fallback...")
            try:
                async with tco_page.expect_download(timeout=10000) as download_info:
                    await f_grid.click('text=Baixar')
                download = await download_info.value
                path_xls = os.path.join(DESTINO_DIR, "TCO 2026.xls")
                await download.save_as(path_xls)
                log(f"✅ TCO baixado via fallback final: {path_xls}")
            except:
                log(f"Erro final: Não foi possível baixar o arquivo.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(download_tco_cad())
