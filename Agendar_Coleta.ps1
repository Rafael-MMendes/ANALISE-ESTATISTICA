# Script para Agendar a Coleta Automática do Dashboard no Windows Task Scheduler
# Instrução: Salve como .ps1 e execute como Administrador.

$TaskName = "Coleta_Dashboard_9BPM"
$ActionScript = Join-Path $PSScriptRoot "Iniciar_Coleta.bat"
$Time = "08:00"

Write-Host "--- Configurando Agendamento de Coleta Automática (Windows) ---" -ForegroundColor Cyan

# Verifica se a tarefa já existe
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "Tarefa '$TaskName' já existe. Atualizando..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Cria a ação
$Action = New-ScheduledTaskAction -Execute $ActionScript -WorkingDirectory $PSScriptRoot

# Cria o gatilho (diário)
$Trigger = New-ScheduledTaskTrigger -Daily -At $Time

# Registra a tarefa (Usa o usuário logado para garantir que a janela apareça e peça o Token)
try {
    # -RunLevel Highest garante privilégios de administrador
    # -User $env:USERNAME garante que a tarefa rode no perfil do usuário atual
    Register-ScheduledTask -Action $Action -Trigger $Trigger -TaskName $TaskName -Description "Coleta automática (NEAC + CAD) para o Dashboard do 9º BPM." -User $env:USERNAME -RunLevel Highest
    Write-Host "`n[SUCESSO] Tarefa '$TaskName' agendada para as $Time diariamente." -ForegroundColor Green
    Write-Host "IMPORTANTE: A janela abrirá às $Time e você deverá digitar o Token do CAD."
} catch {
    Write-Host "`n[ERRO] Falha ao registrar tarefa. Tente rodar o terminal como ADMINISTRADOR." -ForegroundColor Red
    Write-Host $_.Exception.Message
}
