import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

async def main():
    USER = os.getenv('CAD_USER')
    PASS = os.getenv('CAD_PASS')
    WORKSPACE = os.path.dirname(os.path.abspath(__file__))
    SESSION_FILE = 'cad_session.json'
    url = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
        page = await context.new_page()
        
        print("Realizando login...")
        await page.goto(url)
        await page.fill('#cpf', USER)
        await page.fill('#senha', PASS)
        await page.click('input[type="submit"]')
        
        try:
            await page.wait_for_selector('#token', timeout=10000)
            print("\n🔑 TOKEN REQUERIDO PELO CAD!")
            token = input("Digite o Token do CAD: ").strip()
            await page.fill('#token', token)
            await page.click('input[type="submit"]')
        except:
            print("Token não solicitado ou timeout.")

        print("Aguardando carregamento final do Dashboard...")
        await page.wait_for_selector('text=Paineis e Relatórios', timeout=30000)
        
        # Salva o estado da sessão (cookies, localStorage, etc)
        await context.storage_state(path=SESSION_FILE)
        print(f"✅ Sessão salva em {SESSION_FILE}!")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
