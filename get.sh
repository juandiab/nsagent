#!/usr/bin/env sh
# JPilot / NSAgent one-line bootstrap for macOS & Linux.
#
#   curl -fsSL https://raw.githubusercontent.com/Nexxus-Tech-SAS/jpilot/main/get.sh | bash
#
# It checks prerequisites, downloads the project, and launches the setup wizard.
# Override defaults with environment variables, e.g.:
#   curl -fsSL .../get.sh | JPILOT_DIR=~/apps/jpilot JPILOT_REF=main bash
set -eu

REPO_URL="${JPILOT_REPO:-https://github.com/Nexxus-Tech-SAS/jpilot.git}"
REF="${JPILOT_REF:-main}"
TARGET="${JPILOT_DIR:-$(pwd)/jpilot}"

# ---- pretty output ---------------------------------------------------------
if [ -t 1 ]; then B="$(printf '\033[1m')"; G="$(printf '\033[32m')"; Y="$(printf '\033[33m')"; R="$(printf '\033[31m')"; N="$(printf '\033[0m')"; else B=""; G=""; Y=""; R=""; N=""; fi
info() { printf '%s\n' "  $*"; }
ok()   { printf '%s\n' "  ${G}✓${N} $*"; }
warn() { printf '%s\n' "  ${Y}!${N} $*"; }
die()  { printf '%s\n' "  ${R}✗ $*${N}" >&2; exit 1; }

printf '\n%s\n\n' "${B}JPilot / NSAgent installer${N}"

# ---- helpers ---------------------------------------------------------------
OS="$(uname -s 2>/dev/null || echo unknown)"

# Ask a yes/no question. Reads from /dev/tty because when this script is run as
# `curl ... | bash`, stdin is the script itself, not the keyboard. Defaults to
# No when there is no terminal (non-interactive run).
ask_yes_no() {
  if [ -r /dev/tty ]; then
    printf '%s [y/N] ' "$1" > /dev/tty
    read _ans < /dev/tty || _ans=""
    case "$_ans" in [Yy]|[Yy][Ee][Ss]) return 0 ;; *) return 1 ;; esac
  fi
  return 1
}

# Poll the Docker daemon for up to ~2 minutes (Docker Desktop can take a while).
wait_for_docker() {
  _n=0
  while [ "$_n" -lt 60 ]; do
    docker info >/dev/null 2>&1 && return 0
    sleep 2; _n=$((_n + 1))
  done
  return 1
}

install_docker() {
  case "$OS" in
    Linux)
      [ "$(id -u)" -eq 0 ] && _sudo="" || _sudo="sudo"
      info "Installing Docker Engine via the official script (may prompt for sudo)..."
      curl -fsSL https://get.docker.com | $_sudo sh || return 1
      $_sudo systemctl enable --now docker >/dev/null 2>&1 || true
      $_sudo usermod -aG docker "$(id -un)" >/dev/null 2>&1 || true
      return 0 ;;
    Darwin)
      if command -v brew >/dev/null 2>&1; then
        info "Installing Docker Desktop via Homebrew..."
        brew install --cask docker || return 1
        open -a Docker >/dev/null 2>&1 || true
        info "Docker Desktop is starting up..."
        return 0
      fi
      warn "Homebrew isn't installed, so I can't install Docker automatically."
      return 2 ;;
    *)
      return 2 ;;
  esac
}

# ---- prerequisites ---------------------------------------------------------
command -v git >/dev/null 2>&1 || die "git is required but not installed. Install git and re-run."

if ! command -v docker >/dev/null 2>&1; then
  warn "Docker is not installed (it's required to run JPilot)."
  if ask_yes_no "  Try to install Docker automatically now?"; then
    if install_docker; then
      info "Waiting for the Docker daemon to come up..."
      if wait_for_docker; then
        ok "Docker installed and running"
      elif [ "$OS" = "Linux" ]; then
        die "Docker was installed, but your shell isn't in the 'docker' group yet.
     Log out and back in (or run 'newgrp docker'), then re-run this command."
      else
        die "Docker was installed but isn't running yet.
     Start Docker Desktop, wait for it to finish, then re-run this command."
      fi
    else
      die "Automatic install didn't complete.
     Install Docker manually, then re-run this command:
       https://docs.docker.com/get-docker/"
    fi
  else
    die "Docker is required. Install it and re-run this command:
       https://docs.docker.com/get-docker/"
  fi
fi

if ! docker info >/dev/null 2>&1; then
  warn "Docker is installed but the daemon isn't running."
  if [ "$OS" = "Darwin" ] && ask_yes_no "  Start Docker Desktop and wait for it?"; then
    open -a Docker >/dev/null 2>&1 || true
    wait_for_docker || die "Docker didn't come up in time. Start it manually and re-run."
  elif [ "$OS" = "Linux" ] && ask_yes_no "  Start the Docker service now (needs sudo)?"; then
    { [ "$(id -u)" -eq 0 ] && systemctl start docker || sudo systemctl start docker; } >/dev/null 2>&1 || true
    wait_for_docker || die "Docker didn't come up. Start it manually ('sudo systemctl start docker') and re-run."
  else
    die "Start Docker (Docker Desktop, or 'sudo systemctl start docker') and re-run."
  fi
fi

if docker compose version >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1; then
  ok "Docker is ready"
else
  die "Docker Compose was not found. Install Docker Desktop or the compose plugin:
       https://docs.docker.com/compose/install/"
fi

# ---- fetch the project -----------------------------------------------------
if [ -d "$TARGET/.git" ]; then
  info "Updating existing copy in ${B}$TARGET${N}..."
  git -C "$TARGET" fetch --depth 1 origin "$REF" >/dev/null 2>&1 || die "Could not fetch '$REF' from origin."
  git -C "$TARGET" checkout -q "$REF" 2>/dev/null || true
  git -C "$TARGET" reset --hard "origin/$REF" >/dev/null 2>&1 || git -C "$TARGET" reset --hard "$REF" >/dev/null 2>&1 || true
  ok "Updated to latest $REF"
elif [ -e "$TARGET" ]; then
  die "$TARGET already exists and is not a JPilot checkout.
     Remove it or set a different location: JPILOT_DIR=/path/to/dir"
else
  info "Downloading JPilot into ${B}$TARGET${N}..."
  git clone --depth 1 --branch "$REF" "$REPO_URL" "$TARGET" >/dev/null 2>&1 \
    || die "Clone failed. Check the repo URL/branch and your network."
  ok "Downloaded"
fi

# ---- hand off to the orchestrator -----------------------------------------
cd "$TARGET"
[ -f install.sh ] || die "install.sh not found in the project — unexpected layout."
chmod +x install.sh 2>/dev/null || true

printf '\n'
info "Starting the setup wizard..."
printf '\n'
exec sh ./install.sh
