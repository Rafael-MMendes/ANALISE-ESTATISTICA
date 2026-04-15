@echo off
title Dashboard P3 - 9 BPM
echo ==========================================
echo   DASHBOARD P3 - 9 BPM
echo ==========================================
echo   Iniciando o servidor do painel interativo...
echo   Por favor, nao feche esta janela
echo   enquanto usa o painel.
echo.
cd /d "%~dp0"
start cmd /c "streamlit run app.py"
timeout /t 5 /nobreak >nul
start http://localhost:8501
exit