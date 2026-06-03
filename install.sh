#!/usr/bin/env sh
# NSAgent / JPilot installer.
#
# Starts the web setup wizard, waits for you to complete it in the browser, then
# launches the full stack. Run from the project root:
#
#     ./install.sh                # first-time install
#     ./install.sh --reconfigure  # overwrite an existing .env via the wizard
#
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

SENTINEL=".installer-complete"
INSTALLER_COMPOSE="docker-compose.installer.yml"
RECONFIGURE=0

for arg in "$@"; do
  case "$arg" in
    --reconfigure) RECONFIGURE=1 ;;
    -h|--help)
      echo "Usage: ./install.sh [--reconfigure]"
      exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

# ---- locate docker compose -------------------------------------------------
if docker compose version >/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
else
  echo "Error: Docker Compose is required but was not found." >&2
  echo "Install Docker Desktop or the docker compose plugin, then re-run." >&2
  exit 1
fi

# ---- existing-install guard ------------------------------------------------
if [ -f .env ] && [ "$RECONFIGURE" -eq 0 ]; then
  echo "A .env file already exists — this looks like a configured install."
  echo "Re-run with '--reconfigure' to overwrite it via the wizard, or start the"
  echo "stack directly with: $DC up -d"
  exit 1
fi

rm -f "$SENTINEL"

cleanup() {
  echo ""
  echo "Shutting down the installer..."
  $DC -f "$INSTALLER_COMPOSE" down >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

# ---- launch the wizard -----------------------------------------------------
echo "Building and starting the setup wizard..."
$DC -f "$INSTALLER_COMPOSE" up -d --build

INSTALLER_URL="https://localhost:9443"

# Emit an OSC 8 terminal hyperlink (clickable) when writing to a TTY; fall back
# to the plain URL otherwise. The visible text is the URL itself, so it reads
# fine even on terminals that don't support OSC 8.
osc8_link() {
  if [ -t 1 ]; then
    printf '\033]8;;%s\033\\%s\033]8;;\033\\' "$1" "$1"
  else
    printf '%s' "$1"
  fi
}

printf '\n'
printf '  ┌──────────────────────────────────────────────────────────┐\n'
printf '  │  JPilot setup is ready.                                    │\n'
printf '  └──────────────────────────────────────────────────────────┘\n'
printf '\n'
printf '   ▶  Open  '
osc8_link "$INSTALLER_URL"
printf '\n\n'
printf '  It uses a self-signed certificate, so your browser will show a\n'
printf '  security warning the first time — that is expected for the\n'
printf '  installer. Accept it to continue.\n'
printf '\n'
printf 'Waiting for you to finish the wizard (Ctrl-C to abort)...\n'

# ---- wait for the wizard to finish -----------------------------------------
while [ ! -f "$SENTINEL" ]; do
  sleep 2
done

DOMAIN=$(head -n1 "$SENTINEL" 2>/dev/null || echo "localhost")
echo ""
echo "Configuration received. Stopping the installer..."
$DC -f "$INSTALLER_COMPOSE" down >/dev/null 2>&1 || true
trap - EXIT INT TERM

# ---- launch the real stack -------------------------------------------------
echo "Launching JPilot..."
$DC up -d --build

rm -f "$SENTINEL"

printf '\n  ✅ JPilot is starting at  '
osc8_link "https://$DOMAIN"
printf '\n\n'
printf '  • The first boot may take a few seconds while services come up.\n'
printf '  • Sign in with the admin account you just created.\n'
printf '  • View logs with:   %s logs -f\n' "$DC"
printf '  • Stop with:        %s down\n' "$DC"
printf '\n'
