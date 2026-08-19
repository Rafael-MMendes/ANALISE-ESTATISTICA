import asyncio
import os
import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright
import urllib.parse

load_dotenv()

async def main():
    USER = os.getenv('NEAC_USER')
    PASS = os.getenv('NEAC_PASS')
    
    captured_requests = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
        page = await context.new_page()
        
        async def on_request(request):
            url = request.url
            if any(k in url for k in ["report", "content", "api", "prpt", "j_spring_security", "ViewReport", "plugin"]):
                info = {
                    "method": request.method,
                    "url": url,
                    "post_data": request.post_data,
                    "headers": dict(request.headers)
                }
                captured_requests.append(info)
                print(f"\n[NETWORK REQ] {request.method} {url[:120]}...")
                if request.post_data:
                    print(f"   -> Post Data: {request.post_data[:200]}")
        
        async def on_response(response):
            url = response.url
            if any(k in url for k in ["report", "content", "prpt", "ViewReport", "j_spring_security"]):
                content_type = response.headers.get("content-type", "")
                print(f"[NETWORK RES] {response.status} {content_type} ({url[:100]}...)")
        
        page.on("request", on_request)
        page.on("response", on_response)
        
        print("1. Acessando login...")
        await page.goto('https://neac.seguranca.al.gov.br/pentaho/Login', wait_until='domcontentloaded')
        await page.fill('#j_username', USER)
        await page.fill('#j_password', PASS)
        await page.keyboard.press('Enter')
        await asyncio.sleep(8)
        
        print("2. Abrindo Procurar Arquivos...")
        home_frame = page.frame_locator('iframe[id="home.perspective"]')
        await home_frame.get_by_text("Procurar Arquivos").click()
        await asyncio.sleep(4)
        
        print("3. Abrindo CVLI -> 03.0...")
        nav_frame = page.frame_locator('iframe[id="browser.perspective"]')
        await nav_frame.get_by_text("4_RISP", exact=False).first.dblclick(force=True)
        await asyncio.sleep(2)
        await nav_frame.get_by_text("CVLI", exact=False).first.click(force=True)
        await asyncio.sleep(2)
        await nav_frame.get_by_text("03.0", exact=False).first.dblclick(force=True)
        await asyncio.sleep(8)
        
        print("4. Procurando frame do relatório...")
        report_frame = None
        for frame in page.frames:
            try:
                if await frame.get_by_text("View Report", exact=False).count() > 0:
                    report_frame = frame
                    print(f"   Frame encontrado: {frame.url}")
                    break
            except: pass
            
        if report_frame:
            # Seleciona 2026 e Excel
            selects = await report_frame.locator('select').all()
            print(f"Total selects no frame: {len(selects)}")
            for i, sel in enumerate(selects):
                txt = await sel.inner_text()
                if "2026" in txt:
                    await sel.select_option("2026")
                    print(f"   Select {i} -> 2026 selecionado")
                elif "Excel" in txt:
                    await sel.select_option("Excel")
                    print(f"   Select {i} -> Excel selecionado")
            
            await asyncio.sleep(2)
            print("5. Clicando em View Report...")
            btn = report_frame.get_by_text("View Report", exact=True)
            await btn.click(force=True)
            await asyncio.sleep(10)
        
        await browser.close()
        
    print("\n" + "="*60)
    print(f"TOTAL DE REQUISIÇÕES CAPTURADAS: {len(captured_requests)}")
    for r in captured_requests:
        print(f"\n--- {r['method']} {r['url']} ---")
        if r['post_data']:
            print(f"Payload: {r['post_data']}")

if __name__ == "__main__":
    asyncio.run(main())
