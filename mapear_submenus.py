import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

async def main():
    USER = os.getenv('CAD_USER')
    PASS = os.getenv('CAD_PASS')
    WORKSPACE = os.path.dirname(os.path.abspath(__file__))
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
        
        # O robô vai precisar do token de novo se a sessão não persistir, 
        # mas como rodamos agora pouco, talvez a sessão já esteja ativa no IP?
        # Provavelmente vai pedir token. Vou simular a espera.
        print("Aguardando possível tela de token ou dashboard...")
        try:
            # Se aparecer token, o mapeamento falha aqui (pois é interativo).
            # No entanto, se o login for direto (cookies/IP), ele continua.
            # Vou usar um timeout curto para o token e longo para o dashboard.
            await page.wait_for_selector('#token', timeout=5000)
            print("Pausando para Token (necessário novo token)...")
            # Aqui no script de mapeamento NÃO queremos interativo, queremos apenas ver se entra.
            # Se pedir token, o usuário terá que rodar o interativo de novo.
            return
        except:
            print("Não pediu token (ou já passou). Prosseguindo...")
        
        await page.wait_for_selector('text=Paineis e Relatórios', timeout=20000)
        
        # Explorar Paineis e Relatórios
        print("Abrindo Paineis e Relatórios...")
        await page.click('text=Paineis e Relatórios')
        await asyncio.sleep(3)
        await page.screenshot(path=os.path.join(WORKSPACE, 'debug_cad_paineis.png'))
        
        # Explorar Analista de Dados
        print("Abrindo Analista de Dados...")
        await page.click('text=Analista de Dados')
        await asyncio.sleep(3)
        await page.screenshot(path=os.path.join(WORKSPACE, 'debug_cad_analista.png'))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
