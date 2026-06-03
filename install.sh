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

cat <<'BANNER'

  ┌──────────────────────────────────────────────────────────┐
  │  JPilot setup is ready.                                    │
  │                                                            │
  │   ▶  Open  https://localhost:9443                          │
  │                                                            │
  │  It uses a self-signed certificate, so your browser will   │
  │  show a security warning the first time — that is expected │
  │  for the installer. Accept it to continue.                 │
  └──────────────────────────────────────────────────────────┘

Waiting for you to finish the wizard (Ctrl-C to abort)...
BANNER

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

cat <<EOF

  ✅ JPilot is starting at  https://$DOMAIN

  • The first boot may take a few seconds while services come up.
  • Sign in with the admin account you just created.
  • View logs with:   $DC logs -f
  • Stop with:        $DC down

EOF
