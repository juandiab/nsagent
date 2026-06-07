<#
.SYNOPSIS
  JPilot / NSAgent installer for Windows (PowerShell twin of install.sh).

.DESCRIPTION
  Starts the web setup wizard, waits for you to complete it in the browser, then
  launches the full stack. Run from the project root:

      .\install.ps1                 # first-time install
      .\install.ps1 -Reconfigure    # overwrite an existing .env via the wizard
#>
[CmdletBinding()]
param([switch]$Reconfigure)

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

$Sentinel          = '.installer-complete'
$InstallerCompose  = 'docker-compose.installer.yml'

function Fail($msg) { Write-Host "  $msg" -ForegroundColor Red; exit 1 }

function Format-Link($url) {
  $esc = [char]27
  if (-not [Console]::IsOutputRedirected) { "$esc]8;;$url$esc\$url$esc]8;;$esc\" } else { $url }
}

$dc = $null
try { docker compose version *> $null; if ($LASTEXITCODE -eq 0) { $dc = @('docker','compose') } } catch {}
if (-not $dc) {
  if (Get-Command docker-compose -ErrorAction SilentlyContinue) { $dc = @('docker-compose') }
}
if (-not $dc) { Fail "Docker Compose is required but was not found. Install Docker Desktop and re-run." }

function Compose { param([Parameter(ValueFromRemainingArguments=$true)]$Args)
  & $dc[0] @($dc[1..($dc.Count-1)] + $Args)
}

if ((Test-Path '.env') -and (-not $Reconfigure)) {
  Write-Host "A .env file already exists - this looks like a configured install."
  Write-Host "Re-run with '-Reconfigure' to overwrite it via the wizard, or start the"
  Write-Host "stack directly with:  .\compose.ps1 up -d"
  exit 1
}

if (Test-Path $Sentinel) { Remove-Item $Sentinel -Force }

$script:installerUp = $false
$script:domain = 'localhost'

function Cleanup-Installer {
  if ($script:installerUp) {
    Write-Host "`nShutting down the installer..."
    Compose '-f' $InstallerCompose 'down' *> $null
    $script:installerUp = $false
  }
}

function Test-JPilotReady([string]$BaseUrl) {
  [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
  try {
    foreach ($path in @('/api/health', '/')) {
      $resp = Invoke-WebRequest -Uri "$BaseUrl$path" -TimeoutSec 5 -UseBasicParsing
      if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 400) { return $true }
    }
  } catch { }
  finally { [System.Net.ServicePointManager]::ServerCertificateValidationCallback = $null }
  return $false
}

function Wait-JPilotReady([string]$BaseUrl) {
  $max = if ($env:JPILOT_WAIT_MAX) { [int]$env:JPILOT_WAIT_MAX } else { 300 }
  $interval = if ($env:JPILOT_WAIT_INTERVAL) { [int]$env:JPILOT_WAIT_INTERVAL } else { 2 }
  for ($i = 0; $i -lt $max; $i++) {
    if (Test-JPilotReady $BaseUrl) {
      Write-Host ""
      Write-Host "  [########################################] ready!"
      return $true
    }
    $cap = [math]::Floor($max * 0.9)
    $vis = [math]::Min($i, $cap)
    $filled = [math]::Floor($vis * 40 / $max)
    $bar = ('#' * $filled).PadRight(40, '.')
    $elapsed = $i * $interval
    $mins = [math]::Floor($elapsed / 60)
    $secs = $elapsed % 60
    Write-Host -NoNewline ("`r  [$bar] {0}m{1:D2}s  Starting JPilot services..." -f $mins, $secs)
    Start-Sleep -Seconds $interval
  }
  Write-Host ""
  return $false
}

try {
  Write-Host "Building and starting the setup wizard..."
  Compose '-f' $InstallerCompose 'up' '-d' '--build'
  $script:installerUp = $true

  Write-Host ""
  Write-Host "  +----------------------------------------------------------+"
  Write-Host "  |  JPilot setup is ready.                                  |"
  Write-Host "  +----------------------------------------------------------+"
  Write-Host ""
  Write-Host "   >  Open  $(Format-Link 'https://localhost:9443')"
  Write-Host ""
  Write-Host "  It uses a self-signed certificate, so your browser will show a"
  Write-Host "  security warning the first time - that is expected for the"
  Write-Host "  installer. Accept it to continue."
  Write-Host ""
  Write-Host "Waiting for you to finish the wizard (Ctrl-C to abort)..."

  while (-not (Test-Path $Sentinel)) { Start-Sleep -Seconds 2 }

  $script:domain = (Get-Content $Sentinel -TotalCount 1).Trim()
  if ([string]::IsNullOrWhiteSpace($script:domain)) { $script:domain = 'localhost' }

  Write-Host ""
  Write-Host "Configuration received."
  Write-Host "Keep the setup tab open in your browser - JPilot will open automatically when ready."

  $appUrl = "https://$($script:domain)"

  Write-Host ""
  Write-Host "  Building containers in the background (watch progress in your browser)..."
  & "$PSScriptRoot\compose.ps1" up -d --build

  Write-Host ""
  Write-Host "  Waiting for JPilot to finish starting..."
  $ready = Wait-JPilotReady $appUrl

  if ($ready) { Start-Sleep -Seconds 3 }

  Write-Host "Closing the setup wizard..."
  Cleanup-Installer
  if (Test-Path $Sentinel) { Remove-Item $Sentinel -Force }

  Write-Host ""
  if ($ready) {
    Write-Host "  JPilot is ready at  $(Format-Link $appUrl)" -ForegroundColor Green
  } else {
    Write-Host "  JPilot is still starting - open when ready:  $(Format-Link $appUrl)" -ForegroundColor Yellow
  }
  Write-Host ""
  Write-Host "  * Sign in with the admin account you created in the wizard."
  Write-Host "  * View logs with:   .\compose.ps1 logs -f"
  Write-Host "  * Stop with:        .\compose.ps1 down"
  Write-Host ""
}
catch {
  Cleanup-Installer
  throw
}
