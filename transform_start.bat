@echo off
:: ============================================================
::  VISU Dados — transform_start.bat
::  Módulo de Transformação (ETL) e atualização do Parquet
:: ============================================================
SETLOCAL ENABLEDELAYEDEXPANSION
chcp 65001 >nul
title VISU — Apollo Transform (Parquet)

echo.
echo  ====================================================
echo   VISU Dados — Apollo Data Transformation (ETL)
echo  ====================================================
echo.
timeout /t 2 /nobreak >nul

SET "SCRIPT_DIR=%~dp0"
SET "PYTHON_DIR=%SCRIPT_DIR%python"

:: ── PASSO 1: Sincronizar Dependências (Agora com Pandas!) ─────
echo  [1/2] Verificando ambiente e dependencias...
cd /d "%PYTHON_DIR%"

uv sync
IF %ERRORLEVEL% NEQ 0 (
    echo  [ERRO] Falha ao sincronizar o ambiente.
    pause
    exit /b 1
)
echo  [1/2] Dependencias: OK

:: ── PASSO 2: Executar Transformação ───────────────────────────
echo.
echo  [2/2] Iniciando processamento dos dados...
echo.

uv run python projects\transform\transform_apollo_contacts.py
SET RESULT=%ERRORLEVEL%

IF %RESULT% EQU 0 (
    :: Silent Success
    exit /b 0
) ELSE (
    echo.
    echo  =============================================================
    echo   Ocorreu um erro durante a transformacao dos dados.
    echo   Verifique o console para mais detalhes.
    echo  =============================================================
    pause
    exit /b 1
)