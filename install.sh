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
echo "Configuration received."
echo "Keep the setup tab open in your browser — JPilot will open automatically when ready."
trap - EXIT INT TERM

# ---- launch the real stack -------------------------------------------------
APP_URL="https://$DOMAIN"
JPILOT_WAIT_MAX="${JPILOT_WAIT_MAX:-300}"   # attempts; 2s each (~10 min default)
JPILOT_WAIT_INTERVAL="${JPILOT_WAIT_INTERVAL:-2}"

jpilot_http_ready() {
  _url="$1"
  _code=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 5 "${_url}/api/health" 2>/dev/null || echo 000)
  case "$_code" in 200) return 0 ;; esac
  _code=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 5 "${_url}/" 2>/dev/null || echo 000)
  case "$_code" in 200|301|302|304) return 0 ;; esac
  return 1
}

render_startup_progress() {
  _n="$1"
  _max="$2"
  _cap=$((_max * 9 / 10))
  _vis=$_n
  [ "$_vis" -gt "$_cap" ] && _vis=$_cap
  _filled=$((_vis * 40 / _max))
  _bar=""
  _i=0
  while [ "$_i" -lt 40 ]; do
    if [ "$_i" -lt "$_filled" ]; then _bar="${_bar}█"; else _bar="${_bar}░"; fi
    _i=$((_i + 1))
  done
  _elapsed=$((_n * JPILOT_WAIT_INTERVAL))
  _mins=$((_elapsed / 60))
  _secs=$((_elapsed % 60))
  if [ -t 1 ]; then
    printf '\r  [%s] %dm%02ds  Starting JPilot services...' "$_bar" "$_mins" "$_secs"
  else
    printf '\n  [%s] %dm%02ds  Starting JPilot services...\n' "$_bar" "$_mins" "$_secs"
  fi
}

wait_for_jpilot() {
  _url="$1"
  _n=0
  while [ "$_n" -lt "$JPILOT_WAIT_MAX" ]; do
    if jpilot_http_ready "$_url"; then
      if [ -t 1 ]; then
        printf '\r  [████████████████████████████████████████] ready!          \n'
      else
        printf '\n  JPilot is responding.\n'
      fi
      return 0
    fi
    render_startup_progress "$_n" "$JPILOT_WAIT_MAX"
    sleep "$JPILOT_WAIT_INTERVAL"
    _n=$((_n + 1))
  done
  if [ -t 1 ]; then printf '\n' ; fi
  return 1
}

printf '\n  Building containers in the background (watch progress in your browser)...\n'
./compose.sh up -d --build

printf '\n  Waiting for JPilot to finish starting...\n'

_ready=0
if wait_for_jpilot "$APP_URL"; then
  _ready=1
fi

# Give the browser a moment to redirect before we stop the setup wizard.
if [ "$_ready" -eq 1 ]; then
  sleep 3
fi

echo "Closing the setup wizard..."
$DC -f "$INSTALLER_COMPOSE" down >/dev/null 2>&1 || true
rm -f "$SENTINEL"

printf '\n'
if [ "$_ready" -eq 1 ]; then
  printf '  ✅ JPilot is ready at  '
else
  printf '  ⚠ JPilot is still starting — open when ready:  '
fi
osc8_link "$APP_URL"
printf '\n\n'
printf '  • Sign in with the admin account you created in the wizard.\n'
printf '  • View logs with:   ./compose.sh logs -f\n'
printf '  • Stop with:        ./compose.sh down\n'
printf '\n'
