@echo off
title NOVA SMS
cd /d "%~dp0"

echo.
echo   +------------------------------------------+
echo   :           N O V A   S M S                :
echo   :   Envio Inteligente de Mensajes          :
echo   +------------------------------------------+
echo.
echo  Inicializando...
echo.

:: Detectar Python con py (launcher) o python
set PY_CMD=
py -3 --version >nul 2>nul
if %errorlevel% equ 0 ( set PY_CMD=py -3 ) else (
    python --version >nul 2>nul
    if %errorlevel% equ 0 ( set PY_CMD=python ) else (
        python3 --version >nul 2>nul
        if %errorlevel% equ 0 ( set PY_CMD=python3 ) else (
            echo  [ERROR] Python no encontrado. Instala Python 3 desde python.org
            pause
            exit /b 1
        )
    )
)

echo  [OK] Python detectado: %PY_CMD%

:: Instalar dependencias si faltan (silencioso si ya estan)
echo  [*] Verificando dependencias...
%PY_CMD% -m pip install -q requests rich 2>nul
if %errorlevel% neq 0 (
    echo  [*] Instalando dependencias...
    %PY_CMD% -m pip install requests rich
)

echo  [*] Buscando Android en la red...
echo.
%PY_CMD% main.py
pause
