#!/usr/bin/env sh
# Run Docker Compose using the stack file that matches NSAGENT_DEPLOY_MODE in .env.
#
#   ./compose.sh up -d
#   ./compose.sh logs -f backend-api
#   ./compose.sh down
#
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

COMPOSE_ARGS="-f docker-compose.yml"

if [ -f .env ]; then
  # shellcheck disable=SC1091
  mode=$(grep -E '^NSAGENT_DEPLOY_MODE=' .env 2>/dev/null | head -n1 | cut -d= -f2- | tr -d '"' | tr -d "'" | tr '[:upper:]' '[:lower:]' || true)
  if [ "$mode" = "prod" ]; then
    COMPOSE_ARGS="-f docker-compose.yml -f docker-compose.prod.yml"
    if docker compose version >/dev/null 2>&1; then
      # shellcheck disable=SC2086
      docker compose -f docker-compose.yml stop frontend 2>/dev/null || true
      # shellcheck disable=SC2086
      docker compose -f docker-compose.yml rm -f frontend 2>/dev/null || true
    fi
  fi
fi

if docker compose version >/dev/null 2>&1; then
  # shellcheck disable=SC2086
  exec docker compose $COMPOSE_ARGS "$@"
fi

if command -v docker-compose >/dev/null 2>&1; then
  # shellcheck disable=SC2086
  exec docker-compose $COMPOSE_ARGS "$@"
fi

echo "Error: Docker Compose is required but was not found." >&2
exit 1
