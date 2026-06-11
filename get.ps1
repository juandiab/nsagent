<#
  JPilot / NSAgent one-line bootstrap for Windows (PowerShell).

      irm https://raw.githubusercontent.com/Nexxus-Tech-SAS/jpilot/main/get.ps1 | iex

  Checks prerequisites, downloads JPilot to the user profile folder, and launches the setup wizard.
#>
$ErrorActionPreference = 'Stop'

$RepoUrl = if ($env:JPILOT_REPO) { $env:JPILOT_REPO } else { 'https://github.com/Nexxus-Tech-SAS/jpilot.git' }
$Ref     = if ($env:JPILOT_REF)  { $env:JPILOT_REF }  else { 'main' }

# When run as `irm ... | iex`, this script executes inside the current
# PowerShell session, so a bare `exit` terminates the host and closes the
# window before any error can be read. Pause on failure when interactive so the
# message stays on screen; skip the pause under automation (CI / non-interactive).
$Interactive = [Environment]::UserInteractive -and -not $env:CI

function Info($m) { Write-Host "  $m" }
function Ok($m)   { Write-Host "  $([char]0x2713) $m" -ForegroundColor Green }
function Warn($m) { Write-Host "  ! $m" -ForegroundColor Yellow }
function Die($m)  {
  Write-Host "  $([char]0x2717) $m" -ForegroundColor Red
  if ($Interactive) { Read-Host "`n  Press Enter to close" | Out-Null }
  exit 1
}

# Ask a yes/no question; default No. Returns $true only on an explicit yes.
function Ask-YesNo($q) {
  if (-not $Interactive) { return $false }
  return (Read-Host "  $q [y/N]") -match '^(y|yes)$'
}

# winget installs into the machine/user PATH, but the current session keeps its
# old PATH. Rebuild $env:Path from the registry so a freshly installed tool is
# visible without re-launching PowerShell.
function Update-SessionPath {
  $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
  $user    = [Environment]::GetEnvironmentVariable('Path', 'User')
  $env:Path = (@($machine, $user) | Where-Object { $_ }) -join ';'
}

function Get-DefaultInstallDir {
  if ($env:USERPROFILE) { return (Join-Path $env:USERPROFILE 'jpilot') }
  return (Join-Path (Get-Location) 'jpilot')
}

function Resolve-InstallPath([string]$Path) {
  if ($Path -match '^~[\\/]?$') { return $env:USERPROFILE }
  if ($Path -match '^~[\\/](.+)$') { return (Join-Path $env:USERPROFILE $Matches[1]) }
  return $Path
}

function Ask-InstallDir {
  if ($env:JPILOT_DIR) { return (Resolve-InstallPath $env:JPILOT_DIR) }
  $default = Get-DefaultInstallDir
  if (Test-Path (Join-Path $default '.git')) {
    Info "Using existing install at $default."
    return $default
  }
  if (-not $Interactive) { return $default }
  Write-Host ""
  Info "Where should JPilot be downloaded on this PC?"
  Info "Pick a folder you can write to. Press Enter for the default, or type another path"
  Info "(for example D:\jpilot — protected folders may need an Administrator prompt once)."
  $choice = Read-Host "  Install folder [$default]"
  if ([string]::IsNullOrWhiteSpace($choice)) { return $default }
  return (Resolve-InstallPath $choice.Trim())
}

function Ensure-InstallDir([string]$Path) {
  if ((Test-Path $Path) -and -not (Test-Path $Path -PathType Container)) {
    Die "$Path exists but is not a folder."
  }
  if (Test-Path $Path -PathType Container) { return }
  try {
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
    return
  }
  catch {
    Warn "That location needs Administrator rights (common under Program Files or C:\)."
    if (-not (Ask-YesNo "Create $Path and give you access (Administrator prompt)?")) {
      Die "Cannot use $Path. Pick a folder you can write to — the default in your profile works."
    }
    $cmd = "New-Item -ItemType Directory -Path '$Path' -Force | Out-Null; " +
           "icacls '$Path' /grant '$env:USERNAME:(OI)(CI)F' /T"
    Start-Process powershell -Verb RunAs -Wait -ArgumentList @('-NoProfile', '-Command', $cmd) | Out-Null
    if (-not (Test-Path $Path -PathType Container)) {
      Die "Could not create $Path. Try the default folder or run PowerShell as Administrator."
    }
    Ok "Created $Path"
  }
}

Write-Host ""
Write-Host "JPilot / NSAgent installer" -ForegroundColor White
Write-Host ""
Info "Published by Nexxus-Tech SAS - https://nexxus-tech.com"
Info "Source code: $RepoUrl (branch: $Ref)"
Info "This script downloads JPilot from the repository above, then runs its setup wizard."
Info "Read it first: https://raw.githubusercontent.com/Nexxus-Tech-SAS/jpilot/$Ref/get.ps1"
Info "Need help or run into trouble? Contact us at https://www.nexxus-tech.com or support@nexxus-tech.com"
Write-Host ""

# ---- prerequisites ---------------------------------------------------------
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Warn "Git is not installed (it's required to download JPilot)."
  Info "JPilot can install it via winget (Windows Package Manager), which fetches the"
  Info "official 'Git.Git' package from Microsoft's catalog. Windows may show an"
  Info "Administrator (UAC) approval prompt - accept it to continue."
  Info "Prefer to do it yourself? Install from https://git-scm.com/download/win and re-run."
  if (Ask-YesNo "Install Git for Windows now with winget?") {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
      Info "Installing Git for Windows via winget..."
      winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements
      Update-SessionPath
      if (Get-Command git -ErrorAction SilentlyContinue) {
        Ok "Git installed"
      }
      else {
        Die "Git was installed but isn't on this session's PATH yet.
     Close this window, open a new PowerShell, and re-run this command."
      }
    }
    else {
      Die "winget was not found (it needs a recent Windows 10/11). Install Git for Windows
     manually, then re-run: https://git-scm.com/download/win"
    }
  }
  else {
    Die "Git is required. Install Git for Windows and re-run:
       https://git-scm.com/download/win"
  }
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Warn "Docker is not installed (it's required to run JPilot)."
  Info "JPilot can install it via winget (Windows Package Manager), which fetches the"
  Info "official 'Docker.DockerDesktop' package from Microsoft's catalog. Windows may"
  Info "show an Administrator (UAC) approval prompt - accept it to continue."
  Info "Prefer to do it yourself? Install from"
  Info "https://docs.docker.com/desktop/install/windows-install/ and re-run."
  if (Ask-YesNo "Install Docker Desktop now with winget?") {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
      Info "Installing Docker Desktop via winget..."
      winget install -e --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements
      Die "Docker Desktop was installed. It usually needs a sign-out or restart (and WSL2) to finish.
     Start Docker Desktop, wait for it to be ready, then re-run this command."
    }
    else {
      Die "winget was not found (it needs a recent Windows 10/11). Install Docker Desktop
     manually, then re-run: https://docs.docker.com/desktop/install/windows-install/"
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

$Target = Ask-InstallDir
Ensure-InstallDir $Target

# ---- fetch the project -----------------------------------------------------
if (Test-Path (Join-Path $Target '.git')) {
  Info "Updating existing copy in $Target..."
  git -C $Target fetch --depth 1 origin $Ref *> $null
  git -C $Target checkout -q $Ref *> $null
  git -C $Target reset --hard "origin/$Ref" *> $null
  Ok "Updated to latest $Ref"
}
elseif (Test-Path $Target) {
  Die "$Target already exists and is not a JPilot checkout. Remove that folder and re-run this installer."
}
else {
  Info "Downloading JPilot into $Target..."
  git clone --depth 1 --branch $Ref $RepoUrl $Target 2>&1 | Out-Null
  if ($LASTEXITCODE -ne 0) { Die "Clone failed. Check your network and try again." }
  Ok "Downloaded"
}

# ---- hand off to the orchestrator -----------------------------------------
Set-Location $Target
if (-not (Test-Path 'install.ps1')) { Die "install.ps1 not found in the project - unexpected layout." }

Write-Host ""
Info "Starting the setup wizard..."
Write-Host ""
& powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
