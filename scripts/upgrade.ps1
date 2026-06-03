<#
.SYNOPSIS
  Pull latest main, then rebuild either the development or production Docker stack.

.EXAMPLE
  .\scripts\upgrade.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-Location -Path (Join-Path $PSScriptRoot '..')

function Get-ComposeCommand {
  try {
    docker compose version *> $null
    if ($LASTEXITCODE -eq 0) { return @('docker', 'compose') }
  } catch {}
  if (Get-Command docker-compose -ErrorAction SilentlyContinue) { return @('docker-compose') }
  Write-Error 'Docker Compose is required but was not found.'
}

function Invoke-Compose([string[]]$Args) {
  $dc = Get-ComposeCommand
  & $dc[0] @($dc[1..($dc.Count - 1)] + $Args)
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

function Stop-DevFrontend {
  $dc = Get-ComposeCommand
  try {
    & $dc[0] @($dc[1..($dc.Count - 1)] + '-f', 'docker-compose.yml', 'stop', 'frontend') 2>$null
    & $dc[0] @($dc[1..($dc.Count - 1)] + '-f', 'docker-compose.yml', 'rm', '-f', 'frontend') 2>$null
  } catch {}
}

Write-Host '==> Pulling latest from origin/main...'
git pull origin main

Write-Host ''
Write-Host 'Which stack do you want to rebuild?'
Write-Host '  1) Development  (docker compose build && up -d)'
Write-Host '  2) Production   (prod compose build && up -d)'
Write-Host '  q) Skip rebuild (git pull only)'
$choice = Read-Host 'Choice [1/2/q]'

switch ($choice.Trim().ToLowerInvariant()) {
  { $_ -in '1', 'dev', 'development' } {
    Write-Host '==> Rebuilding development stack...'
    Invoke-Compose @('-f', 'docker-compose.yml', 'build')
    Invoke-Compose @('-f', 'docker-compose.yml', 'up', '-d')
    Write-Host 'Upgrade finished (development).'
  }
  { $_ -in '2', 'prod', 'production' } {
    Write-Host '==> Rebuilding production stack...'
    Stop-DevFrontend
    Invoke-Compose @('-f', 'docker-compose.yml', '-f', 'docker-compose.prod.yml', 'build')
    Invoke-Compose @('-f', 'docker-compose.yml', '-f', 'docker-compose.prod.yml', 'up', '-d')
    Write-Host 'Upgrade finished (production).'
  }
  { $_ -in 'q', 'quit', 'skip', '' } {
    Write-Host 'No stack was rebuilt.'
  }
  default {
    Write-Error 'Invalid choice. No stack was rebuilt.'
    exit 1
  }
}
