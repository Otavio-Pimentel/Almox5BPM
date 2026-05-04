@echo off
title Sistema de Almoxarifado PM
color 0A
echo.
echo  ============================================
echo   SISTEMA DE ALMOXARIFADO - POLICIA MILITAR
echo  ============================================
echo.
echo  Iniciando servidor...
echo  Aguarde o navegador abrir automaticamente.
echo.
echo  Para encerrar o sistema, feche esta janela.
echo  ============================================
echo.

cd C:\almoxarifado-pm\backend
cd backend

:: Verifica se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo        Instale o Python em: https://www.python.org/downloads/
    echo        Marque a opcao "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)

:: Instala dependencias se necessario
if not exist "..\venv" (
    echo Configurando ambiente pela primeira vez...
    python -m venv ..\venv
    echo Instalando dependencias...
    ..\venv\Scripts\pip install -r requirements.txt
    echo.
    echo [OK] Configuracao concluida!
    echo.
)

:: Inicia o servidor e abre o navegador
start "" "http://localhost:8000"
..\venv\Scripts\python main.py

pause
