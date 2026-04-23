import asyncio
import os
import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

async def explorar_veiculos():
    USER = os.getenv('CAD_USER')
    PASS = os.getenv('CAD_PASS')
    WORKSPACE = os.path.dirname(os.path.abspath(__file__))
    
    url_login = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
        page = await context.new_page()
        
        log(f"Acessando login CAD...")
        await page.goto(url_login, wait_until='domcontentloaded', timeout=90000)
        
        try:
            await page.wait_for_selector('#cpf', timeout=30000)
            await page.fill('#cpf', USER)
            await page.fill('#senha', PASS)
            await page.click('input[type="submit"]')
        except Exception as e:
            log(f"Erro: {e}")
            
        try:
            await page.wait_for_selector('#token', timeout=20000)
            token = input("Digite o Token do CAD: ").strip()
            await page.fill('#token', token)
            await page.click('input[type="submit"]')
        except:
            pass

        log("Aguardando Dashboard...")
        await page.wait_for_selector('text=Pesquisar', timeout=40000)
        
        log("Navegando: Pesquisar > Pesquisar Veículo na base do CAD...")
        await page.click('text=Pesquisar')
        await asyncio.sleep(4)
        
        target_frame = None
        for f in page.frames:
            try:
                if await f.get_by_text("Pesquisar Veículos na Base do CAD").is_visible():
                    target_frame = f
                    break
            except: continue

        async with context.expect_page() as new_page_info:
            if target_frame is not None:
                await target_frame.get_by_text("Pesquisar Veículos na Base do CAD").first.click()
            else:
                await page.get_by_text("Pesquisar Veículos na Base do CAD").first.click()
        
        v_page = await new_page_info.value
        await v_page.wait_for_load_state()
        log("Nova aba aberta.")
        await asyncio.sleep(5)
        
        # Encontrar iframe de filtros
        f_filtros = None
        for frame in v_page.frames:
            # Geralmente termina em _fil.php ou similar
            if "fil.php" in frame.url or "fil" in frame.url.lower():
                f_filtros = frame
                break
        
        if not f_filtros: f_filtros = v_page
        
        html = await f_filtros.content()
        path = os.path.join(WORKSPACE, 'debug_cad_veiculos_frame.html')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
            
        await f_filtros.screenshot(path=os.path.join(WORKSPACE, 'debug_cad_veiculos_tela.png'))
        log(f"HTML salvo em: {path}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(explorar_veiculos())
