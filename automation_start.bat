@echo off
:: ============================================================
::  VISU Dados — iniciar_apollo_contacts.bat
:: ============================================================
SETLOCAL ENABLEDELAYEDEXPANSION
:: Força o terminal a usar UTF-8
chcp 65001 >nul
title VISU — Apollo Sequence Contacts Extractor

echo.
echo  ====================================================
echo   VISU Dados — Apollo Sequence Contacts Extractor
echo  ====================================================
echo.
timeout /t 2 /nobreak >nul

SET "SCRIPT_DIR=%~dp0"
SET "PYTHON_DIR=%SCRIPT_DIR%python"

IF NOT EXIST "%PYTHON_DIR%\pyproject.toml" (
    echo  [ERRO] Pasta "python" ou pyproject.toml nao encontrado.
    echo  Certifique-se de que o .bat esta na raiz do repositorio.
    echo.
    pause
    exit /b 1
)

:: ── PASSO 1: Verificar uv ─────────────────────────────────────
echo  [1/4] Verificando gerenciador de ambiente (uv)...
where uv >nul 2>&1
:: Se o uv já existir, pula toda a instalação e vai direto para UV_INSTALADO
IF %ERRORLEVEL% EQU 0 GOTO UV_INSTALADO

echo         uv nao encontrado. Instalando via WinGet (Metodo Seguro/Sem AV)...
winget install --id=astral-sh.uv -e --accept-source-agreements --accept-package-agreements

IF !ERRORLEVEL! NEQ 0 (
    echo.
    echo  [ERRO] Falha ao instalar o uv via WinGet.
    echo  Por favor, instale manualmente em: https://docs.astral.sh/uv/
    echo.
    pause
    exit /b 1
)

:: A MÁGICA DA SESSÃO ÚNICA (Fora do bloco IF para não quebrar o CMD)
for /f "tokens=2*" %%A in ('reg query HKCU\Environment /v Path 2^>nul ^| find /i "Path"') do set "USER_PATH=%%B"
set "PATH=!USER_PATH!;%PATH%"

where uv >nul 2>&1
IF !ERRORLEVEL! NEQ 0 (
    echo.
    echo  [ERRO FATAL] Nao foi possivel carregar o uv na sessao atual.
    echo  Feche esta janela, abra uma nova e tente rodar o script novamente.
    pause
    exit /b 1
)
echo  [1/4] uv instalado e reconhecido automaticamente!

:UV_INSTALADO
echo  [1/4] uv: OK
timeout /t 1 /nobreak >nul


:: ── PASSO 2 e 3: Ambiente Virtual e Sincronização ─────────────
echo.
echo  [2/4] Preparando ambiente virtual Python e dependencias...
cd /d "%PYTHON_DIR%"

:: uv sync é inteligente: cria o .venv (se nao existir) e instala o pyproject.toml
uv sync
IF %ERRORLEVEL% NEQ 0 (
    echo  [ERRO] Falha ao criar ambiente ou sincronizar dependencias.
    pause
    exit /b 1
)
echo  [3/4] Ambiente e dependencias: OK
timeout /t 1 /nobreak >nul


:: ── PASSO 4: Executar Automação ───────────────────────────────
echo.
echo  [4/4] Iniciando o robo do Apollo...
echo.
echo  =============================================================
echo  A automacao assumira o controle do navegador a partir de agora.
echo  Se for seu primeiro acesso, voce tera 3 minutos para logar.
echo  =============================================================
echo.

:: O uv run garante que o script rode usando o Python isolado correto
uv run python projects\run_apollo_sequence_contacts.py
SET RESULT=%ERRORLEVEL%

IF %RESULT% EQU 0 (
    :: Filosofia "Silent Success": se deu certo, apenas fecha a janela sem pedir ENTER.
    exit /b 0
) ELSE (
    echo.git 
    echo  =============================================================
    echo   Ocorreu um erro durante a execucao. 
    echo   Verifique o log e as imagens de erro na pasta python/projects
    echo  =============================================================
    :: Mantemos o pause APENAS no erro, para dar tempo do usuário ler o que houve.
    pause
    exit /b 1
)