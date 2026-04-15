import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

async def main():
    USER = os.getenv('CAD_USER')
    PASS = os.getenv('CAD_PASS')
    url_login = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
        page = await context.new_page()
        
        print("Login...")
        await page.goto(url_login)
        await page.fill('#cpf', USER)
        await page.fill('#senha', PASS)
        await page.click('input[type="submit"]')
        
        try:
            await page.wait_for_selector('#token', timeout=5000)
            token = input("TOKEN: ").strip()
            await page.fill('#token', token)
            await page.click('input[type="submit"]')
        except: pass

        await page.wait_for_selector('text=Pesquisar', timeout=30000)
        await page.click('text=Pesquisar')
        await asyncio.sleep(2)
        
        # Encontrar o frame do menu se necessário
        frames = page.frames
        frame_menu = page
        for f in frames:
            if "menu" in f.url.lower():
                frame_menu = f
                break
        
        print("Abrindo Pesquisar Ocorrências...")
        async with context.expect_page() as new_page_info:
            target = frame_menu.get_by_text("Pesquisar Ocorrências")
            if await target.count() == 0:
                # Tenta em todos os frames
                for f in frames:
                    try:
                        t = f.get_by_text("Pesquisar Ocorrências")
                        if await t.count() > 0:
                            await t.click()
                            break
                    except: continue
            else:
                await target.click()
        
        tco_page = await new_page_info.value
        await tco_page.wait_for_load_state()
        await asyncio.sleep(5)
        
        # Mapear frames na nova aba
        tco_frames = tco_page.frames
        print(f"Frames na aba de pesquisa: {len(tco_frames)}")
        
        for i, f in enumerate(tco_frames):
            try:
                html = await f.content()
                filename = f"debug_cad_tco_frame_{i}.html"
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(html)
                print(f"✅ Arquivo salvo: {filename} (URL: {f.url[:50]}...)")
            except Exception as e:
                print(f"❌ Erro ao salvar frame {i}: {e}")
            
        print("\n" + "#"*50)
        print("🎉 RAIO-X CONCLUÍDO COM SUCESSO!")
        print("Agora avise o assistente no chat para ele ler os arquivos.")
        print("#"*50 + "\n")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
