import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navegando para NEAC Pentaho...")
        await page.goto('https://neac.seguranca.al.gov.br/pentaho/Login', wait_until='networkidle')
        await page.wait_for_timeout(2000)
        
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        inputs = []
        for inp in soup.find_all('input'):
            input_info = {
                'id': inp.get('id', ''),
                'name': inp.get('name', ''),
                'type': inp.get('type', ''),
                'class': inp.get('class', [])
            }
            inputs.append(input_info)
            
        buttons = []
        for btn in soup.find_all(['button', 'input']):
            if btn.name == 'button' or btn.get('type') in ['submit', 'button']:
                btn_info = {
                    'text': btn.text.strip() if btn.name == 'button' else btn.get('value', ''),
                    'id': btn.get('id', ''),
                    'name': btn.get('name', ''),
                    'type': btn.get('type', '')
                }
                buttons.append(btn_info)

        print("--- INPUTS DE TEXTO/SENHA ---")
        for i in inputs:
            if i['type'] in ['text', 'password', '']:
                print(i)
                
        print("\n--- BOTOES ---")
        for b in buttons:
            print(b)
            
        await browser.close()

asyncio.run(main())
