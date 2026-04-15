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
        selects = await report_frame.locator('select').all()
        print(f"Total de selects: {len(selects)}")
        
        for i, s in enumerate(selects):
            options = await s.locator('option').all_inner_texts()
            print(f"Select {i} opções: {options[:10]}... (Total: {len(options)})")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
