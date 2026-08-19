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
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    
    print("1. Login HTTP inicial...", flush=True)
    session.get('https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/', verify=False, timeout=15)
    session.post('https://analisacad.seguranca.al.gov.br/app/cad/cad_blank_validar_login/cad_blank_validar_login.php', data={'login': USER, 'senha': PASS}, verify=False, timeout=15)
    
    cookies = [
        {
            "name": k,
            "value": v,
            "domain": "analisacad.seguranca.al.gov.br",
            "path": "/"
        }
        for k, v in session.cookies.get_dict().items()
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        print("2. Acessando cad_grid_tb_ocor_consulta_com_cadastro...", flush=True)
        url_ocor = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_grid_tb_ocor_consulta_com_cadastro/cad_grid_tb_ocor_consulta_com_cadastro.php'
        await page.goto(url_ocor, wait_until='domcontentloaded')
        
        f_filtros = None
        for f in page.frames:
            if "fil" in f.url.lower():
                f_filtros = f
                break
        if not f_filtros: f_filtros = page
        
        print("3. Selecionando Este Ano e POLÍCIA MILITAR...", flush=True)
        await f_filtros.select_option('#SC_data_cond', value='CY')
        await f_filtros.select_option('#SC_unid_id_orga_fk_orig', value='2##@@POLÍCIA MILITAR')
        await f_filtros.locator('#SC_unid_id_orga_fk_orig option[value="2##@@POLÍCIA MILITAR"]').dblclick()
        
        print("4. Aguardando 9º BPM...", flush=True)
        await f_filtros.wait_for_selector('#SC_despc_id_orga_unid_fk_orig option', timeout=15000)
        options = await f_filtros.locator('#SC_despc_id_orga_unid_fk_orig option').all()
        val_9bpm = None
        for opt in options:
            txt = await opt.inner_text()
            if "9º BPM" in txt:
                val_9bpm = await opt.get_attribute('value')
                break
        print(f"Valor 9º BPM: {val_9bpm}", flush=True)
        if val_9bpm:
            await f_filtros.select_option('#SC_despc_id_orga_unid_fk_orig', value=val_9bpm)
            await f_filtros.locator(f'#SC_despc_id_orga_unid_fk_orig option[value="{val_9bpm}"]').dblclick()
            
        print("5. Selecionando LEI MARIA DA PENHA...", flush=True)
        await f_filtros.select_option('#SC_ocor_id_ocor_grup_fk_orig', label='LEI MARIA DA PENHA')
        await f_filtros.locator('#SC_ocor_id_ocor_grup_fk_orig option').filter(has_text='LEI MARIA DA PENHA').dblclick()
        
        print("6. Clicando em Pesquisar...", flush=True)
        t_pesq = time.time()
        await f_filtros.click('#sc_b_pesq_top', timeout=5000)
        
        print("7. Aguardando grid...", flush=True)
        f_grid = None
        for _ in range(40):
            for f in page.frames:
                if "grid" in f.url.lower() and "fil" not in f.url.lower():
                    f_grid = f
                    break
            if f_grid:
                if await f_grid.locator('#sc_b_xls_top, #sc_b_xls_bot').first.is_visible():
                    print(f"Grid carregado em {time.time()-t_pesq:.2f}s!", flush=True)
                    break
            await asyncio.sleep(1)
            
        if not f_grid: f_grid = page
        
        print("8. Clicando no botão XLS e capturando popup...", flush=True)
        async with context.expect_page(timeout=20000) as dl_page_info:
            try:
                await f_grid.locator('#sc_b_xls_top').click(timeout=5000)
            except:
                await f_grid.evaluate("nm_gp_move('xls', '0')")
                
        dl_page = await dl_page_info.value
        await dl_page.wait_for_load_state('domcontentloaded')
        print(f"Janela de download aberta: '{await dl_page.title()}'", flush=True)
        
        btn = dl_page.locator('text=Baixar, text=DOWNLOAD, #id_img_bt_baixar').first
        await btn.wait_for(state='visible', timeout=40000)
        print("Botão Baixar visível! Disparando download...", flush=True)
        
        async with dl_page.expect_download(timeout=30000) as dl_info:
            await btn.click()
        download = await dl_info.value
        
        path_out = os.path.join("dados", "2026", "Maria da Penha 2026.xls")
        os.makedirs(os.path.dirname(path_out), exist_ok=True)
        await download.save_as(path_out)
        print(f"✅ Maria da Penha salva com sucesso ({os.path.getsize(path_out)} bytes)!", flush=True)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
