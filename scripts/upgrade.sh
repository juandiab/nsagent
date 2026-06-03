#!/usr/bin/env sh
# Pull latest main, then rebuild either the development or production Docker stack.
#
#   ./scripts/upgrade.sh
#
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

COMPOSE_DEV="-f docker-compose.yml"
COMPOSE_PROD="-f docker-compose.yml -f docker-compose.prod.yml"

compose() {
  if docker compose version >/dev/null 2>&1; then
    # shellcheck disable=SC2086
    docker compose "$@"
    return
  fi
  if command -v docker-compose >/dev/null 2>&1; then
    # shellcheck disable=SC2086
    docker-compose "$@"
    return
  fi
  echo "Error: Docker Compose is required but was not found." >&2
  exit 1
}

stop_dev_frontend() {
  compose -f docker-compose.yml stop frontend 2>/dev/null || true
  compose -f docker-compose.yml rm -f frontend 2>/dev/null || true
}

echo "==> Pulling latest from origin/main..."
git pull origin main

echo ""
echo "Which stack do you want to rebuild?"
echo "  1) Development  (docker compose build && up -d)"
echo "  2) Production   (prod compose build && up -d)"
echo "  q) Skip rebuild (git pull only)"
printf '%s' "Choice [1/2/q]: "
read -r choice

case $(printf '%s' "$choice" | tr '[:upper:]' '[:lower:]') in
  1|dev|development)
    echo "==> Rebuilding development stack..."
    # shellcheck disable=SC2086
    compose $COMPOSE_DEV build
    # shellcheck disable=SC2086
    compose $COMPOSE_DEV up -d
    echo "Upgrade finished (development)."
    ;;
  2|prod|production)
    echo "==> Rebuilding production stack..."
    stop_dev_frontend
    # shellcheck disable=SC2086
    compose $COMPOSE_PROD build
    # shellcheck disable=SC2086
    compose $COMPOSE_PROD up -d
    echo "Upgrade finished (production)."
    ;;
  q|quit|skip|'')
    echo "No stack was rebuilt."
    ;;
  *)
    echo "Invalid choice. No stack was rebuilt." >&2
    exit 1
    ;;
esac
