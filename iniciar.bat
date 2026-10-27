@echo off
chcp 65001 >nul
title CRM Comercial OA
cd /d "%~dp0"

echo ============================================
echo        CRM Comercial OA - iniciando
echo ============================================
echo.

REM Verifica se o Python esta instalado
where python >nul 2>nul
if errorlevel 1 (
  echo [!] Python nao encontrado no seu computador.
  echo     Instale em: https://www.python.org/downloads/
  echo     IMPORTANTE: na instalacao, marque a caixa "Add Python to PATH".
  echo.
  pause
  exit /b
)

REM Na primeira vez, cria o ambiente e instala o Flask (pode demorar 1-2 min)
if not exist ".venv\Scripts\activate.bat" (
  echo Primeira execucao: preparando o sistema, aguarde...
  python -m venv .venv
  call ".venv\Scripts\activate.bat"
  python -m pip install --upgrade pip
  pip install -r requirements.txt
) else (
  call ".venv\Scripts\activate.bat"
)

echo.
echo ============================================
echo  Abra o navegador em:  http://localhost:5000
echo  Para desligar: feche esta janela ou Ctrl+C
echo ============================================
echo.

python run.py
pause
