"""
extract_apollo_sequence_contacts.py - VISU Dados
=================================================

Módulo orquestrador de extração de contatos filtrados por Step de Múltiplas Sequences
do Apollo.io.
"""

# -------------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------------
import sys
import os
import time
import glob
import logging
import shutil
from pathlib import Path
from typing import Optional

sys.path.append(str(Path(__file__).resolve().parents[2]))

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from common.common_browser import iniciar_chrome_driver, CAMINHO_PERFIL_VISU
from common.common_setup import verificar_e_configurar

# -------------------------------------------------------------------------
# Configuração de logging
# -------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("apollo_sequence_contacts_extract.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Constantes — URLs e Tempos
# -------------------------------------------------------------------------
URL_SEQUENCES_LIST = (
    "https://app.apollo.io/#/sequences"
    "?page=1&sortAscending=false&sortByField=lastUsedAt"
)

TIMEOUT_ELEMENTO = 30
TIMEOUT_DOWNLOAD = 90

# -------------------------------------------------------------------------
# Seletores (XPath / CSS)
# -------------------------------------------------------------------------
def _xpath_sequence_link(nome_sequence: str) -> str:
    return f'//div[@role="gridcell"]//a[contains(., "{nome_sequence}")]'

SELECTOR_TAB_CONTACTS = 'a#Contacts[role="tab"]'
XPATH_BTN_CONFIRM_MODAL = '//button[@data-cta-variant="destroy"][.//span[normalize-space(text())="Confirm"]]'
SELECTOR_BTN_SHOW_FILTERS = 'button[data-cy="finder-filter-button"]'
XPATH_ACCORDION_SEQUENCE_STEP = '//div[contains(@class,"zp-accordion-header")][.//span[normalize-space(text())="Sequence Step"]]'

def _xpath_step_label(step_label: str) -> str:
    return f'//label[.//span[normalize-space(text())="{step_label}"]]'

SELECTOR_BTN_BULK_SELECT = 'button[class*="finder-select-multiple-entities-button"]'
SELECTOR_LINK_SELECT_ALL = 'a[data-cy="select-this-page"]'
SELECTOR_BTN_MORE_ACTIONS = 'button[data-cy="more-button"]'
XPATH_LINK_EXPORT = '//a[contains(@class,"zp-menu-item")][normalize-space(.)="Export"]'
XPATH_BTN_EXPORT_RECORDS = '//button[.//div[@data-elem="button-label" and normalize-space(text())="Export records"]]'
XPATH_BTN_DOWNLOAD = '//button[.//div[@data-elem="button-label" and normalize-space(text())="Download"]]'

# -------------------------------------------------------------------------
# Utilitários Originais (Browser)
# -------------------------------------------------------------------------
def clicar_elemento(driver, wait: WebDriverWait, seletor: str, tipo: str = "css", descricao: str = "", js_click: bool = False) -> bool:
    by = By.CSS_SELECTOR if tipo == "css" else By.XPATH
    nome = descricao or seletor

    log.info(f"  → Localizando: {nome}...")
    try:
        elemento = wait.until(EC.element_to_be_clickable((by, seletor)))
    except TimeoutException:
        log.error(f"  ❌ Elemento não encontrado ou não clicável: {nome}")
        return False

    try:
        if js_click:
            driver.execute_script("arguments[0].click();", elemento)
            log.info(f"  ✅ Clique JS em: {nome}")
        else:
            elemento.click()
            log.info(f"  ✅ Clique em: {nome}")
    except Exception as e:
        log.warning(f"  ⚠️  Clique direto falhou ({e}). Tentando JS click...")
        try:
            driver.execute_script("arguments[0].click();", elemento)
            log.info(f"  ✅ Clique JS (fallback) em: {nome}")
        except Exception as e2:
            log.error(f"  ❌ JS click também falhou em: {nome} — {e2}")
            return False

    return True

# -------------------------------------------------------------------------
# Utilitários Novos (Arquitetura Clean Code)
# -------------------------------------------------------------------------
def renomear_arquivo_exportado(caminho_original: str, pasta_download: str, nome_sequence: str, step_label: str) -> str:
    seq_seguro = "".join([c if c.isalnum() else "_" for c in nome_sequence]).strip("_")
    step_seguro = step_label.replace(" ", "").replace(":", "_")
    
    novo_nome = f"{seq_seguro}_{step_seguro}.csv"
    novo_caminho = os.path.join(pasta_download, novo_nome)

    if os.path.exists(novo_caminho):
        os.remove(novo_caminho)

    shutil.move(caminho_original, novo_caminho)
    log.info(f"  [ARQUIVO] Renomeado para: {novo_nome}")
    
    return novo_caminho

def verificar_se_tabela_tem_dados(driver) -> bool:
    """
    Verifica de forma inteligente e rápida se a tabela retornou dados.
    Corrige o falso-positivo garantindo que o elemento está visível,
    e faz um 'fast-fail' se a mensagem de vazio estiver na tela.
    """
    # 1. Fast-Fail: Procura a mensagem exata de vazio ("No records found")
    # find_elements retorna uma lista (vazia se não achar nada), não gera erro.
    elementos_vazios = driver.find_elements(By.XPATH, '//*[contains(text(), "No records found")]')
    for el in elementos_vazios:
        if el.is_displayed():
            log.info("  [FAST-CHECK] Mensagem 'No records found' detectada na tela.")
            return False

    # 2. Verificação Segura: Exige que o botão esteja VISÍVEL (não apenas oculto no HTML)
    wait_curto = WebDriverWait(driver, 3)
    try:
        wait_curto.until(EC.visibility_of_element_located((By.CSS_SELECTOR, SELECTOR_BTN_BULK_SELECT)))
        return True
    except TimeoutException:
        return False

# =========================================================================
# CAMADA 3 (BOTTOM): EXTRAI APENAS UM STEP
# =========================================================================
def extrair_unico_step(driver, wait, nome_sequence: str, step_label: str, pasta_download: str) -> Optional[str]:
    """Sabe apenas como lidar com 1 step: Marca, Exporta, Renomeia e Desmarca."""
    log.info(f"\n  [STEP] Iniciando processamento: {step_label}")
    arquivo_final = None

    if not clicar_elemento(driver, wait, _xpath_step_label(step_label), "xpath", f"Marcar {step_label}", js_click=True):
        return None
    
    time.sleep(3) 
    
    if not verificar_se_tabela_tem_dados(driver):
        log.warning(f"  ⚠️ Nenhum contato encontrado no {step_label}. Pulando exportação.")
    else:
        sucesso = (
            clicar_elemento(driver, wait, SELECTOR_BTN_BULK_SELECT, "css", "Bulk Select") and
            clicar_elemento(driver, wait, SELECTOR_LINK_SELECT_ALL, "css", "Select all people") and
            clicar_elemento(driver, wait, SELECTOR_BTN_MORE_ACTIONS, "css", "More Actions") and
            clicar_elemento(driver, wait, XPATH_LINK_EXPORT, "xpath", "Export") and
            clicar_elemento(driver, wait, XPATH_BTN_EXPORT_RECORDS, "xpath", "Export records")
        )

        if sucesso:
            # --- NOVO: Dual-Polling (Monitora a pasta E o botão simultaneamente) ---
            log.info("  [DOWNLOAD] Aguardando processamento (auto-download ou botão)...")
            ts_inicio = time.time()
            caminho_csv = None
            botao_clicado = False

            while time.time() - ts_inicio < TIMEOUT_DOWNLOAD:
                # 1. Verifica se o arquivo chegou magicamente na pasta (Auto-download do Apollo)
                # Usamos getmtime (Data de Modificação) para ter precisão absoluta contra o Windows
                candidatos = [
                    f for f in glob.glob(os.path.join(pasta_download, "*.csv"))
                    if not f.endswith(".crdownload") and os.path.getmtime(f) >= ts_inicio - 2.0
                ]
                if candidatos:
                    caminho_csv = max(candidatos, key=os.path.getmtime)
                    log.info(f"  [DOWNLOAD] ✅ Arquivo detectado: {caminho_csv}")
                    break

                # 2. Se o arquivo não chegou, procura o botão "Download" como fallback
                if not botao_clicado:
                    try:
                        btn = driver.find_element(By.XPATH, XPATH_BTN_DOWNLOAD)
                        if btn.is_displayed() and btn.is_enabled():
                            driver.execute_script("arguments[0].click();", btn)
                            log.info("  [DOWNLOAD] Botão 'Download' detectado e clicado manualmente.")
                            botao_clicado = True
                    except Exception:
                        pass # Silencioso, pois é normal o botão demorar ou nem aparecer

                time.sleep(1)

            # --- Tratamento Pós-Download ---
            if caminho_csv:
                # Buffer de 1 segundo para o Windows/Antivírus liberar o arquivo antes de mover
                time.sleep(1) 
                arquivo_final = renomear_arquivo_exportado(caminho_csv, pasta_download, nome_sequence, step_label)
                
                log.info("  [COOLDOWN] Fechando modal de sucesso do Apollo (ESC)...")
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                
                log.info("  [COOLDOWN] Aguardando a tela estabilizar (3s)...")
                time.sleep(3) 
            else:
                log.error(f"  ❌ Timeout: Nenhum CSV recebido após {TIMEOUT_DOWNLOAD}s.")

    log.info(f"  [LIMPANDO] Desmarcando {step_label}...")
    clicar_elemento(driver, wait, _xpath_step_label(step_label), "xpath", f"Desmarcar {step_label}", js_click=True)
    time.sleep(3)

    return arquivo_final

# =========================================================================
# CAMADA 2 (MIDDLE): PREPARA A SEQUENCE E ITERA OS STEPS
# =========================================================================
def processar_uma_sequence(driver, wait, nome_sequence: str, step_labels: list, pasta_download: str) -> list:
    log.info(f"\n[SEQUENCE] ── Iniciando Sequence: {nome_sequence} ──")
    arquivos_baixados = []

    driver.get(URL_SEQUENCES_LIST)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="gridcell"]')))
    except TimeoutException:
        log.error(f"[SEQUENCE] ❌ Tabela de Sequences não renderizou para {nome_sequence}.")
        return arquivos_baixados
    time.sleep(1)

    if not clicar_elemento(driver, wait, _xpath_sequence_link(nome_sequence), "xpath", f"Acessar {nome_sequence}"):
        log.error(f"[SEQUENCE] ❌ Falha ao encontrar a sequence {nome_sequence}.")
        return arquivos_baixados
    time.sleep(2)

    if not clicar_elemento(driver, wait, SELECTOR_TAB_CONTACTS, "css", "Aba Contacts"):
        return arquivos_baixados
    time.sleep(1)

    log.info("  [SEQUENCE] Verificando modal de confirmação...")
    try:
        btn_confirm = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, XPATH_BTN_CONFIRM_MODAL)))
        btn_confirm.click()
        log.info("  [SEQUENCE] ✅ Modal 'Are you sure?' confirmado.")
    except TimeoutException:
        pass 
    time.sleep(2)

    preparacao_ok = (
        clicar_elemento(driver, wait, SELECTOR_BTN_SHOW_FILTERS, "css", "Show Filters") and
        clicar_elemento(driver, wait, XPATH_ACCORDION_SEQUENCE_STEP, "xpath", "Accordion Step")
    )

    if not preparacao_ok:
        log.error(f"[SEQUENCE] ❌ Falha ao preparar filtros para {nome_sequence}.")
        return arquivos_baixados
    time.sleep(1)

    for step in step_labels:
        arquivo = extrair_unico_step(driver, wait, nome_sequence, step, pasta_download)
        if arquivo:
            arquivos_baixados.append(arquivo)

    return arquivos_baixados

# =========================================================================
# CAMADA 1 (TOP): ORQUESTRAÇÃO GERAL
# =========================================================================
def orquestrar_extracao_sequences(nomes_sequences: list, step_labels: list, download_dir: str = None, headless: bool = False, timeout: int = TIMEOUT_ELEMENTO) -> dict:
    pasta = download_dir or str(Path.home() / "Downloads")
    resultado_geral = {} 

    log.info("=" * 60)
    log.info(f"  ORQUESTRADOR APOLLO — Iniciando Operação em Lote")
    log.info(f"  Sequences: {nomes_sequences}")
    log.info(f"  Steps:     {step_labels}")
    log.info("=" * 60)

    driver = iniciar_chrome_driver(headless=headless, usar_perfil_visu=True, download_dir=pasta)

    try:
        wait = WebDriverWait(driver, timeout)

        if not verificar_e_configurar(driver, CAMINHO_PERFIL_VISU, URL_SEQUENCES_LIST):
            log.error("[ORQUESTRADOR] Sessão inválida. Cancelando tudo.")
            return resultado_geral

        for nome in nomes_sequences:
            arquivos = processar_uma_sequence(driver, wait, nome, step_labels, pasta)
            resultado_geral[nome] = arquivos

        return resultado_geral

    except Exception as e:
        log.error(f"[ERRO FATAL] Falha inesperada no orquestrador: {e}", exc_info=True)
        return resultado_geral
    finally:
        driver.quit()
        log.info("[ORQUESTRADOR] Operação finalizada. Navegador encerrado.")

# -------------------------------------------------------------------------
# Execução Direta (Para Testes)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    TEST_SEQUENCES = ["[Alessandro]"] 
    TEST_STEPS = ["Step: 1", "Step: 2"]
    
    resultados = orquestrar_extracao_sequences(
        nomes_sequences=TEST_SEQUENCES,
        step_labels=TEST_STEPS,
        headless=False
    )
    print(f"\nResultados do teste direto: {resultados}")