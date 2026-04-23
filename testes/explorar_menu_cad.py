import asyncio
import os
from playwright.async_api import async_playwright

async def explorar_com_sessao():
    WORKSPACE = os.path.dirname(os.path.abspath(__file__))
    SESSION_FILE = os.path.join(WORKSPACE, 'cad_session.json')
    url_login = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/'
    
    if not os.path.exists(SESSION_FILE):
        print("Sessão não existe.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=SESSION_FILE, viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
        page = await context.new_page()
        
        print(f"Acessando login CAD usando sessão...")
        await page.goto(url_login, wait_until='domcontentloaded', timeout=90000)
        await asyncio.sleep(5)
        
        await page.wait_for_selector('text=Pesquisar', timeout=40000)
        
        print("Navegando: Pesquisar > Pesquisar Veículos na Base do CAD...")
        await page.click('text=Pesquisar')
        await asyncio.sleep(4)
        
        target_frame = None
        for f in page.frames:
            try:
                if await f.get_by_text("Pesquisar Veículos na Base do CAD").is_visible():
                    target_frame = f
                    break
            except: continue

        print("Localizando o card...")
        async with context.expect_page() as new_page_info:
            if target_frame is not None:
                await target_frame.get_by_text("Pesquisar Veículos na Base do CAD").first.click()
            else:
                await page.get_by_text("Pesquisar Veículos na Base do CAD", exact=False).first.click()
        
        v_page = await new_page_info.value
        await v_page.wait_for_load_state()
        print("Nova aba aberta.")
        await asyncio.sleep(8) # Espera carregar os iframes e filtros
        
        f_filtros = None
        for frame in v_page.frames:
            if "fil.php" in frame.url or "fil" in frame.url.lower():
                f_filtros = frame
                break
        
        if not f_filtros: f_filtros = v_page
        
        print("Capturando tela e HTML da nova aba...")
        html = await f_filtros.content()
        path = os.path.join(WORKSPACE, 'debug_cad_veiculos_pesquisa_frame.html')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
            
        await f_filtros.screenshot(path=os.path.join(WORKSPACE, 'debug_cad_veiculos_pesquisa_tela.png'), full_page=True)
        print(f"HTML salvo em: {path}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(explorar_com_sessao())
