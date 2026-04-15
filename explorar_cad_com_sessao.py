import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    WORKSPACE = os.path.dirname(os.path.abspath(__file__))
    SESSION_FILE = 'cad_session.json'
    url = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/'
    
    if not os.path.exists(SESSION_FILE):
        print(f"Erro: {SESSION_FILE} não encontrado. Rode o login_cad_persistente.py primeiro.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Carregando a sessão salva
        context = await browser.new_context(storage_state=SESSION_FILE, viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
        page = await context.new_page()
        
        print("Acessando dashboard com sessão salva...")
        await page.goto(url) # Redireciona para home se logado
        await asyncio.sleep(5)
        
        # Tirar print da home para confirmar login
        await page.screenshot(path=os.path.join(WORKSPACE, 'debug_cad_home_reentrada.png'))
        
        # Tenta clicks e mapeia links
        print("Explorando Paineis e Relatórios...")
        paineis_btn = page.get_by_text("Paineis e Relatórios")
        if await paineis_btn.is_visible():
            await paineis_btn.click()
            await asyncio.sleep(5)
            await page.screenshot(path=os.path.join(WORKSPACE, 'debug_cad_paineis.png'))
            # Lista links visíveis no menu/página
            links = await page.locator('a, button').all_inner_texts()
            print(f"Links em Paineis: {[l for l in links if l.strip()][:30]}")
        
        print("Explorando Analista de Dados...")
        # Volta pra home ou clica direto se estiver no topo
        analista_btn = page.get_by_text("Analista de Dados")
        if await analista_btn.is_visible():
            await analista_btn.click()
            await asyncio.sleep(5)
            await page.screenshot(path=os.path.join(WORKSPACE, 'debug_cad_analista.png'))
            links = await page.locator('a, button').all_inner_texts()
            print(f"Links em Analista: {[l for l in links if l.strip()][:30]}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
