import asyncio
import os
from playwright.async_api import async_playwright

async def explorar_armas():
    # Obtém a sessão salva
    session_file = 'cad_session.json'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
        
        # Carrega os cookies
        if os.path.exists(session_file):
            import json
            with open(session_file, 'r') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            print("Cookies de sessão carregados.")
        
        page = await context.new_page()
        print("Acessando CAD...")
        await page.goto('https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/')
        await asyncio.sleep(3)
        
        print("Aguardando Dashboard...")
        try:
            await page.wait_for_selector('text=Pesquisar', timeout=15000)
        except Exception as e:
            print("Parece que a sessão expirou. Você precisará gerar uma nova sessão rodando: python explorar_cad_com_sessao.py primeiro, e fazendo login.")
            await browser.close()
            return
            
        print("Clicando em Pesquisar...")
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

        print("Localizando o card 'Pesquisar Armas na Base do CAD'...")
        async with context.expect_page() as new_page_info:
            if target_frame is not None:
                await target_frame.get_by_text("Pesquisar Armas na Base do CAD").first.click()
            else:
                await page.get_by_text("Pesquisar Armas na Base do CAD").first.click()
                
        r_page = await new_page_info.value
        await r_page.wait_for_load_state()
        print("Nova aba aberta. Aguardando iframe de filtros...")
        await asyncio.sleep(8)
        
        # Localiza o frame de filtros
        f_filtros = None
        for frame in r_page.frames:
            if "fil.php" in frame.url or "fil" in frame.url.lower():
                f_filtros = frame
                break
        if not f_filtros: f_filtros = r_page
        
        html = await f_filtros.content()
        with open('debug_cad_armas_frame.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        await f_filtros.screenshot(path='debug_cad_armas_tela.png')
        print("HTML salvo em debug_cad_armas_frame.html")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(explorar_armas())
