"""
extract_apollo_sequence_contacts.py - VISU Dados
=================================================

Módulo de extração de contatos filtrados por Step de uma Sequence
específica do Apollo.io.

Representa a fase de **extração (Extract)** do pipeline ETL da VISU para
dados de contatos do Apollo por etapa de Sequence. Utiliza o perfil Chrome
logado da VISU, eliminando a necessidade de armazenar credenciais.

Fluxo de execução (12 etapas):
-------------------------------
1.  Navega para a lista de Sequences e clica na Sequence alvo
2.  Clica na aba "Contacts" da Sequence
3.  Confirma o modal "Are you sure?" clicando em "Confirm"
4.  Clica em "Show Filters" para abrir o painel de filtros
5.  Clica no accordion "Sequence Step" para expandir os filtros de etapa
6.  Marca o checkbox "Step: 1" (ou o step configurado)
7.  Clica no botão de seleção múltipla (bulk select checkbox)
8.  Clica em "Select all people (N)" para selecionar todos os contatos
9.  Clica no botão "More actions" (⋯) da toolbar
10. Clica em "Export" no menu de ações
11. Clica em "Export records" no modal de exportação
12. Clica em "Download" no modal de confirmação e aguarda o arquivo

Autenticação:
-------------
Nenhuma credencial é armazenada neste módulo. O login é mantido
pelo perfil Chrome em /projects/chrome_profiles/profile_visu.

Dependências:
-------------
- selenium (Selenium Manager cuida do chromedriver automaticamente)
- common_browser (módulo interno VISU)
- common_setup  (módulo interno VISU)
"""

# -------------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------------
import sys
import os
import time
import glob
import logging
from pathlib import Path
from typing import Optional

sys.path.append(str(Path(__file__).resolve().parents[2]))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

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
# Constantes — URLs
# -------------------------------------------------------------------------
URL_SEQUENCES_LIST = (
    "https://app.apollo.io/#/sequences"
    "?page=1&sortAscending=false&sortByField=lastUsedAt"
)

# Tempo máximo de espera por elementos (segundos)
TIMEOUT_ELEMENTO = 30

# Tempo máximo para o download completar (segundos)
TIMEOUT_DOWNLOAD = 90

# -------------------------------------------------------------------------
# Seletores — centralizados para facilitar manutenção
# -------------------------------------------------------------------------

# Etapa 1 — Link da Sequence na tabela (texto parcial configurável)
# XPath: <a> dentro de gridcell que contenha o nome da sequence
def _xpath_sequence_link(nome_sequence: str) -> str:
    return f'//div[@role="gridcell"]//a[contains(., "{nome_sequence}")]'

# Etapa 2 — Aba "Contacts"
# <a id="Contacts" role="tab" ...>
SELECTOR_TAB_CONTACTS = 'a#Contacts[role="tab"]'

# Etapa 3 — Botão "Confirm" no modal "Are you sure?"
# Aparece ao navegar para Contacts com alterações não salvas na Sequence.
# <button data-cta-variant="destroy" ...><span>Confirm</span></button>
# Usa data-cta-variant="destroy" + texto para não colidir com outros modais.
XPATH_BTN_CONFIRM_MODAL = (
    '//button[@data-cta-variant="destroy"]'
    '[.//span[normalize-space(text())="Confirm"]]'
)

# Etapa 4 — Botão "Show Filters"
# <button data-cy="finder-filter-button" ...>
SELECTOR_BTN_SHOW_FILTERS = 'button[data-cy="finder-filter-button"]'

# Etapa 5 — Header do accordion "Sequence Step"
# <span>Sequence Step</span> dentro de um header clicável
XPATH_ACCORDION_SEQUENCE_STEP = (
    '//div[contains(@class,"zp-accordion-header")]'
    '[.//span[normalize-space(text())="Sequence Step"]]'
)

# Etapa 5 — Checkbox/label do Step (texto configurável, ex: "Step: 1")
# <label> que contém <span> com o texto do step
def _xpath_step_label(step_label: str) -> str:
    return f'//label[.//span[normalize-space(text())="{step_label}"]]'

# Etapa 6 — Botão de seleção múltipla (bulk select)
# <button class="...finder-select-multiple-entities-button">
SELECTOR_BTN_BULK_SELECT = 'button[class*="finder-select-multiple-entities-button"]'

# Etapa 7 — Link "Select all people (N)"
# <a data-cy="select-this-page" ...>
SELECTOR_LINK_SELECT_ALL = 'a[data-cy="select-this-page"]'

# Etapa 8 — Botão "More actions" (⋯) da toolbar de seleção
# <button data-cy="more-button" ...>
SELECTOR_BTN_MORE_ACTIONS = 'button[data-cy="more-button"]'

# Etapa 9 — Link "Export" no menu dropdown
# <a class="...zp-menu-item...">Export</a>  (sem data-cy preenchido)
XPATH_LINK_EXPORT = (
    '//a[contains(@class,"zp-menu-item")]'
    '[normalize-space(.)="Export"]'
)

# Etapa 10 — Botão "Export records" no modal
# <div data-elem="button-label">Export records</div> dentro de <button>
XPATH_BTN_EXPORT_RECORDS = (
    '//button[.//div[@data-elem="button-label" '
    'and normalize-space(text())="Export records"]]'
)

# Etapa 12 — Botão "Download" no modal de confirmação
# <div data-elem="button-label">Download</div> dentro de <button>
XPATH_BTN_DOWNLOAD = (
    '//button[.//div[@data-elem="button-label" '
    'and normalize-space(text())="Download"]]'
)


# -------------------------------------------------------------------------
# Utilitário: clicar_elemento
# -------------------------------------------------------------------------
def clicar_elemento(
    driver,
    wait: WebDriverWait,
    seletor: str,
    tipo: str = "css",
    descricao: str = "",
    js_click: bool = False,
) -> bool:
    """Localiza um elemento na página e executa clique direto (.click()).

    Usa `.click()` do Selenium em vez de focus()+ENTER, pois:
    - Checkboxes e labels requerem clique real para alternar estado.
    - Links <a> no Apollo respondem melhor a .click() do que a keypresses.
    - Em caso de interceptação por outro elemento, `js_click=True` aciona
      o clique via JavaScript, contornando overlays.

    Args:
        driver: Instância do WebDriver ativa.
        wait: Instância de WebDriverWait configurada com o timeout desejado.
        seletor: String do seletor CSS ou XPath.
        tipo: "css" para CSS Selector, "xpath" para XPath. Default: "css".
        descricao: Nome legível do elemento para logging. Default: seletor.
        js_click: Se True, executa o clique via JavaScript (contorna overlays).
            Default: False.

    Returns:
        True se o clique foi executado com sucesso, False em caso de erro.
    """
    by = By.CSS_SELECTOR if tipo == "css" else By.XPATH
    nome = descricao or seletor

    log.info(f"  → Localizando: {nome}...")
    try:
        elemento = wait.until(EC.element_to_be_clickable((by, seletor)))
    except TimeoutException:
        log.error(
            f"  ❌ Elemento não encontrado ou não clicável: {nome}\n"
            f"     Tipo: {tipo.upper()} | Seletor: {seletor}\n"
            f"     Verifique se a página carregou e se o seletor ainda é válido."
        )
        driver.save_screenshot(
            f"erro_{nome.replace(' ', '_').replace('/', '_').lower()}.png"
        )
        return False

    try:
        if js_click:
            driver.execute_script("arguments[0].click();", elemento)
            log.info(f"  ✅ Clique JS em: {nome}")
        else:
            elemento.click()
            log.info(f"  ✅ Clique em: {nome}")
    except Exception as e:
        # Fallback: tenta JS click se o clique direto falhar (ex: overlay)
        log.warning(f"  ⚠️  Clique direto falhou ({e}). Tentando JS click...")
        try:
            driver.execute_script("arguments[0].click();", elemento)
            log.info(f"  ✅ Clique JS (fallback) em: {nome}")
        except Exception as e2:
            log.error(f"  ❌ JS click também falhou em: {nome} — {e2}")
            driver.save_screenshot(
                f"erro_{nome.replace(' ', '_').lower()}.png"
            )
            return False

    return True


# -------------------------------------------------------------------------
# Utilitário: aguardar_download_concluir
# -------------------------------------------------------------------------
def aguardar_download_concluir(
    pasta_download: str,
    timeout: int = TIMEOUT_DOWNLOAD,
    extensao: str = ".csv",
    referencia_tempo: float = None,
) -> Optional[str]:
    """Aguarda até que um novo arquivo CSV apareça na pasta de download.

    Ignora arquivos .crdownload (Chrome ainda em progresso) e arquivos
    mais antigos que o instante de início da espera.

    Args:
        pasta_download: Caminho absoluto da pasta monitorada.
        timeout: Tempo máximo de espera em segundos. Default: 90.
        extensao: Extensão do arquivo esperado. Default: ".csv".
        referencia_tempo: Timestamp float (time.time()) usado como
            marco inicial. Se None, usa o momento da chamada.

    Returns:
        Caminho absoluto do arquivo mais recente encontrado, ou None.
    """
    inicio = referencia_tempo or time.time()
    log.info(f"[DOWNLOAD] Aguardando arquivo {extensao} em: {pasta_download}")

    while time.time() - inicio < timeout:
        candidatos = [
            f
            for f in glob.glob(os.path.join(pasta_download, f"*{extensao}"))
            if not f.endswith(".crdownload")
            and os.path.getctime(f) >= inicio
        ]
        if candidatos:
            mais_recente = max(candidatos, key=os.path.getctime)
            log.info(f"[DOWNLOAD] ✅ Arquivo recebido: {mais_recente}")
            return mais_recente
        time.sleep(1)

    log.error(
        f"[DOWNLOAD] ❌ Timeout: nenhum {extensao} encontrado em {timeout}s."
    )
    return None


# -------------------------------------------------------------------------
# Função principal de extração
# -------------------------------------------------------------------------
def extrair_contatos_por_step(
    nome_sequence: str,
    step_label: str = "Step: 1",
    download_dir: str = None,
    headless: bool = False,
    timeout: int = TIMEOUT_ELEMENTO,
) -> Optional[str]:
    """Acessa o Apollo.io e exporta contatos de um Step específico de uma Sequence.

    Executa as 11 etapas de navegação/interação descritas no módulo,
    desde a lista de Sequences até o download do CSV.

    Args:
        nome_sequence: Texto (parcial) do nome da Sequence a ser clicada
            na lista. Ex: "Presença Invisível" ou "[André] Presença".
        step_label: Rótulo exato do Step a filtrar, conforme exibido na UI.
            Ex: "Step: 1", "Step: 2". Default: "Step: 1".
        download_dir: Caminho absoluto da pasta onde o CSV será salvo.
            Se None, usa a pasta Downloads padrão do Windows.
        headless: Se True, Chrome roda sem interface gráfica.
            Use False na primeira execução para que o login seja visível.
        timeout: Tempo máximo (segundos) para aguardar cada elemento.

    Returns:
        Caminho completo do arquivo CSV baixado, ou None em caso de erro.
    """
    pasta = download_dir or str(Path.home() / "Downloads")

    log.info("=" * 60)
    log.info("  APOLLO SEQUENCE CONTACTS EXTRACT — Iniciando")
    log.info("=" * 60)
    log.info(f"  Sequence: {nome_sequence}")
    log.info(f"  Step:     {step_label}")
    log.info(f"  Download: {pasta}")
    log.info(f"  Headless: {headless}")
    log.info("=" * 60)

    driver = iniciar_chrome_driver(
        headless=headless,
        usar_perfil_visu=True,
        download_dir=pasta,
    )

    try:
        wait = WebDriverWait(driver, timeout)

        # ── PASSO 0: Verificar sessão e navegar para a lista de Sequences ─
        log.info("[0/11] Verificando sessão e navegando para Sequences...")
        if not verificar_e_configurar(driver, CAMINHO_PERFIL_VISU, URL_SEQUENCES_LIST):
            log.error("[EXTRACT] Sessão inválida. Extração cancelada.")
            return None

        # Aguarda a tabela de sequences renderizar
        try:
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div[role="gridcell"]')
            ))
        except TimeoutException:
            log.error("[0/12] ❌ Tabela de Sequences não renderizou.")
            driver.save_screenshot("erro_lista_sequences.png")
            return None
        log.info(f"[0/12] ✅ Lista de Sequences carregada.")

        # ── ETAPA 1: Clicar na Sequence alvo ─────────────────────────────
        log.info(f'[1/12] Clicando na Sequence: "{nome_sequence}"...')
        if not clicar_elemento(
            driver, wait,
            seletor=_xpath_sequence_link(nome_sequence),
            tipo="xpath",
            descricao=f"Sequence: {nome_sequence}",
        ):
            return None
        time.sleep(2)  # Aguarda SPA navegar para a página da Sequence

        # ── ETAPA 2: Aba "Contacts" ───────────────────────────────────────
        log.info("[2/12] Clicando na aba Contacts...")
        if not clicar_elemento(
            driver, wait,
            seletor=SELECTOR_TAB_CONTACTS,
            tipo="css",
            descricao="Aba Contacts",
        ):
            return None
        time.sleep(1)

        # ── ETAPA 3: Confirmar modal "Are you sure?" ──────────────────────
        # O Apollo exibe este modal ao trocar de aba com alterações não salvas.
        # Tentamos localizar o botão Confirm; se não aparecer dentro de 5s,
        # assumimos que o modal não foi exibido e seguimos normalmente.
        log.info("[3/12] Verificando modal de confirmação...")
        try:
            btn_confirm = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, XPATH_BTN_CONFIRM_MODAL))
            )
            btn_confirm.click()
            log.info("[3/12] ✅ Modal confirmado.")
        except TimeoutException:
            log.info("[3/12] ℹ️  Modal 'Are you sure?' não apareceu — seguindo.")
        time.sleep(2)  # Aguarda carregamento da lista de contatos

        # ── ETAPA 4: Botão "Show Filters" ────────────────────────────────
        log.info("[4/12] Abrindo painel de filtros...")
        if not clicar_elemento(
            driver, wait,
            seletor=SELECTOR_BTN_SHOW_FILTERS,
            tipo="css",
            descricao="Show Filters",
        ):
            return None
        time.sleep(1)

        # ── ETAPA 5: Accordion "Sequence Step" ───────────────────────────
        log.info("[5/12] Expandindo filtro Sequence Step...")
        if not clicar_elemento(
            driver, wait,
            seletor=XPATH_ACCORDION_SEQUENCE_STEP,
            tipo="xpath",
            descricao="Accordion Sequence Step",
        ):
            return None
        time.sleep(1)

        # ── ETAPA 6: Checkbox do Step alvo ───────────────────────────────
        log.info(f'[6/12] Selecionando filtro "{step_label}"...')
        if not clicar_elemento(
            driver, wait,
            seletor=_xpath_step_label(step_label),
            tipo="xpath",
            descricao=f"Checkbox {step_label}",
            js_click=True,  # Labels com checkbox requerem JS click no Apollo
        ):
            return None
        time.sleep(2)  # Aguarda a lista de contatos filtrar

        # ── ETAPA 7: Botão de seleção múltipla (bulk select) ─────────────
        log.info("[7/12] Clicando no botão de seleção múltipla...")
        if not clicar_elemento(
            driver, wait,
            seletor=SELECTOR_BTN_BULK_SELECT,
            tipo="css",
            descricao="Bulk Select Button",
        ):
            return None
        time.sleep(1)

        # ── ETAPA 8: "Select all people (N)" ─────────────────────────────
        log.info("[8/12] Selecionando todos os contatos...")
        if not clicar_elemento(
            driver, wait,
            seletor=SELECTOR_LINK_SELECT_ALL,
            tipo="css",
            descricao="Select all people",
        ):
            return None
        time.sleep(1)

        # ── ETAPA 9: Botão "More actions" (⋯) ────────────────────────────
        log.info("[9/12] Abrindo menu de ações (More actions)...")
        if not clicar_elemento(
            driver, wait,
            seletor=SELECTOR_BTN_MORE_ACTIONS,
            tipo="css",
            descricao="More Actions Button",
        ):
            return None
        time.sleep(1)

        # ── ETAPA 10: Opção "Export" no menu ─────────────────────────────
        log.info('[10/12] Clicando em "Export"...')
        if not clicar_elemento(
            driver, wait,
            seletor=XPATH_LINK_EXPORT,
            tipo="xpath",
            descricao="Menu Export",
        ):
            return None
        time.sleep(1.5)  # Aguarda o modal de exportação abrir

        # ── ETAPA 11: Botão "Export records" no modal ─────────────────────
        log.info('[11/12] Confirmando exportação ("Export records")...')
        if not clicar_elemento(
            driver, wait,
            seletor=XPATH_BTN_EXPORT_RECORDS,
            tipo="xpath",
            descricao="Export records",
        ):
            return None
        time.sleep(2)  # Aguarda o modal de download aparecer

        # ── ETAPA 12: Botão "Download" e aguarda o arquivo ────────────────
        log.info('[12/12] Clicando em "Download" e aguardando arquivo CSV...')
        ts_inicio_download = time.time()
        if not clicar_elemento(
            driver, wait,
            seletor=XPATH_BTN_DOWNLOAD,
            tipo="xpath",
            descricao="Download",
        ):
            return None

        caminho_csv = aguardar_download_concluir(
            pasta_download=pasta,
            timeout=TIMEOUT_DOWNLOAD,
            referencia_tempo=ts_inicio_download,
        )

        if caminho_csv:
            log.info(f"[12/12] ✅ Download concluído: {caminho_csv}")
        else:
            log.error("[12/12] ❌ Download não detectado dentro do tempo limite.")
            driver.save_screenshot("erro_download.png")

        return caminho_csv

    except Exception as e:
        log.error(f"[ERRO] Falha inesperada: {e}", exc_info=True)
        try:
            driver.save_screenshot("erro_inesperado.png")
        except Exception:
            pass
        return None

    finally:
        driver.quit()
        log.info("[EXTRACT] Navegador encerrado.")


# -------------------------------------------------------------------------
# Execução direta (teste)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    resultado = extrair_contatos_por_step(
        nome_sequence="Presença Invisível",
        step_label="Step: 1",
        headless=False,
    )
    if resultado:
        print(f"\n[OK] CSV exportado: {resultado}")
    else:
        print("\n[ERRO] Extração falhou. Verifique os logs e screenshots.")
