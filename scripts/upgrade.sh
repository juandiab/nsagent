#!/usr/bin/env sh
# Pull latest main, then optionally rebuild dev and/or production Docker stacks.
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

yes_answer() {
  case $(printf '%s' "$1" | tr '[:upper:]' '[:lower:]') in
    y|yes) return 0 ;;
    *) return 1 ;;
  esac
}

stop_dev_frontend() {
  compose -f docker-compose.yml stop frontend 2>/dev/null || true
  compose -f docker-compose.yml rm -f frontend 2>/dev/null || true
}

echo "==> Pulling latest from origin/main..."
git pull origin main

printf '%s' "Update development stack (docker compose build && up -d)? [y/N] "
read -r dev_answer

printf '%s' "Update production stack (prod compose build && up -d)? [y/N] "
read -r prod_answer

updated=0

if yes_answer "$dev_answer"; then
  echo "==> Rebuilding development stack..."
  # shellcheck disable=SC2086
  compose $COMPOSE_DEV build
  # shellcheck disable=SC2086
  compose $COMPOSE_DEV up -d
  updated=1
fi

if yes_answer "$prod_answer"; then
  echo "==> Rebuilding production stack..."
  stop_dev_frontend
  # shellcheck disable=SC2086
  compose $COMPOSE_PROD build
  # shellcheck disable=SC2086
  compose $COMPOSE_PROD up -d
  updated=1
fi

if [ "$updated" -eq 0 ]; then
  echo "No stacks were rebuilt."
else
  echo "Upgrade finished."
fi
