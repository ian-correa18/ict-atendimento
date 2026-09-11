@echo off
title ICT - Sistema de Atendimento
cd /d "%~dp0"

echo ==========================================
echo     ICT - SISTEMA DE ATENDIMENTO
echo ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo ERRO: Python nao foi encontrado neste computador.
    echo Instale o Python 3.11 ou superior e marque "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

echo Verificando dependencias...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERRO ao instalar as dependencias.
    echo Verifique sua conexao de rede e tente novamente.
    echo.
    pause
    exit /b 1
)

echo.
echo Iniciando o sistema...
echo.
echo Acesse: http://127.0.0.1:5000
echo Para outros computadores: http://IP-DESTE-PC:5000
echo.
echo NAO FECHE ESTA JANELA ENQUANTO O SISTEMA ESTIVER EM USO.
echo.

start "" http://127.0.0.1:5000

python app.py

echo.
echo O servidor foi encerrado.
pause
