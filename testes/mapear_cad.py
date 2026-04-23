import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    WORKSPACE = os.path.dirname(os.path.abspath(__file__))
    url = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720}, ignore_https_errors=True)
        page = await context.new_page()
        
        print(f"Acessando {url}...")
        await page.goto(url, wait_until='networkidle')
        await asyncio.sleep(5) # Esperar carregamento de scripts
        
        await page.screenshot(path=os.path.join(WORKSPACE, 'debug_cad_login.png'))
        print("Screenshot de login salvo.")
        
        # Identificar inputs
        inputs = await page.locator('input').all()
        for i, inp in enumerate(inputs):
            name = await inp.get_attribute('name')
            id_ = await inp.get_attribute('id')
            type_ = await inp.get_attribute('type')
            placeholder = await inp.get_attribute('placeholder')
            print(f"Input {i}: id={id_}, name={name}, type={type_}, placeholder={placeholder}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
