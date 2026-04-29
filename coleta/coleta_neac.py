"""
coleta_neac.py — Robô autônomo de coleta NEAC Pentaho (Versão Robusta)
----------------------------------------------------------------------
Baixa automaticamente os 3 relatórios do sistema NEAC (SSP-AL):
  1. CVLI          → 03.0 - Relação Nominal (Ano)
  2. CVP           → 07.2 - Acumulado por natureza - AISP (24ª AISP)
  3. Tent. Homicídio → 01.0 - Relação Nominal (Ano) RISP_AISP (4ª RISP / 24ª AISP)

Estratégia: "Clean Slate" — Realiza o reload da Home entre cada relatório para
evitar conflitos de abas/iframes do Pentaho.

Variáveis de ambiente (.env):
  NEAC_USER  →  usuário de acesso ao NEAC
  NEAC_PASS  →  senha de acesso ao NEAC
"""

import asyncio
import os
import datetime
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright
import pandas as pd
import numpy as np
import re

import sys
# Força UTF-8 para stdout no Windows para evitar erros de charmap
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── Configuração ──────────────────────────────────────────────────────────────
load_dotenv()

ANO          = str(datetime.datetime.now().year)
BASE_DIR     = Path(__file__).parent.parent
DESTINO_DIR  = BASE_DIR / "dados" / ANO
LOG_FILE     = BASE_DIR / "coleta_neac.log"

URL_BASE     = "https://neac.seguranca.al.gov.br/pentaho/"
URL_LOGIN    = URL_BASE + "Login"
URL_HOME     = URL_BASE + "Home"

# ── Utilitários ───────────────────────────────────────────────────────────────
def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{timestamp}] {msg}"
    print(linha)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linha + "\n")

def update_report_status(report_name, status):
    progress_file = Path(__file__).parent.parent / "coleta_progresso.txt"
    progress = {}
    if progress_file.exists():
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "|" in line:
                        r, s = line.strip().split("|")
                        progress[r] = s
        except: pass
    
    progress[report_name] = status
    with open(progress_file, "w", encoding="utf-8") as f:
        for r, s in progress.items():
            f.write(f"{r}|{s}\n")

async def fazer_login(page, user: str, password: str):
    log("Acessando NEAC Pentaho...")
    await page.goto(URL_LOGIN, wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_selector("#j_username", timeout=60000)
    await page.fill("#j_username", user)
    await page.fill("#j_password", password)
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(10000)
    log("Login efetuado.")

async def ir_para_home_e_abrir_browser(page):
    """Reseta o Pentaho para o estado inicial e abre o 'Procurar Arquivos'."""
    log("Limpando estado (Reset p/ Home)...")
    await page.goto(URL_HOME, wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(5000)
    
    log("Clicando em 'Procurar Arquivos'...")
    home_frame = page.frame_locator('iframe[id="home.perspective"]')
    await home_frame.get_by_text("Procurar Arquivos").click(timeout=10000)
    await page.wait_for_timeout(5000)
    
    return page.frame_locator('iframe[id="browser.perspective"]')

async def expandir_pasta(nav_frame, nome: str):
    log(f"Expandindo pasta: {nome}...")
    await nav_frame.get_by_text(nome, exact=False).first.dblclick(force=True)
    await asyncio.sleep(2)

async def selecionar_pasta(nav_frame, nome: str):
    log(f"Selecionando pasta: {nome}...")
    await nav_frame.get_by_text(nome, exact=False).first.click(force=True)
    await asyncio.sleep(2)

async def abrir_relatorio(nav_frame, nome_parcial: str, page_obj):
    try:
        log(f"Abrindo relatório: {nome_parcial}...")
        # Usa seletor que ignore espaços extras e seja case-insensitive
        locator = nav_frame.get_by_text(nome_parcial, exact=False).first
        await locator.wait_for(state="visible", timeout=20000)
        await locator.dblclick(force=True)
        await asyncio.sleep(10) # Aguarda carregamento do form
    except Exception as e:
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        screenshot_path = f"erro_abrir_{timestamp}.png"
        await page_obj.screenshot(path=screenshot_path)
        log(f"❌ Falha ao abrir {nome_parcial}. Erro: {e}. Screenshot: {screenshot_path}")
        raise e

async def encontrar_frame_relatorio(page):
    """Busca o frame que contém os parâmetros do relatório e espera os selects."""
    log("Buscando frame do relatório...")
    for attempt in range(10): # Tenta por 50s
        for frame in page.frames:
            try:
                # Verifica se o frame tem o botão 'View Report'
                if await frame.get_by_text("View Report", exact=False).count() > 0:
                    # Verifica se já renderezou os selects de parâmetros
                    if await frame.locator("select").count() > 0:
                        log(f"Frame do relatório localizado e pronto: {frame.name}")
                        return frame
            except: pass
        await asyncio.sleep(5)
    log("❌ Time-out: Frame do relatório não encontrado ou sem selects.")
    return None

async def preencher_comum(frame, ano: str):
    """Preenche Ano e Saída=Excel que são comuns a todos, buscando-os dinamicamente."""
    log(f"Buscando campos Ano ({ano}) e Saída (Excel)...")
    qtd = await frame.locator("select").count()
    
    # Busca o select que contém o Ano
    ano_encontrado = False
    for i in range(qtd):
        opts = await frame.locator("select").nth(i).inner_text()
        if ano in opts.split('\n'): # Match exato por linha
            await frame.locator("select").nth(i).select_option(ano)
            log(f"  → Ano {ano} selecionado no select {i}")
            ano_encontrado = True
            break
    
    if not ano_encontrado:
        # Tenta busca parcial caso o ano esteja formatado (ex: [2026])
        for i in range(qtd):
            opts = await frame.locator("select").nth(i).inner_text()
            if ano in opts:
                await frame.locator("select").nth(i).select_option(label=next(o for o in opts.split('\n') if ano in o))
                log(f"  → Ano {ano} (parcial) selecionado no select {i}")
                ano_encontrado = True
                break

    # Busca o select que contém 'Excel'
    for i in range(qtd):
        opts = await frame.locator("select").nth(i).inner_text()
        if "Excel" in opts:
            await frame.locator("select").nth(i).select_option("Excel")
            log(f"  → Saída Excel selecionada no select {i}")
            break
    
    await asyncio.sleep(2)

async def disparar_download(page, frame, nome_final: str):
    log(f"Disparando download de {nome_final}...")
    btn = frame.get_by_text("View Report", exact=True)
    async with page.expect_download(timeout=120000) as download_info:
        await btn.click(force=True)
    download = await download_info.value
    path = DESTINO_DIR / nome_final
    DESTINO_DIR.mkdir(parents=True, exist_ok=True)
    await download.save_as(str(path))
    log(f"✅ Arquivo salvo: {path.name}")
    return True

# ── Rotinas Específicas ───────────────────────────────────────────────────────

async def download_cvli(page, nav_frame, ano: str):
    log(">>> Iniciando CVLI")
    await expandir_pasta(nav_frame, "4_RISP")
    await selecionar_pasta(nav_frame, "CVLI")
    await abrir_relatorio(nav_frame, "03.0 - Relação Nominal (Ano)", page)
    
    frame = await encontrar_frame_relatorio(page)
    if not frame: return False
    
    await preencher_comum(frame, ano)
    return await disparar_download(page, frame, f"MVI {ano}.xls")

async def download_cvp(page, nav_frame, ano: str):
    log(">>> Iniciando CVP")
    await expandir_pasta(nav_frame, "4_RISP")
    await selecionar_pasta(nav_frame, "CVP")
    # Usa seletor curto e resiliente
    await abrir_relatorio(nav_frame, "07.2", page)
    
    frame = await encontrar_frame_relatorio(page)
    if not frame: return False
    
    # Busca select da AISP (o que contém '24')
    qtd = await frame.locator("select").count()
    for i in range(qtd):
        options = await frame.locator("select").nth(i).inner_text()
        if "24" in options:
            opts_lista = [l.strip() for l in options.split('\n') if "24" in l]
            if opts_lista:
                await frame.locator("select").nth(i).select_option(label=opts_lista[0])
                log(f"AISP 24ª selecionada no select {i}")
                break
            
    await preencher_comum(frame, ano)
    return await disparar_download(page, frame, "CVP Geral 2026.xls")

async def download_tentativa(page, nav_frame, ano: str):
    log(">>> Iniciando TENTATIVA HOMICÍDIO")
    await expandir_pasta(nav_frame, "4_RISP")
    await selecionar_pasta(nav_frame, "TENTATIVA_HOMICIDIO")
    # Usa seletor curto e resiliente
    await abrir_relatorio(nav_frame, "01.0", page)
    
    frame = await encontrar_frame_relatorio(page)
    if not frame: return False
    
    # Tentativa tem RISP (4ª) e AISP (24ª)
    qtd = await frame.locator("select").count()
    for i in range(qtd):
        text = await frame.locator("select").nth(i).inner_text()
        lines = [l.strip() for l in text.split('\n')]
        if "4ª" in text and "RISP" in text.upper():
            opt = next((l for l in lines if "4ª" in l), None)
            if opt:
                await frame.locator("select").nth(i).select_option(label=opt)
                log(f"RISP 4ª selecionada no select {i}")
        elif "24" in text:
            opt = next((l for l in lines if "24" in l), None)
            if opt:
                await frame.locator("select").nth(i).select_option(label=opt)
                log(f"AISP 24ª selecionada no select {i}")
            
    await preencher_comum(frame, ano)
    return await disparar_download(page, frame, f"Tentativa de MVI {ano}.xls")

async def download_prisões(page, nav_frame, ano: str):
    log(">>> Iniciando PRISÕES (Mês a Mês)")
    await expandir_pasta(nav_frame, "PMAL")
    await selecionar_pasta(nav_frame, "CAD")
    await expandir_pasta(nav_frame, "CAD")
    await selecionar_pasta(nav_frame, "Prisões")
    await abrir_relatorio(nav_frame, "04.2", page)
    
    frame = await encontrar_frame_relatorio(page)
    if not frame: return False
    
    meses_nomes = [
        "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
        "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"
    ]
    
    mes_atual = datetime.datetime.now().month
    dfs = []
    
    try:
        # 1. Selecionar OPM (9º BPM)
        await frame.locator("select").nth(0).select_option(label="9º BPM")
        # 2. Selecionar ANO
        await frame.locator("select").nth(1).select_option(label=ano)
        
        # Esperar cascata de meses carregar
        await asyncio.sleep(5)
        
        # 3. Detectar meses disponíveis no Select 2
        opcoes_meses = await frame.locator("select").nth(2).locator("option").all_inner_texts()
        opcoes_meses = [m.strip().upper() for m in opcoes_meses if m.strip()]
        log(f"Meses disponíveis no NEAC: {opcoes_meses}")
        
        # 4. Selecionar Saída Excel (Último select)
        await frame.locator("select").nth(3).select_option(label="Excel")
        
        for m_nome in meses_nomes[:mes_atual]:
            if m_nome not in opcoes_meses:
                log(f"  -> Pulando {m_nome} (não disponível no sistema)")
                continue
                
            log(f"  -> Coletando {m_nome}...")
            # Seleciona o mês no Select 2
            await frame.locator("select").nth(2).select_option(label=m_nome)
            await asyncio.sleep(1) # Estabilidade
            
            temp_name = f"temp_prisao_{m_nome}.xls"
            try:
                async with page.expect_download(timeout=120000) as download_info:
                    # Clique no View Report
                    btn = frame.locator('button:has-text("View Report"), input[type="button"][value="View Report"]').first
                    await btn.click(force=True)
                
                download = await download_info.value
                temp_path = DESTINO_DIR / temp_name
                await download.save_as(temp_path)
                
                # Ler e guardar para merge
                df_temp = pd.read_excel(temp_path, header=None)
                dfs.append(df_temp)
                temp_path.unlink() # Limpa temp
                log(f"     ✅ {m_nome} OK")
            except Exception as e:
                log(f"     ❌ Erro {m_nome}: {e}")
                
    except Exception as e:
        log(f"Erro em PRISÕES: {e}")
        return False

    if dfs:
        log(f"Mesclando {len(dfs)} arquivos de Prisões...")
        consolidado = pd.concat(dfs, ignore_index=True)
        out_path = DESTINO_DIR / f"Prisões {ano}.xls"
        consolidado.to_excel(out_path, index=False, header=False)
        log(f"✅ Prisões unificadas em: {out_path.name}")
        return True
    
    return False

# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    USER = os.getenv("NEAC_USER")
    PASS = os.getenv("NEAC_PASS")
    if not USER or not PASS:
        log("Erro: Credenciais não encontradas no .env")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        
        try:
            await fazer_login(page, USER, PASS)
            
            # Relatórios a baixar
            jobs_all = [
                ("CVLI", download_cvli),
                ("CVP", download_cvp),
                ("TENTATIVA", download_tentativa),
                ("PRISÕES", download_prisões)
            ]
            
            import unicodedata
            def normalize_str(s):
                return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()

            # Filtra pelos selecionados
            sel_file = Path(__file__).parent.parent / "selected_reports.txt"
            selected = []
            if sel_file.exists():
                with open(sel_file, "r", encoding="utf-8") as f:
                    selected = [normalize_str(line.strip()) for line in f if line.strip()]
            
            jobs = [j for j in jobs_all if normalize_str(j[0]) in selected] if selected else jobs_all
            
            if not jobs:
                log("Nenhum relatório do NEAC selecionado. Pulando.")
                return

            resultados = {}
            for nome, func in jobs:
                try:
                    update_report_status(nome, "PROCESSANDO")
                    nav = await ir_para_home_e_abrir_browser(page)
                    res = await func(page, nav, ANO)
                    resultados[nome] = res
                    update_report_status(nome, "OK" if res else "ERRO")
                except Exception as e:
                    log(f"Erro em {nome}: {e}")
                    ts = datetime.datetime.now().strftime("%H%M%S")
                    await page.screenshot(path=f"erro_{nome}_{ts}.png")
                    resultados[nome] = False
                    update_report_status(nome, "ERRO")

            log("\n" + "="*30)
            log(f"RESUMO FINAL:")
            for nome, res in resultados.items():
                log(f"{nome}: {'OK ✅' if res else 'FALHA ❌'}")
            log("="*30)
            
        except Exception as e:
            log(f"Erro Crítico no Main: {e}")
            await page.screenshot(path="erro_critico_main.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
