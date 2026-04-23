import asyncio
import os
import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

async def main():
    USER = os.getenv('NEAC_USER')
    PASS = os.getenv('NEAC_PASS')
    
    WORKSPACE = os.path.dirname(os.path.abspath(__file__))
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
        page = await context.new_page()
        
        print("Acessando login...")
        await page.goto('https://neac.seguranca.al.gov.br/pentaho/Login', wait_until='domcontentloaded')
        await page.fill('#j_username', USER)
        await page.fill('#j_password', PASS)
        await page.keyboard.press('Enter')
        await asyncio.sleep(10)
        
        print("Abrindo Procurar Arquivos...")
        home_frame = page.frame_locator('iframe[id="home.perspective"]')
        await home_frame.get_by_text("Procurar Arquivos").click()
        await asyncio.sleep(5)
        
        # Screenshot da lista inicial de pastas
        browser_frame = page.frame_locator('iframe[id="browser.perspective"]')
        await page.screenshot(path=os.path.join(WORKSPACE, 'debug_pastas_1.png'))
        print("Screenshot 1 salvo.")
        
        # Tenta listar os textos visíveis no frame de navegação
        print("Capturando lista de pastas visíveis...")
        # O Pentaho 10 costuma usar .title para os nomes das pastas
        titles = await browser_frame.locator('.title').all_inner_texts()
        print(f"Pastas encontradas: {titles}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
