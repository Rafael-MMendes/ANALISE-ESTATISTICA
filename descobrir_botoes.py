import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

async def main():
    USER = os.getenv('NEAC_USER')
    PASS = os.getenv('NEAC_PASS')
    
    if not USER or not PASS or USER == 'COLOQUE_SEU_CPF_OU_LOGIN_AQUI':
        print("\n[!] ERRO: Olá Policial, antes de rodar, abra o arquivo '.env' e coloque seu Login e Senha!")
        return

    print("Iniciando navegador Chrome para Mapeamento Institucional...")
    async with async_playwright() as p:
        # headless=False para rodar fisicamente e vc ver a injeção em tempo real!
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        
        print("Lendo a página de Login do Pentaho...")
        await page.goto('https://neac.seguranca.al.gov.br/pentaho/Login', wait_until='domcontentloaded', timeout=60000)
        
        print("Aguardando carregamento da caixinha de login...")
        await page.wait_for_selector('#j_username', timeout=60000)
        
        print("Injetando Senha Secreta...")
        await page.fill('#j_username', USER)
        await page.fill('#j_password', PASS)
        
        print("Apertando o botão ENTER no teclado para logar...")
        # A página usa um input de submit disfarçado, então um Enter direto resolve!
        await page.keyboard.press('Enter')
        
        print("Aguardando carregamento da interface interna do Estado (15 segundos para os JSS subirem)...")
        await page.wait_for_timeout(15000) 
        
        print("Capturando Árvore de Botões e Pastas (DOM) da tela...")
        html = await page.content()
        
        # O Pentaho 100% embute a página de ferramentas dentro de iFrames aninhados (mantle)
        frames_html = ""
        for i, frame in enumerate(page.frames):
            try:
                content = await frame.content()
                frames_html += f"\n\n<!-- ======== IFRAME ID: {i} NOME: {frame.name} ======== -->\n"
                frames_html += content
            except Exception as e:
                pass

        with open('dom_pentaho.txt', 'w', encoding='utf-8') as f:
            f.write(html)
            f.write("\n\n\n----------------- CAMADA 2 (IFRAMES SUB-JANELAS) ----------------\n\n\n")
            f.write(frames_html)
            
        print("\n==============================================")
        print("SUCESSO! Estrutura salva no arquivo 'dom_pentaho.txt'.")
        print("O robô-sonda cumpriu seu papel e catalogou todo o Pentaho no bloco de notas.")
        print("Pode voltar na Inteligência Artificial e avisar: 'Script rodou, analise o texto'.")
        print("==============================================\n")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
