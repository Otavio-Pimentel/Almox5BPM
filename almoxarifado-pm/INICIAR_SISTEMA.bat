@echo off
title Sistema de Almoxarifado PM - 5 BPM
color 0A

echo.
echo  ============================================
echo   SISTEMA DE ALMOXARIFADO - POLICIA MILITAR
echo  ============================================
echo.

:: 1. Entra na pasta correta do projeto
cd /d C:\5BPM\almoxarifado-pm\backend

:: 2. Verifica se o ambiente virtual existe
if not exist "..\venv" (
    echo [AVISO] Ambiente virtual nao encontrado. Criando...
    python -m venv ..\venv
)

:: 3. Garante que as pecas de seguranca estao instaladas
echo Verificando componentes de seguranca...
..\venv\Scripts\python.exe -m pip install python-jose[cryptography] passlib[bcrypt] cryptography fastapi uvicorn sqlalchemy >nul 2>&1

:: 4. Abre o navegador na tela de LOGIN (mais seguro)
echo.
echo Iniciando servidor...
start "" "http://localhost:8000/login"

:: 5. Lança o sistema
..\venv\Scripts\python.exe main.py

pause