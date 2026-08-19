import requests
import asyncio
import os
import sys
import io
import time
from dotenv import load_dotenv
from playwright.async_api import async_playwright
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

USER = os.getenv('CAD_USER')
PASS = os.getenv('CAD_PASS')

async def main():
    t_start = time.time()
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    
    print("=== FASE 1: COLETA HTTP DIRETA (Armas, Drogas, Veículos) ===", flush=True)
    session.get('https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/', verify=False, timeout=15)
    r_login = session.post('https://analisacad.seguranca.al.gov.br/app/cad/cad_blank_validar_login/cad_blank_validar_login.php', data={'login': USER, 'senha': PASS}, verify=False, timeout=15)
    
    def coletar_http(app_name, custom_filters, filename):
        t0 = time.time()
        url_app = f"https://analisacad.seguranca.al.gov.br/app/cad/{app_name}/{app_name}.php"
        r_form = session.get(url_app, verify=False, timeout=20)
        import bs4
        soup = bs4.BeautifulSoup(r_form.text, 'html.parser')
        form = soup.find('form', {'name': 'F1'})
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
        actions = [f.get('action') for f in soup_xls.find_all('form') if '.xls' in f.get('action', '')]
        if actions:
            f_url = "https://analisacad.seguranca.al.gov.br" + actions[0] if not actions[0].startswith('http') else actions[0]
            r_file = session.get(f_url, verify=False, timeout=35)
            out_p = os.path.join("dados", "2026", filename)
            os.makedirs(os.path.dirname(out_p), exist_ok=True)
            with open(out_p, 'wb') as f:
                f.write(r_file.content)
            print(f"✅ {filename} salvo ({len(r_file.content)} bytes em {time.time()-t0:.2f}s)!", flush=True)
            return True
        return False

    coletar_http('cad_grid_arma_boletim', {'ocor_dt_ocor_cond': 'CY', 'despc_id_orga_unid_fk': '32##@@9º BPM', 'despc_id_orga_unid_fk_dest': ['32##@@9º BPM']}, 'Armas 2026.xls')
    coletar_http('cad_grid_droga_boletim', {'ocor_dt_ocor_cond': 'CY', 'despc_id_orga_unid_fk': '32##@@9º BPM', 'despc_id_orga_unid_fk_dest': ['32##@@9º BPM']}, 'Drogas 2026.xls')
    coletar_http('cad_grid_tb_ocor_despc_envl_veic_pesquisa', {'ocor_dt_ocor_cond': 'CY', 'veic_id_orga_unid_fk': '32##@@9º BPM', 'veic_id_orga_unid_fk_dest': ['32##@@9º BPM'], 'veic_id_ocor_envl_veic_sitc_fk': '3##@@RECUPERADO', 'veic_id_ocor_envl_veic_sitc_fk_dest': ['3##@@RECUPERADO']}, 'Veiculo Recuperado 2026.xls')

    print("\n=== FASE 2: COLETA OCORRÊNCIAS (Maria da Penha, TCO, Mandados, Visitas) ===", flush=True)
    cookies = [{"name": k, "value": v, "domain": "analisacad.seguranca.al.gov.br", "path": "/"} for k, v in session.cookies.get_dict().items()]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        await page.goto('https://analisacad.seguranca.al.gov.br/app/cad/cad_blank_menu_respons/cad_blank_menu_respons.php', wait_until='domcontentloaded')
        
        async def coletar_ocorrencia_pw(tipo, filename, custom_action):
            t0 = time.time()
            print(f"\nIniciando {filename}...", flush=True)
            try:
                await page.click('text=Pesquisar', timeout=5000)
                await asyncio.sleep(1)
            except: pass
            
            target_frame = None
            for f in page.frames:
                try:
                    if await f.get_by_text("Pesquisar Ocorrências").is_visible():
                        target_frame = f
                        break
                except: continue
                
            if not target_frame: target_frame = page
            
            async with context.expect_page(timeout=30000) as new_page_info:
                await target_frame.get_by_text("Pesquisar Ocorrências").first.click()
            t_page = await new_page_info.value
            await t_page.wait_for_load_state('domcontentloaded')
            
            f_filtros = None
            for f in t_page.frames:
                if "fil" in f.url.lower():
                    f_filtros = f
                    break
            if not f_filtros: f_filtros = t_page
            
            # Filtros base
            await f_filtros.select_option('#SC_data_cond', value='CY')
            await f_filtros.select_option('#SC_unid_id_orga_fk_orig', value='2##@@POLÍCIA MILITAR')
            await f_filtros.locator('#SC_unid_id_orga_fk_orig option[value="2##@@POLÍCIA MILITAR"]').dblclick()
            
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
                
            # Ação customizada
            await custom_action(f_filtros)
            
            # Clica em Pesquisar
            await f_filtros.click('#sc_b_pesq_top', timeout=5000)
            
            # Aguarda Grid
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
                    except: pass
                await asyncio.sleep(1)
                
            if not f_grid: f_grid = t_page
            
            # Exporta XLS
            try:
                await f_grid.evaluate("nm_gp_move('xls', '0')")
            except:
                await f_grid.locator('#sc_b_xls_top').first.click()
                
            dl_page = None
            try:
                async with context.expect_page(timeout=30000) as dl_info: pass
                dl_page = await dl_info.value
            except:
                if len(context.pages) > 1: dl_page = context.pages[-1]
                
            if dl_page:
                await dl_page.wait_for_load_state('domcontentloaded')
                btn = dl_page.locator('text=Baixar, text=DOWNLOAD, #id_img_bt_baixar').first
                await btn.wait_for(state='visible', timeout=40000)
                async with dl_page.expect_download(timeout=30000) as dl_info:
                    await btn.click()
                download = await dl_info.value
                out_p = os.path.join("dados", "2026", filename)
                await download.save_as(out_p)
                print(f"✅ {filename} salvo com sucesso ({os.path.getsize(out_p)} bytes em {time.time()-t0:.2f}s)!", flush=True)
                await dl_page.close()
                
            await t_page.close()

        # 1. Maria da Penha
        async def act_maria(f):
            await f.select_option('#SC_ocor_id_ocor_grup_fk_orig', label='LEI MARIA DA PENHA')
            await f.locator('#SC_ocor_id_ocor_grup_fk_orig option').filter(has_text='LEI MARIA DA PENHA').dblclick()
        await coletar_ocorrencia_pw('maria', 'Maria da Penha 2026.xls', act_maria)

        # 2. TCO
        async def act_tco(f):
            await f.select_option('#SC_despc_id_ocor_despc_soluc_tipo_fk_orig', value='9##@@ELABOROU TCO (PM)')
            await f.locator('#SC_despc_id_ocor_despc_soluc_tipo_fk_orig option[value="9##@@ELABOROU TCO (PM)"]').dblclick()
        await coletar_ocorrencia_pw('tco', 'TCO 2026.xls', act_tco)

        # 3. Mandados
        async def act_mandados(f):
            await f.select_option('#SC_despc_id_ocor_despc_tip_fk_orig', value='6##@@CUMPRIMENTO DE MANDADO JUDICIAL')
            await f.locator('#SC_despc_id_ocor_despc_tip_fk_orig option[value="6##@@CUMPRIMENTO DE MANDADO JUDICIAL"]').dblclick()
        await coletar_ocorrencia_pw('mandados', 'Cumprimento de Mandados 2026.xls', act_mandados)

        # 4. Visitas
        async def act_visitas(f):
            await f.select_option('#SC_ocor_id_ocor_grup_fk_orig', label='OCORRÊNCIA SEM ILICITUDE')
            await f.locator('#SC_ocor_id_ocor_grup_fk_orig option').filter(has_text='OCORRÊNCIA SEM ILICITUDE').dblclick()
            await asyncio.sleep(1)
            for t in ["VISITA COMUNITÁRIA", "VISITA COMUNITÁRIA / MARIA DA PENHA", "VISITA PREVENTIVA"]:
                try:
                    await f.select_option('#SC_ocor_id_ocor_sgrup_fk_orig', label=t)
                    await f.locator('#SC_ocor_id_ocor_sgrup_fk_orig option').filter(has_text=t).dblclick()
                except: pass
        await coletar_ocorrencia_pw('visitas', 'Visita Comunitária 2026.xls', act_visitas)

        await browser.close()

    print(f"\n=======================================================")
    print(f"🏁 TODOS OS 7 RELATÓRIOS DO CAD COLETADOS EM {time.time()-t_start:.2f}s!")
    print(f"=======================================================")

if __name__ == "__main__":
    asyncio.run(main())
