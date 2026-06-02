#requires -Version 5.1
<#
.SYNOPSIS
  Impede o PC de dormir/hibernar enquanto este script estiver rodando.

.DESCRIPTION
  Usa Win32 SetThreadExecutionState para sinalizar pro Windows que o
  sistema esta ocupado. Eficaz mesmo quando "Suspender: Nunca" nao funciona
  (Modern Standby, hibernacao agressiva, etc).

  Rode em um PowerShell separado e deixe aberto durante treinos longos:
    powershell -ExecutionPolicy Bypass -File scripts\keepalive.ps1

  Pra parar: Ctrl+C ou fechar a janela.
#>

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public class PowerControl {
    [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern uint SetThreadExecutionState(uint esFlags);

    public const uint ES_CONTINUOUS        = 0x80000000;
    public const uint ES_SYSTEM_REQUIRED   = 0x00000001;
    public const uint ES_DISPLAY_REQUIRED  = 0x00000002;
    public const uint ES_AWAYMODE_REQUIRED = 0x00000040;
}
"@

# ES_CONTINUOUS = persiste ate ser desfeito
# ES_SYSTEM_REQUIRED = sistema fica acordado
# ES_AWAYMODE_REQUIRED = modo "away" (sistema responde mesmo de tela apagada)
$flags = [PowerControl]::ES_CONTINUOUS -bor `
         [PowerControl]::ES_SYSTEM_REQUIRED -bor `
         [PowerControl]::ES_AWAYMODE_REQUIRED

[void][PowerControl]::SetThreadExecutionState($flags)

Write-Host ""
Write-Host "==================================" -ForegroundColor Green
Write-Host " PC nao vai dormir enquanto este " -ForegroundColor Green
Write-Host " terminal estiver aberto.         " -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""
Write-Host "Pra parar: Ctrl+C ou fechar." -ForegroundColor Gray
Write-Host ""

try {
    while ($true) {
        # Reforca a cada 60s (defesa contra timeouts internos do Win)
        [void][PowerControl]::SetThreadExecutionState($flags)
        Start-Sleep -Seconds 60
        Write-Host "$(Get-Date -Format 'HH:mm:ss') | keepalive ativo" -ForegroundColor DarkGray
    }
} finally {
    # Restaura comportamento normal
    [void][PowerControl]::SetThreadExecutionState([PowerControl]::ES_CONTINUOUS)
    Write-Host "Keepalive encerrado. PC pode voltar a dormir." -ForegroundColor Yellow
}
