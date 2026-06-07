<#
  JPilot / NSAgent one-line bootstrap for Windows (PowerShell).

      irm https://raw.githubusercontent.com/Nexxus-Tech-SAS/jpilot/main/get.ps1 | iex

  Checks prerequisites, downloads the project, and launches the setup wizard.
  Override defaults with environment variables before running, e.g.:
      $env:JPILOT_DIR = "C:\apps\jpilot"; $env:JPILOT_REF = "main"
#>
$ErrorActionPreference = 'Stop'

$RepoUrl = if ($env:JPILOT_REPO) { $env:JPILOT_REPO } else { 'https://github.com/Nexxus-Tech-SAS/jpilot.git' }
$Ref     = if ($env:JPILOT_REF)  { $env:JPILOT_REF }  else { 'main' }
$Target  = if ($env:JPILOT_DIR)  { $env:JPILOT_DIR }  else { Join-Path (Get-Location) 'jpilot' }

function Info($m) { Write-Host "  $m" }
function Ok($m)   { Write-Host "  $([char]0x2713) $m" -ForegroundColor Green }
function Die($m)  { Write-Host "  $([char]0x2717) $m" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "JPilot / NSAgent installer" -ForegroundColor White
Write-Host ""

# ---- prerequisites ---------------------------------------------------------
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Die "git is required but not installed. Install Git for Windows (https://git-scm.com/download/win) and re-run."
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Host "  ! Docker is not installed (it's required to run JPilot)." -ForegroundColor Yellow
  $ans = Read-Host "  Try to install Docker Desktop automatically with winget? [y/N]"
  if ($ans -match '^(y|yes)$') {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
      Info "Installing Docker Desktop via winget..."
      winget install -e --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements
      Die "Docker Desktop was installed. It usually needs a sign-out or restart (and WSL2) to finish.
     Start Docker Desktop, wait for it to be ready, then re-run this command."
    }
    else {
      Die "winget was not found. Install Docker Desktop manually, then re-run:
       https://docs.docker.com/desktop/install/windows-install/"
    }
  }
  else {
    Die "Docker is required. Install Docker Desktop and re-run:
       https://docs.docker.com/get-docker/"
  }
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
  Die "Docker is installed but not running. Start Docker Desktop, wait for it to be ready, then re-run."
}

docker compose version *> $null
if ($LASTEXITCODE -ne 0 -and -not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
  Die "Docker Compose was not found. Install Docker Desktop (https://docs.docker.com/get-docker/)."
}
Ok "Docker is ready"

# ---- fetch the project -----------------------------------------------------
if (Test-Path (Join-Path $Target '.git')) {
  Info "Updating existing copy in $Target..."
  git -C $Target fetch --depth 1 origin $Ref *> $null
  git -C $Target checkout -q $Ref *> $null
  git -C $Target reset --hard "origin/$Ref" *> $null
  Ok "Updated to latest $Ref"
}
elseif (Test-Path $Target) {
  Die "$Target already exists and is not a JPilot checkout. Remove it or set `$env:JPILOT_DIR to another path."
}
else {
  Info "Downloading JPilot into $Target..."
  git clone --depth 1 --branch $Ref $RepoUrl $Target *> $null
  if ($LASTEXITCODE -ne 0) { Die "Clone failed. Check the repo URL/branch and your network." }
  Ok "Downloaded"
}

# ---- hand off to the orchestrator -----------------------------------------
Set-Location $Target
if (-not (Test-Path 'install.ps1')) { Die "install.ps1 not found in the project - unexpected layout." }

Write-Host ""
Info "Starting the setup wizard..."
Write-Host ""
& powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
