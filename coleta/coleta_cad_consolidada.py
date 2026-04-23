import asyncio
import os
import datetime
from dotenv import load_dotenv
import sys
import io
from playwright.async_api import async_playwright

# Força UTF-8 para stdout no Windows para evitar erros de charmap
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

async def handle_download(context, page, f_grid, filename, destino_dir):
    log(f"Iniciando exportação XLS para '{filename}'...")
    try:
        # Comando padrão ScriptCase para exportação
        await f_grid.evaluate("nm_gp_move('xls', '0')")
    except Exception as e:
        log(f"Erro ao disparar exportação JS: {e}. Tentando clique...")
        try: await f_grid.click('#sc_b_xls_top', timeout=5000)
        except: pass

    log("Aguardando janela de download...")
    try:
        async with context.expect_page(timeout=90000) as dl_page_info:
            pass
        dl_page = await dl_page_info.value
        await dl_page.wait_for_load_state()
        log("Aguardando botão 'Baixar' na nova janela...")
        await dl_page.wait_for_selector('text=Baixar, #id_img_bt_baixar', timeout=60000)
        async with dl_page.expect_download() as dl_info:
            try: await dl_page.click('text=Baixar', timeout=10000)
            except: await dl_page.click('#id_img_bt_baixar', timeout=10000)
        download = await dl_info.value
        path_xls = os.path.join(destino_dir, filename)
        await download.save_as(path_xls)
        log(f"✅ {filename} salvo com sucesso.")
        await dl_page.close()
        return True
    except Exception as e:
        log(f"Aviso: Fallback para download na aba atual... ({e})")
        try:
            async with page.expect_download(timeout=15000) as dl_info:
                try: await f_grid.click('text=Baixar', timeout=5000)
                except: await f_grid.click('#id_img_bt_baixar', timeout=5000)
            download = await dl_info.value
            path_xls = os.path.join(destino_dir, filename)
            await download.save_as(path_xls)
            log(f"✅ {filename} salvo com sucesso (fallback).")
            return True
        except Exception as e2:
            log(f"❌ Falha crítica no download de '{filename}': {e2}")
            return False

async def script_coleta_consolidada():
    import tkinter as tk
    from tkinter import messagebox

    def create_styled_window(title, width, height):
        root = tk.Tk()
        root.title(title)
        
        # Centralizar a janela
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        x = int((screen_w/2) - (width/2))
        y = int((screen_h/2) - (height/2))
        root.geometry(f"{width}x{height}+{x}+{y}")
        
        root.configure(bg="#1E1E1E")
        root.attributes('-topmost', True)
        root.resizable(False, False)
        return root

    def pedir_credenciais():
        root = create_styled_window("Login CAD", 350, 280)
        result = {"user": None, "pass": None}
        
        tk.Label(root, text="Autenticação do CAD", fg="#FFFFFF", bg="#1E1E1E", font=("Segoe UI", 16, "bold")).pack(pady=(20, 15))
        frame = tk.Frame(root, bg="#1E1E1E")
        frame.pack(fill="x", padx=30)
        
        tk.Label(frame, text="CPF:", fg="#CCCCCC", bg="#1E1E1E", font=("Segoe UI", 10)).pack(anchor="w")
        entry_user = tk.Entry(frame, font=("Segoe UI", 12), bg="#333333", fg="#FFFFFF", insertbackground="white", relief="flat")
        entry_user.pack(fill="x", pady=(2, 10), ipady=4)
        
        tk.Label(frame, text="Senha:", fg="#CCCCCC", bg="#1E1E1E", font=("Segoe UI", 10)).pack(anchor="w")
        entry_pass = tk.Entry(frame, font=("Segoe UI", 12), bg="#333333", fg="#FFFFFF", insertbackground="white", relief="flat", show="*")
        entry_pass.pack(fill="x", pady=(2, 15), ipady=4)
        
        def on_submit(event=None):
            result["user"] = entry_user.get().strip()
            result["pass"] = entry_pass.get().strip()
            if not result["user"] or not result["pass"]:
                messagebox.showwarning("Aviso", "Preencha todos os campos!", parent=root)
                return
            root.destroy()
            
        btn = tk.Button(root, text="Entrar", bg="#0066CC", fg="white", activebackground="#0052A3", activeforeground="white", font=("Segoe UI", 11, "bold"), relief="flat", command=on_submit, cursor="hand2")
        btn.pack(fill="x", padx=30, ipady=5)
        
        entry_user.bind('<Return>', lambda e: entry_pass.focus())
        entry_pass.bind('<Return>', on_submit)
        entry_user.focus()
        
        root.mainloop()
        return result["user"], result["pass"]

    def pedir_token():
        root = create_styled_window("Token CAD", 350, 220)
        result = {"token": None}
        
        tk.Label(root, text="Token Requerido", fg="#FFFFFF", bg="#1E1E1E", font=("Segoe UI", 16, "bold")).pack(pady=(20, 15))
        frame = tk.Frame(root, bg="#1E1E1E")
        frame.pack(fill="x", padx=30)
        
        tk.Label(frame, text="Digite o TOKEN enviado (E-mail/SMS):", fg="#CCCCCC", bg="#1E1E1E", font=("Segoe UI", 10)).pack(anchor="w")
        entry_token = tk.Entry(frame, font=("Segoe UI", 12), bg="#333333", fg="#FFFFFF", insertbackground="white", relief="flat")
        entry_token.pack(fill="x", pady=(2, 15), ipady=4)
        
        def on_submit(event=None):
            result["token"] = entry_token.get().strip()
            if not result["token"]:
                messagebox.showwarning("Aviso", "O Token é obrigatório!", parent=root)
                return
            root.destroy()
            
        btn = tk.Button(root, text="Confirmar", bg="#28A745", fg="white", activebackground="#218838", activeforeground="white", font=("Segoe UI", 11, "bold"), relief="flat", command=on_submit, cursor="hand2")
        btn.pack(fill="x", padx=30, ipady=5)
        
        entry_token.bind('<Return>', on_submit)
        entry_token.focus()
        
        root.mainloop()
        return result["token"]

    USER, PASS = pedir_credenciais()
    if not USER or not PASS:
        log("Usuário ou senha não fornecidos. Encerrando automação.")
        return

    WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DESTINO_DIR = os.path.join(WORKSPACE, "dados", "2026")
    os.makedirs(DESTINO_DIR, exist_ok=True)
    
    url_login = 'https://analisacad.seguranca.al.gov.br/app/cad/cad_gestao_login/'
    
    tasks = [
        {"name": "Veiculos Recuperados", "card_text": "Pesquisar Veículos na Base do CAD", "filename": "Veiculo Recuperado 2026.xls", "type": "veiculos"},
        {"name": "Armas Apreendidas", "card_text": "Pesquisar Armas na Base do CAD", "filename": "Armas 2026.xls", "type": "armas"},
        {"name": "Drogas Apreendidas", "card_text": "Pesquisar Drogas na Base do CAD", "filename": "Drogas 2026.xls", "type": "drogas"},
        {"name": "Maria da Penha", "card_text": "Pesquisar Ocorrências", "filename": "Maria da Penha 2026.xls", "type": "maria_da_penha"},
        {"name": "TCO", "card_text": "Pesquisar Ocorrências", "filename": "TCO 2026.xls", "type": "tco"},
        {"name": "Mandados de Prisão", "card_text": "Pesquisar Ocorrências", "filename": "Cumprimento de Mandados 2026.xls", "type": "mandados"},
        {"name": "Visitas Comunitárias", "card_text": "Pesquisar Ocorrências", "filename": "Visita Comunitária 2026.xls", "type": "visitas"}
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
        page = await context.new_page()
        
        log("Iniciando login CAD...")
        await page.goto(url_login, wait_until='domcontentloaded', timeout=90000)
        
        try:
            await page.wait_for_selector('#cpf', timeout=30000)
            await page.fill('#cpf', USER)
            await page.fill('#senha', PASS)
            await page.click('input[type="submit"]')
        except: pass
        
        # Token
        try:
            log("Verificando se pede Token...")
            await page.wait_for_selector('#token', timeout=15000)
            print("\n" + "="*50)
            print("🔑 TOKEN REQUERIDO PELO CAD! (Exibindo janela de popup)")
            print("="*50)
            
            token = pedir_token()
            if not token:
                log("Token não fornecido. Encerrando.")
                await browser.close()
                return
                
            print("Token recebido com sucesso!")

            await page.fill('#token', token)
            await page.click('input[type="submit"]')
            await asyncio.sleep(3)
        except Exception as e:
            pass

        log("Aguardando carregamento do portal principal (Portal de Pesquisa)...")
        try:
            # Aumentado para 90s devido a instabilidades do portal
            await page.wait_for_selector('text=Pesquisar', timeout=90000)
            log("Portal principal carregado com sucesso.")
        except Exception as e:
            log(f"Erro ao carregar portal principal: {e}")
            await page.screenshot(path=os.path.join(WORKSPACE, 'erro_carregamento_portal.png'))
            raise e

        for task in tasks:
            log(f"--- Iniciando indicador: {task['name']} ---")
            
            # Garantir que o menu Pesquisar está clicado/visível
            try:
                await page.click('text=Pesquisar', timeout=5000)
                await asyncio.sleep(2)
            except: pass

            target_frame = None
            for f in page.frames:
                try:
                    if await f.get_by_text(task['card_text']).is_visible():
                        target_frame = f
                        break
                except: continue

            if not target_frame:
                log(f"❌ Erro: Card '{task['card_text']}' não encontrado no portal.")
                continue

            log(f"Abrindo aba para '{task['name']}'...")
            async with context.expect_page() as new_page_info:
                await target_frame.get_by_text(task['card_text']).first.click()
            
            t_page = await new_page_info.value
            await t_page.wait_for_load_state()
            await asyncio.sleep(5)

            # Localizar Frame de Filtros
            f_filtros = None
            for frame in t_page.frames:
                if "fil.php" in frame.url.lower():
                    f_filtros = frame
                    break
            if not f_filtros: f_filtros = t_page

            log(f"Preenchendo filtros para {task['name']}...")
            
            try:
                # -------------------------------------------------------------
                # 1. Filtros Comuns (Data e Unidade)
                # -------------------------------------------------------------
                if task['type'] in ['veiculos', 'armas', 'drogas']:
                    await f_filtros.select_option('#SC_ocor_dt_ocor_cond', value='CY')
                else: # Ocorrências
                    await f_filtros.select_option('#SC_data_cond', value='CY')
                
                await asyncio.sleep(1)

                # Unidade/Despacho: 9º BPM
                sel_unid = ""
                if task['type'] == 'veiculos': sel_unid = '#SC_veic_id_orga_unid_fk_orig'
                elif task['type'] in ['armas', 'drogas']: sel_unid = '#SC_despc_id_orga_unid_fk_orig'
                elif task['type'] in ['maria_da_penha', 'tco', 'mandados', 'visitas']: 
                    # Órgão -> PM
                    await f_filtros.select_option('#SC_unid_id_orga_fk_orig', value='2##@@POLÍCIA MILITAR')
                    await f_filtros.locator('#SC_unid_id_orga_fk_orig option[value="2##@@POLÍCIA MILITAR"]').dblclick()
                    await asyncio.sleep(3)
                    sel_unid = '#SC_despc_id_orga_unid_fk_orig'

                # Preencher 9º BPM
                if sel_unid:
                    await f_filtros.wait_for_selector(f"{sel_unid} option", timeout=15000)
                    options = await f_filtros.locator(f"{sel_unid} option").all()
                    val_9bpm = None
                    for opt in options:
                        if "9º BPM" in await opt.inner_text():
                            val_9bpm = await opt.get_attribute('value')
                            break
                    if val_9bpm:
                        await f_filtros.select_option(sel_unid, value=val_9bpm)
                        await f_filtros.locator(f"{sel_unid} option[value='{val_9bpm}']").dblclick()
                    await asyncio.sleep(1)

                # -------------------------------------------------------------
                # 2. Filtros Específicos
                # -------------------------------------------------------------
                if task['type'] == 'veiculos':
                    await f_filtros.select_option('#SC_veic_id_ocor_envl_veic_sitc_fk_orig', label='RECUPERADO')
                    await f_filtros.locator('#SC_veic_id_ocor_envl_veic_sitc_fk_orig option').filter(has_text='RECUPERADO').dblclick()
                
                elif task['type'] == 'maria_da_penha':
                    # Natureza Geral
                    await f_filtros.select_option('#SC_ocor_id_ocor_grup_fk_orig', label='LEI MARIA DA PENHA')
                    await f_filtros.locator('#SC_ocor_id_ocor_grup_fk_orig option').filter(has_text='LEI MARIA DA PENHA').dblclick()
                
                elif task['type'] == 'tco':
                    # Sub Solução
                    await f_filtros.select_option('#SC_despc_id_ocor_despc_soluc_tipo_fk_orig', value='9##@@ELABOROU TCO (PM)')
                    await f_filtros.locator('#SC_despc_id_ocor_despc_soluc_tipo_fk_orig option[value="9##@@ELABOROU TCO (PM)"]').dblclick()
                
                elif task['type'] == 'mandados':
                    # Tipo do Despacho
                    await f_filtros.select_option('#SC_despc_id_ocor_despc_tip_fk_orig', value='6##@@CUMPRIMENTO DE MANDADO JUDICIAL')
                    await f_filtros.locator('#SC_despc_id_ocor_despc_tip_fk_orig option[value="6##@@CUMPRIMENTO DE MANDADO JUDICIAL"]').dblclick()

                elif task['type'] == 'visitas':
                    # Natureza -> OCORRÊNCIA SEM ILICITUDE
                    await f_filtros.select_option('#SC_ocor_id_ocor_grup_fk_orig', label='OCORRÊNCIA SEM ILICITUDE')
                    await f_filtros.locator('#SC_ocor_id_ocor_grup_fk_orig option').filter(has_text='OCORRÊNCIA SEM ILICITUDE').dblclick()
                    await asyncio.sleep(2)
                    # Tipicidades (Múltiplas)
                    tips = ["VISITA COMUNITÁRIA", "VISITA COMUNITÁRIA / MARIA DA PENHA", "VISITA PREVENTIVA"]
                    for t in tips:
                        try:
                            await f_filtros.select_option('#SC_ocor_id_ocor_sgrup_fk_orig', label=t)
                            await f_filtros.locator('#SC_ocor_id_ocor_sgrup_fk_orig option').filter(has_text=t).dblclick()
                        except: pass

                await asyncio.sleep(1)
                
                # -------------------------------------------------------------
                # 3. Pesquisar e Exportar
                # -------------------------------------------------------------
                log("Clicando em Pesquisar/Filtrar...")
                btn_pesq = "#sc_b_pesq_top" if task['type'] not in ['veiculos', 'armas', 'drogas'] else "#sc_b_pesq_bot"
                try: await f_filtros.click(btn_pesq, timeout=5000)
                except: 
                    for alt in ["text=Pesquisa Avançada", "text=Filtrar", "text=Pesquisar"]:
                        try: 
                            await f_filtros.click(alt, timeout=3000)
                            break
                        except: pass
                
                log("Aguardando resultados (15s)...")
                await asyncio.sleep(15)

                f_grid = None
                for gr_frame in t_page.frames:
                    if "grid" in gr_frame.url.lower() and "fil" not in gr_frame.url.lower():
                        f_grid = gr_frame
                        break
                if not f_grid: f_grid = t_page
                
                # Download
                await handle_download(context, t_page, f_grid, task['filename'], DESTINO_DIR)

            except Exception as loop_e:
                log(f"⚠️ Erro ao processar '{task['name']}': {loop_e}")

            log(f"Fechando aba de '{task['name']}'...")
            await t_page.close()
            await asyncio.sleep(2)

        log("🏁 Coleta Consolidada do CAD Finalizada!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(script_coleta_consolidada())
