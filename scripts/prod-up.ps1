<#
.SYNOPSIS
  Build and start the production Docker Compose stack from the repository root.

.EXAMPLE
  .\scripts\prod-up.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-Location -Path (Join-Path $PSScriptRoot '..')

$composeArgs = @('-f', 'docker-compose.yml', '-f', 'docker-compose.prod.yml')

$dc = $null
try { docker compose version *> $null; if ($LASTEXITCODE -eq 0) { $dc = @('docker', 'compose') } } catch {}
if (-not $dc) {
  if (Get-Command docker-compose -ErrorAction SilentlyContinue) { $dc = @('docker-compose') }
}
if (-not $dc) { Write-Error 'Docker Compose is required but was not found.'; exit 1 }

function Invoke-Compose([string[]]$Extra) {
  & $dc[0] @($dc[1..($dc.Count - 1)] + $composeArgs + $Extra)
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

try {
  & $dc[0] @($dc[1..($dc.Count - 1)] + '-f', 'docker-compose.yml', 'stop', 'frontend') 2>$null
  & $dc[0] @($dc[1..($dc.Count - 1)] + '-f', 'docker-compose.yml', 'rm', '-f', 'frontend') 2>$null
} catch {}

Invoke-Compose @('build')
Invoke-Compose @('up', '-d')
