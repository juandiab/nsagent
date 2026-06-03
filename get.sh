#!/usr/bin/env sh
# JPilot / NSAgent one-line bootstrap for macOS & Linux.
#
#   curl -fsSL https://raw.githubusercontent.com/juandiab/nsagent/main/get.sh | bash
#
# It checks prerequisites, downloads the project, and launches the setup wizard.
# Override defaults with environment variables, e.g.:
#   curl -fsSL .../get.sh | JPILOT_DIR=~/apps/jpilot JPILOT_REF=main bash
set -eu

REPO_URL="${JPILOT_REPO:-https://github.com/juandiab/nsagent.git}"
REF="${JPILOT_REF:-main}"
TARGET="${JPILOT_DIR:-$(pwd)/nsagent}"

# ---- pretty output ---------------------------------------------------------
if [ -t 1 ]; then B="$(printf '\033[1m')"; G="$(printf '\033[32m')"; Y="$(printf '\033[33m')"; R="$(printf '\033[31m')"; N="$(printf '\033[0m')"; else B=""; G=""; Y=""; R=""; N=""; fi
info() { printf '%s\n' "  $*"; }
ok()   { printf '%s\n' "  ${G}✓${N} $*"; }
warn() { printf '%s\n' "  ${Y}!${N} $*"; }
die()  { printf '%s\n' "  ${R}✗ $*${N}" >&2; exit 1; }

printf '\n%s\n\n' "${B}JPilot / NSAgent installer${N}"

# ---- prerequisites ---------------------------------------------------------
command -v git >/dev/null 2>&1 || die "git is required but not installed. Install git and re-run."

if ! command -v docker >/dev/null 2>&1; then
  die "Docker is required but not installed.
     Install Docker Desktop (Mac/Windows) or Docker Engine (Linux):
       https://docs.docker.com/get-docker/
     then re-run this command."
fi

if ! docker info >/dev/null 2>&1; then
  die "Docker is installed but the daemon isn't running.
     Start Docker Desktop (or 'sudo systemctl start docker') and re-run."
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
