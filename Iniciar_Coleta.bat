@echo off
:: Iniciar_Coleta.bat
:: Executa os robos de coleta automatica (NEAC e CAD Consolidado)

cd /d "%~dp0"

echo STARTING > coleta_status.txt
echo [%date% %time%] Iniciando coleta NEAC... >> logs\coleta_automatica.log
python coleta\coleta_neac.py >> logs\coleta_automatica.log 2>&1

echo RUNNING_CAD > coleta_status.txt
echo [%date% %time%] Iniciando coleta CAD Consolidada... >> logs\coleta_automatica.log
python coleta\coleta_cad_consolidada.py >> logs\coleta_automatica.log 2>&1

echo [%date% %time%] Coleta completa finalizada. >> logs\coleta_automatica.log
echo FINISHED > coleta_status.txt
