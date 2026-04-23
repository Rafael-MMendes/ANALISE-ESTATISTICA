import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

async def main():
    USER = os.getenv('NEAC_USER')
    PASS = os.getenv('NEAC_PASS')
    
    if not USER or not PASS:
        print("ERRO: Credenciais ausentes.")
        return

    print("Iniciando navegador em modo Invisível (Headless=True)...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        
        print("Logando...")
        await page.goto('https://neac.seguranca.al.gov.br/pentaho/Login', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_selector('#j_username', timeout=60000)
        await page.fill('#j_username', USER)
        await page.fill('#j_password', PASS)
        await page.keyboard.press('Enter')
        
        print("Aguardando painel principal...")
        await page.wait_for_timeout(10000)
        
        print("Buscando o Frame Central da Home...")
        home_frame = page.frame_locator('iframe[id="home.perspective"]')
        
        print("Clicando no botão Verde 'Procurar Arquivos'...")
        try:
            await home_frame.locator('text="Procurar Arquivos"').click()
            await page.wait_for_timeout(5000)
            
            print("Entrando no Frame de Navegação (browser.perspective)...")
            browser_frame = page.frame_locator('iframe[id="browser.perspective"]')
            
            # Expandir 4_RISP
            print("Expandindo 4_RISP (dblclick)...")
            await browser_frame.locator('text="4_RISP"').first.dblclick(force=True)
            await page.wait_for_timeout(3000)
            WORKSPACE = os.path.dirname(os.path.abspath(__file__))
            await page.screenshot(path=os.path.join(WORKSPACE, 'media__step1.png'), full_page=True)
            
            # Selecionar a pasta CVLI para popular o lado direito (Files List)
            print("Selecionando pasta CVLI (click simples)...")
            await browser_frame.locator('text="CVLI"').first.click(force=True)
            await page.wait_for_timeout(3000)
            WORKSPACE = os.path.dirname(os.path.abspath(__file__))
            await page.screenshot(path=os.path.join(WORKSPACE, 'media__step2.png'), full_page=True)
            
            print("Dando Duplo Clique no Arquivo 03.0 - Relação Nominal...")
            # Usar get_by_text com correspondência parcial é imune a quebras de DOM ou \xa0 (non-breaking spaces)
            await browser_frame.get_by_text("03.0 - Relação Nominal (Ano)", exact=False).first.dblclick()
            
            print("Aguardando carregamento da aba do relatório...")
            await page.wait_for_timeout(10000)
            
            # Tira screenshot do relatorio aberto
            screenshot_path = os.path.join(WORKSPACE, 'media__pentaho_report.png')
            await page.screenshot(path=screenshot_path, full_page=True)
            
            print("Procurando o botão 'View Report' dinamicamente nos Frames...")
            target_frame = None
            for i, frame in enumerate(page.frames):
                try:
                    count = await frame.get_by_text("View Report", exact=False).count()
                    tipo_saida = await frame.get_by_text("Tipo de", exact=False).count()
                    ano = await frame.get_by_text("ANO", exact=False).count()
                    if count > 0 or tipo_saida > 0 or ano > 0:
                        print(f"!!! ENCONTRADO NO FRAME {i} NOME: {frame.name} URL: {frame.url} (View Report: {count}, Tipo de Saida: {tipo_saida}, ANO: {ano}) !!!")
                        target_frame = frame
                        
                        # Vamos tentar ver o código HTML e salvar
                        content = await frame.content()
                        with open('dom_report_frame.html', 'w', encoding='utf-8') as f:
                            f.write(content)
                except Exception as ex:
                    print(f"Erro no frame {i}: {ex}")
            
            if target_frame:
                print("Preenchendo formulário...")
                
                # O Select 0 é o ANO
                ano_select = target_frame.locator('select').nth(0)
                await ano_select.select_option("2025")
                
                # O Select 1 é o TIPO DE SAÍDA
                saida_select = target_frame.locator('select').nth(1)
                await saida_select.select_option("Excel")
                
                print("Aguardando carregamento interno (Dojo refresh)...")
                await page.wait_for_timeout(3000)
                
                print("Iniciando escuta do download e clicando em View Report...")
                # O botão é "View Report"
                btn_view = target_frame.get_by_text("View Report", exact=True)
                
                async with page.expect_download(timeout=120000) as download_info:
                    await btn_view.click(force=True)
                
                download = await download_info.value
                
                # Garantindo que a variavel de downloads seja salva
                save_path = os.path.join(WORKSPACE, download.suggested_filename)
                await download.save_as(save_path)
                
                print(f"!!! SUCESSO !!! Download completo salvo em: {save_path}")
            else:
                print("Não achei o form.")
                
        except Exception as e:
            print(f"Erro principal: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("Fechando navegador...")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
