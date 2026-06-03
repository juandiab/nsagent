<#
.SYNOPSIS
  Run Docker Compose using the stack file that matches NSAGENT_DEPLOY_MODE in .env.

.EXAMPLE
  .\compose.ps1 up -d
  .\compose.ps1 logs -f backend-api
  .\compose.ps1 down
#>
[CmdletBinding()]
param([Parameter(ValueFromRemainingArguments = $true)][object[]]$Args)

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

$composeArgs = @('-f', 'docker-compose.yml')

if (Test-Path '.env') {
  $modeLine = Get-Content '.env' | Where-Object { $_ -match '^\s*NSAGENT_DEPLOY_MODE\s*=' } | Select-Object -First 1
  if ($modeLine -match '=\s*prod\s*$') {
    $composeArgs = @('-f', 'docker-compose.yml', '-f', 'docker-compose.prod.yml')
    try {
      & docker compose -f docker-compose.yml stop frontend 2>$null
      & docker compose -f docker-compose.yml rm -f frontend 2>$null
    } catch {}
  }
}

$dc = $null
try { docker compose version *> $null; if ($LASTEXITCODE -eq 0) { $dc = @('docker','compose') } } catch {}
if (-not $dc) {
  if (Get-Command docker-compose -ErrorAction SilentlyContinue) { $dc = @('docker-compose') }
}
if (-not $dc) { Write-Error 'Docker Compose is required but was not found.'; exit 1 }

& $dc[0] @($dc[1..($dc.Count-1)] + $composeArgs + $Args)
exit $LASTEXITCODE
