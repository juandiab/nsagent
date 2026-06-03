<#
.SYNOPSIS
  Pull latest main, then optionally rebuild dev and/or production Docker stacks.

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

function Test-Yes([string]$Value) {
  switch ($Value.Trim().ToLowerInvariant()) {
    'y' { return $true }
    'yes' { return $true }
    default { return $false }
  }
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

$devAnswer = Read-Host 'Update development stack (docker compose build && up -d)? [y/N]'
$prodAnswer = Read-Host 'Update production stack (prod compose build && up -d)? [y/N]'

$updated = $false

if (Test-Yes $devAnswer) {
  Write-Host '==> Rebuilding development stack...'
  Invoke-Compose @('-f', 'docker-compose.yml', 'build')
  Invoke-Compose @('-f', 'docker-compose.yml', 'up', '-d')
  $updated = $true
}

if (Test-Yes $prodAnswer) {
  Write-Host '==> Rebuilding production stack...'
  Stop-DevFrontend
  Invoke-Compose @('-f', 'docker-compose.yml', '-f', 'docker-compose.prod.yml', 'build')
  Invoke-Compose @('-f', 'docker-compose.yml', '-f', 'docker-compose.prod.yml', 'up', '-d')
  $updated = $true
}

if (-not $updated) {
  Write-Host 'No stacks were rebuilt.'
} else {
  Write-Host 'Upgrade finished.'
}
