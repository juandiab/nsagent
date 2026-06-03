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
  echo "stack directly with: ./compose.sh up -d"
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
./compose.sh up -d --build

rm -f "$SENTINEL"

APP_URL="https://$DOMAIN"

printf '\n  ✅ JPilot is starting at  '
osc8_link "$APP_URL"
printf '\n\n'
printf '  • The first boot may take a few seconds while services come up.\n'
printf '  • Sign in with the admin account you just created.\n'
printf '  • View logs with:   ./compose.sh logs -f\n'
printf '  • Stop with:        ./compose.sh down\n'
printf '\n'

# ---- open the app in a browser (best effort) -------------------------------
# Only auto-open when the app is reachable on this machine (localhost). For a
# custom domain the operator usually browses from elsewhere, so we just leave
# the clickable link above. Set JPILOT_NO_OPEN=1 to disable entirely.
open_url() {
  case "$(uname -s 2>/dev/null)" in
    Darwin) command -v open     >/dev/null 2>&1 && open "$1"     >/dev/null 2>&1 ;;
    Linux)  command -v xdg-open >/dev/null 2>&1 && xdg-open "$1" >/dev/null 2>&1 ;;
  esac
}

if [ -z "${JPILOT_NO_OPEN:-}" ]; then
  case "$DOMAIN" in
    localhost|127.*|::1)
      printf '  Waiting for JPilot to be ready'
      _n=0; _opened=0
      while [ "$_n" -lt 60 ]; do
        if curl -sk -o /dev/null --max-time 2 "https://localhost/" 2>/dev/null; then
          printf ' done.\n  Opening your browser...\n\n'
          open_url "$APP_URL"; _opened=1
          break
        fi
        printf '.'; sleep 2; _n=$((_n + 1))
      done
      if [ "$_opened" -eq 0 ]; then
        printf '\n  Still starting — open the link above when ready.\n\n'
      fi
      ;;
    *) : ;;                                 # custom domain: rely on the printed link
  esac
fi
