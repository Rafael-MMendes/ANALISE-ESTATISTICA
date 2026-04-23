import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

async def main():
    USER = os.getenv('NEAC_USER')
    PASS = os.getenv('NEAC_PASS')
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
        page = await context.new_page()
        
        await page.goto('https://neac.seguranca.al.gov.br/pentaho/Login', wait_until='domcontentloaded')
        await page.fill('#j_username', USER)
        await page.fill('#j_password', PASS)
        await page.keyboard.press('Enter')
        await asyncio.sleep(10)
        
        home_frame = page.frame_locator('iframe[id="home.perspective"]')
        await home_frame.get_by_text("Procurar Arquivos").click()
        await asyncio.sleep(5)
        
        nav_frame = page.frame_locator('iframe[id="browser.perspective"]')
        await nav_frame.get_by_text("PMAL", exact=False).first.dblclick(force=True)
        await asyncio.sleep(2)
        await nav_frame.get_by_text("CAD", exact=False).first.dblclick(force=True)
        await asyncio.sleep(2)
        await nav_frame.get_by_text("Prisões", exact=False).first.click(force=True)
        await asyncio.sleep(2)
        await nav_frame.get_by_text("04.2", exact=False).first.dblclick(force=True)
        await asyncio.sleep(10)
        
        report_frame = page.frame_locator('iframe[name="frame_0"], iframe[id="frame_0"]')
        
        # Selecionar OPM
        await report_frame.locator('select').nth(0).select_option(label="9º BPM")
        print("OPM 9º BPM selecionado.")
        
        # Selecionar ANO
        await report_frame.locator('select').nth(1).select_option(label="2026")
        print("ANO 2026 selecionado.")
        
        await asyncio.sleep(5) # Esperar carregar meses
        
        months = await report_frame.locator('select').nth(2).locator('option').all_inner_texts()
        print(f"Meses disponíveis após seleção: {months}")
        
        years = await report_frame.locator('select').nth(1).locator('option').all_inner_texts()
        print(f"Anos disponíveis: {years}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
