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

# Build an OSC 8 terminal hyperlink (clickable) when output is a real console;
# fall back to the plain URL otherwise. Windows Terminal supports OSC 8.
function Format-Link($url) {
  $esc = [char]27
  if (-not [Console]::IsOutputRedirected) { "$esc]8;;$url$esc\$url$esc]8;;$esc\" } else { $url }
}

# ---- locate docker compose -------------------------------------------------
$dc = $null
try { docker compose version *> $null; if ($LASTEXITCODE -eq 0) { $dc = @('docker','compose') } } catch {}
if (-not $dc) {
  if (Get-Command docker-compose -ErrorAction SilentlyContinue) { $dc = @('docker-compose') }
}
if (-not $dc) { Fail "Docker Compose is required but was not found. Install Docker Desktop and re-run." }

function Compose { param([Parameter(ValueFromRemainingArguments=$true)]$Args)
  & $dc[0] @($dc[1..($dc.Count-1)] + $Args)
}

# ---- existing-install guard ------------------------------------------------
if ((Test-Path '.env') -and (-not $Reconfigure)) {
  Write-Host "A .env file already exists - this looks like a configured install."
  Write-Host "Re-run with '-Reconfigure' to overwrite it via the wizard, or start the"
  Write-Host "stack directly with:  $($dc -join ' ') up -d"
  exit 1
}

if (Test-Path $Sentinel) { Remove-Item $Sentinel -Force }

$installerUp = $false
function Cleanup {
  if ($script:installerUp) {
    Write-Host "`nShutting down the installer..."
    Compose '-f' $InstallerCompose 'down' *> $null
  }
}

try {
  # ---- launch the wizard ---------------------------------------------------
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

  # ---- wait for the wizard to finish ---------------------------------------
  while (-not (Test-Path $Sentinel)) { Start-Sleep -Seconds 2 }

  $domain = (Get-Content $Sentinel -TotalCount 1).Trim()
  if ([string]::IsNullOrWhiteSpace($domain)) { $domain = 'localhost' }

  Write-Host ""
  Write-Host "Configuration received. Stopping the installer..."
  Compose '-f' $InstallerCompose 'down' *> $null
  $script:installerUp = $false
}
finally {
  Cleanup
}

# ---- launch the real stack -------------------------------------------------
Write-Host "Launching JPilot..."
Compose 'up' '-d' '--build'

if (Test-Path $Sentinel) { Remove-Item $Sentinel -Force }

Write-Host ""
Write-Host "  JPilot is starting at  $(Format-Link "https://$domain")" -ForegroundColor Green
Write-Host ""
Write-Host "  * The first boot may take a few seconds while services come up."
Write-Host "  * Sign in with the admin account you just created."
Write-Host "  * View logs with:   $($dc -join ' ') logs -f"
Write-Host "  * Stop with:        $($dc -join ' ') down"
Write-Host ""

# ---- open the app in a browser (best effort) -------------------------------
# Only auto-open for a local install; set $env:JPILOT_NO_OPEN=1 to disable.
if ((-not $env:JPILOT_NO_OPEN) -and ($domain -eq 'localhost' -or $domain -like '127.*' -or $domain -eq '::1')) {
  [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
  Write-Host -NoNewline "  Waiting for JPilot to be ready"
  $opened = $false
  for ($i = 0; $i -lt 60; $i++) {
    try {
      Invoke-WebRequest -Uri 'https://localhost/' -TimeoutSec 2 -UseBasicParsing *> $null
      Write-Host " done.`n  Opening your browser..."
      Start-Process "https://$domain"
      $opened = $true
      break
    } catch { Write-Host -NoNewline '.'; Start-Sleep -Seconds 2 }
  }
  if (-not $opened) { Write-Host "`n  Still starting - open the link above when ready." }
  [System.Net.ServicePointManager]::ServerCertificateValidationCallback = $null
  Write-Host ""
}
