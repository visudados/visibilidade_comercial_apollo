@echo off
:: ============================================================
::  VISU Dados — iniciar_apollo_contacts.bat
::  Duplo-clique para executar a extração de contatos por Step.
::  Verifica e instala o ambiente automaticamente se necessário.
:: ============================================================
SETLOCAL ENABLEDELAYEDEXPANSION
title VISU — Apollo Sequence Contacts Extractor

echo.
echo  ====================================================
echo   VISU Dados — Apollo Sequence Contacts Extractor
echo  ====================================================
echo.
timeout /t 2 /nobreak >nul

SET "SCRIPT_DIR=%~dp0"
SET "PYTHON_DIR=%SCRIPT_DIR%python"
SET "VENV_DIR=%PYTHON_DIR%\.venv"

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
IF %ERRORLEVEL% NEQ 0 (
    echo         uv nao encontrado. Instalando automaticamente...
    powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    IF !ERRORLEVEL! NEQ 0 (
        echo  [ERRO] Falha ao instalar o uv.
        pause
        exit /b 1
    )
    SET "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.cargo\bin;%PATH%"
    where uv >nul 2>&1
    IF !ERRORLEVEL! NEQ 0 (
        echo  [AVISO] Feche esta janela, abra uma nova e execute novamente.
        pause
        exit /b 1
    )
    echo  [1/4] uv instalado com sucesso.
) ELSE (
    echo  [1/4] uv: OK
)
timeout /t 2 /nobreak >nul

:: ── PASSO 2: Verificar ambiente virtual ───────────────────────
echo  [2/4] Verificando ambiente virtual Python (.venv)...
cd /d "%PYTHON_DIR%"

IF EXIST "%VENV_DIR%" (
    echo  [2/4] Ambiente virtual: JA EXISTE em python\.venv
) ELSE (
    echo         Criando ambiente virtual...
    uv sync
    IF !ERRORLEVEL! NEQ 0 (
        echo  [ERRO] Falha ao criar o ambiente virtual.
        pause
        exit /b 1
    )
    echo  [2/4] Ambiente virtual criado com sucesso.
)
timeout /t 2 /nobreak >nul

:: ── PASSO 3: Sincronizar dependencias ─────────────────────────
echo  [3/4] Verificando dependencias Python...
uv sync
IF %ERRORLEVEL% NEQ 0 (
    echo  [ERRO] Falha ao sincronizar dependencias.
    pause
    exit /b 1
)
echo  [3/4] Dependencias: OK
timeout /t 2 /nobreak >nul

:: ── PASSO 4: Executar a automacao ─────────────────────────────
echo  [4/4] Iniciando Apollo Sequence Contacts Extractor...
echo.

uv run python projects\run_apollo_sequence_contacts.py
SET RESULT=%ERRORLEVEL%

echo.
IF %RESULT% EQU 0 (
    echo  ====================================================
    echo   Concluido com sucesso!
    echo   O CSV foi salvo na pasta Downloads do Windows.
    echo  ====================================================
    echo.
    timeout /t 5 /nobreak >nul
) ELSE (
    echo  ====================================================
    echo   Ocorreu um erro durante a execucao.
    echo.
    echo   Arquivos de diagnostico (pasta python\projects):
    echo     apollo_sequence_contacts_extract.log
    echo     erro_*.png  (screenshot do momento do erro)
    echo  ====================================================
    echo.
    pause
)

ENDLOCAL
