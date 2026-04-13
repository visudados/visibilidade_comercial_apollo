"""
common_setup.py - VISU Dados
=============================

Módulo responsável por gerenciar a navegação inicial e a validação de sessão
do Apollo.io utilizando o padrão de "Navegação Direta" (KISS).
"""

import time
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Constantes
# -------------------------------------------------------------------------
# Tempo máximo aguardando o usuário concluir o login manualmente (segundos).
# 180s (3 minutos) é ideal para digitação de credenciais e MFA/2FA do Google.
TIMEOUT_LOGIN_MANUAL = 180


# -------------------------------------------------------------------------
# Funções de Setup e Autenticação
# -------------------------------------------------------------------------

def aguardar_login_manual(driver, timeout: int = TIMEOUT_LOGIN_MANUAL) -> bool:
    """
    Monitora a URL atual até que o usuário conclua o login.
    Não força navegação, apenas observa a mudança de estado da página.
    """
    print()
    print("=" * 60)
    print("  LOGIN NECESSÁRIO — VISU Dados / Apollo.io")
    print("=" * 60)
    print("  O Apollo redirecionou para a página de login.")
    print("  Por favor:")
    print("    1. Vá para a janela do Chrome que acabou de abrir.")
    print("    2. Clique em 'Log in with Google'.")
    print("    3. Selecione a conta @visudados.com.br e confirme no celular se necessário.")
    print("    4. Aguarde o redirecionamento automático da página.")
    print(f"  Tempo limite: {timeout // 60} minutos.")
    print("=" * 60)
    print()

    inicio = time.time()
    while time.time() - inicio < timeout:
        url_atual = driver.current_url
        
        # Se a palavra 'login' sumir da URL e continuarmos no Apollo, o login foi feito.
        if "login" not in url_atual and "apollo.io" in url_atual:
            log.info(f"[SETUP] ✅ Login detectado automaticamente. URL atual: {url_atual}")
            print("  ✅ Login detectado com sucesso! Retomando automação...")
            print()
            return True
        
        time.sleep(2) # Aguarda 2 segundos antes de checar a URL novamente para não sobrecarregar

    log.error("[SETUP] ❌ Timeout: login não detectado no tempo limite.")
    print("  ❌ Tempo limite atingido. Feche a janela e execute o script novamente.\n")
    return False


def verificar_e_configurar(driver, caminho_perfil: Path, url_destino: str) -> bool:
    """
    Aplica o padrão de 'Navegação Direta'.
    Vai direto para a página alvo e reage dinamicamente ao roteamento do SPA do Apollo.
    """
    log.info("[SETUP] ── Iniciando Navegação ──────────────────────────")
    log.info(f"[SETUP] Acessando destino inicial: {url_destino}")
    
    # 1. Navega direto para a página que a automação precisa
    driver.get(url_destino)

    # 2. Mini-polling de 10 segundos
    # Dá tempo para o Single Page Application (SPA) decidir o roteamento (loading spinner).
    log.info("[SETUP] Verificando estado da sessão...")
    precisa_logar = False
    
    for _ in range(10):
        time.sleep(1)
        if "login" in driver.current_url:
            precisa_logar = True
            break

    # 3. Avalia a reação do site
    if precisa_logar:
        # O Apollo nos barrou e mandou pro login
        log.warning("[SETUP] Acesso negado. A sessão expirou ou não existe.")
        
        if not aguardar_login_manual(driver):
            return False
            
        # Após logar, o Apollo geralmente joga para a Home. 
        # Precisamos forçar a ida para a URL alvo novamente de forma limpa.
        log.info(f"[SETUP] Redirecionando de volta ao destino final: {url_destino}")
        driver.get(url_destino)
        
        # Dá um fôlego maior (5s) para o Apollo carregar a página pesada após um login recente
        time.sleep(5) 
        return True

    # Se passamos os 10 segundos e não caímos no login, assumimos que estamos logados e na página correta!
    log.info("[SETUP] ✅ Sessão validada sem intervenção. Destino alcançado diretamente.")
    return True