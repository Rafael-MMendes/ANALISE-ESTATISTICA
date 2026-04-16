@echo off
:: Iniciar_Coleta.bat
:: Executa os robos de coleta automatica (NEAC e CAD Consolidado)

cd /d "%~dp0"

echo STARTING > coleta_status.txt
echo [%date% %time%] Iniciando coleta NEAC... >> coleta_automatica.log
python coleta_neac.py >> coleta_automatica.log 2>&1

echo RUNNING_CAD > coleta_status.txt
echo [%date% %time%] Iniciando coleta CAD Consolidada... >> coleta_automatica.log
python coleta_cad_consolidada.py >> coleta_automatica.log 2>&1

echo [%date% %time%] Coleta completa finalizada. >> coleta_automatica.log
echo FINISHED > coleta_status.txt
