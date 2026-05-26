#requires -Version 5.1
<#
.SYNOPSIS
  Atualiza o Raspberry Pi com a versao mais recente dos arquivos modificados
  (tracking + dedup IOU + CORS) e reinicia o main.py.

.DESCRIPTION
  Roda do PowerShell do PC. Vai pedir a senha do `lorenzo` no Pi tres vezes
  (uma por arquivo). Depois reinicia o main.py em modo headless dentro de tmux.

.PARAMETER PiHost
  IP ou hostname do Pi. Padrao: 10.0.1.121
#>
param(
    [string]$PiHost = "10.0.1.121",
    [string]$PiUser = "lorenzo",
    [string]$PiPath = "projetos/residuos-ai"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent

$arquivos = @(
    "api/routes.py",
    "core/turno.py",
    "ml/modelo.py",
    "ml/bytetrack_residuos.yaml"
)

Write-Host ""
Write-Host "==> Atualizando $PiUser@${PiHost}:$PiPath" -ForegroundColor Cyan
Write-Host ""

foreach ($arq in $arquivos) {
    $origem = Join-Path $repo $arq.Replace('/', '\')
    if (-not (Test-Path $origem)) {
        Write-Host "PULADO (arquivo nao existe localmente): $arq" -ForegroundColor Yellow
        continue
    }
    $destPath = "$PiPath/$($arq.Replace('\','/').Substring(0, $arq.LastIndexOf('/')))/"
    Write-Host "scp $arq -> $PiUser@${PiHost}:$destPath" -ForegroundColor Gray
    & scp $origem "${PiUser}@${PiHost}:$destPath"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FALHOU em $arq (codigo $LASTEXITCODE)" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "==> Reiniciando main.py no Pi (headless)" -ForegroundColor Cyan
Write-Host ""

$remoteCmd = @"
pkill -f main.py 2>/dev/null; sleep 2;
cd ~/$PiPath && source .venv/bin/activate && \
  tmux kill-session -t residuos 2>/dev/null; \
  tmux new -d -s residuos 'python main.py --headless'; \
  sleep 3; \
  echo '---'; \
  tmux capture-pane -t residuos -p | tail -20
"@

& ssh "${PiUser}@${PiHost}" $remoteCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "OK — Pi atualizado e rodando." -ForegroundColor Green
    Write-Host ""
    Write-Host "Para ver os logs ao vivo:" -ForegroundColor Gray
    Write-Host "  ssh $PiUser@$PiHost"
    Write-Host "  tmux attach -t residuos"
    Write-Host ""
    Write-Host "Para sair do tmux sem matar: Ctrl+B solta D" -ForegroundColor Gray
} else {
    Write-Host "FALHOU reiniciar (codigo $LASTEXITCODE)" -ForegroundColor Red
    exit 1
}
