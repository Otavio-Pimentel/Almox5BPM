@echo off
title Sistema Almoxarifado PM - Gestor Inteligente
color 0A

:: 1. Define a pasta do projeto
cd /d %~dp0

echo ============================================
echo   SISTEMA DE ALMOXARIFADO - POLICIA MILITAR
echo ============================================

:: 2. Verifica se a pasta venv existe, se nao, cria
if not exist "venv\Scripts\python.exe" (
    echo [AVISO] Ambiente virtual nao encontrado. Criando...
    python -m venv venv
)

:: 3. TESTE DE FOGO: O Django esta instalado no venv?
echo [INFO] Verificando integridade dos componentes...
venv\Scripts\python.exe -c "import django" >nul 2>&1

if %errorlevel% neq 0 (
    echo [ALERTA] Componentes faltando. Iniciando instalacao completa...
    venv\Scripts\python.exe -m pip install --upgrade pip
    :: ADICIONADO: django-simple-history na lista abaixo
    venv\Scripts\python.exe -m pip install django djangorestframework djangorestframework-simplejwt django-filter django-cors-headers django-simple-history
    echo [OK] Dependencias instaladas com sucesso.
) else (
    :: Checagem extra para o simple-history especificamente
    venv\Scripts\python.exe -c "import simple_history" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [REPARO] Instalando modulo de historico...
        venv\Scripts\python.exe -m pip install django-simple-history
    )
    echo [OK] Todos os componentes estao prontos.
)

:: 4. Sincroniza o Banco de Dados (Migrações)
echo [INFO] Sincronizando banco de dados...
venv\Scripts\python.exe manage.py migrate --noinput

:: 5. Abre o navegador e lanca o sistema
echo.
echo ============================================
echo   SISTEMA PRONTO! LIGANDO MOTORES...
echo ============================================
start "" "http://127.0.0.1:8000/login/"
venv\Scripts\python.exe manage.py runserver

pause