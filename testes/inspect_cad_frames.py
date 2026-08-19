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
        url_ocor = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_grid_tb_ocor_consulta_com_cadastro/cad_grid_tb_ocor_consulta_com_cadastro.php'
        await page.goto(url_ocor, wait_until='domcontentloaded')
        
        f_filtros = None
        for f in page.frames:
            if "fil" in f.url.lower():
                f_filtros = f
                break
        if not f_filtros: f_filtros = page
        
        await f_filtros.select_option('#SC_data_cond', value='CY')
        await f_filtros.select_option('#SC_unid_id_orga_fk_orig', value='2##@@POLÍCIA MILITAR')
        await f_filtros.locator('#SC_unid_id_orga_fk_orig option[value="2##@@POLÍCIA MILITAR"]').dblclick()
        
        await f_filtros.wait_for_selector('#SC_despc_id_orga_unid_fk_orig option', timeout=15000)
        options = await f_filtros.locator('#SC_despc_id_orga_unid_fk_orig option').all()
        val_9bpm = None
        for opt in options:
            if "9º BPM" in await opt.inner_text():
                val_9bpm = await opt.get_attribute('value')
                break
        if val_9bpm:
            await f_filtros.select_option('#SC_despc_id_orga_unid_fk_orig', value=val_9bpm)
            await f_filtros.locator(f'#SC_despc_id_orga_unid_fk_orig option[value="{val_9bpm}"]').dblclick()
            
        await f_filtros.select_option('#SC_ocor_id_ocor_grup_fk_orig', label='LEI MARIA DA PENHA')
        await f_filtros.locator('#SC_ocor_id_ocor_grup_fk_orig option').filter(has_text='LEI MARIA DA PENHA').dblclick()
        
        print("Clicando em Pesquisar...", flush=True)
        await f_filtros.click('#sc_b_pesq_top', timeout=5000)
        
        for i in range(1, 15):
            await asyncio.sleep(2)
            print(f"\n[Check {i}] Total frames: {len(page.frames)}")
            for j, f in enumerate(page.frames):
                print(f"  Frame {j}: name='{f.name}', url='{f.url[:80]}'")
                xls_count = await f.locator('#sc_b_xls_top, #sc_b_xls_bot').count()
                if xls_count > 0:
                    print(f"    -> Botão XLS ENCONTRADO no frame {j} (total: {xls_count})!")
                    
        await page.screenshot(path='debug_maria_grid.png')
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
