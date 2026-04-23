import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

async def main():
    USER = os.getenv('NEAC_USER')
    PASS = os.getenv('NEAC_PASS')
    
    # Path para o brain
    WORKSPACE = os.path.dirname(os.path.abspath(__file__))
    screenshot_path = os.path.join(WORKSPACE, 'media__pentaho_desktop.png')

    async with async_playwright() as p:
        # Usando window-size de um PC normal para não cortar frames
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
        page = await context.new_page()
        
        await page.goto('https://neac.seguranca.al.gov.br/pentaho/Login', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_selector('#j_username', timeout=60000)
        await page.fill('#j_username', USER)
        await page.fill('#j_password', PASS)
        await page.keyboard.press('Enter')
        
        await page.wait_for_timeout(10000)
        
        # Tira Screenshot do dashboard base
        await page.screenshot(path=screenshot_path, full_page=True)
        print("Mapeamento visual concluido e salvo!")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
