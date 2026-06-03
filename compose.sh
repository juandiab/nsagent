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

COMPOSE_FILE="docker-compose.yml"

if [ -f .env ]; then
  # shellcheck disable=SC1091
  mode=$(grep -E '^NSAGENT_DEPLOY_MODE=' .env 2>/dev/null | head -n1 | cut -d= -f2- | tr -d '"' | tr -d "'" | tr '[:upper:]' '[:lower:]' || true)
  if [ "$mode" = "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
  fi
fi

if docker compose version >/dev/null 2>&1; then
  exec docker compose -f "$COMPOSE_FILE" "$@"
fi

if command -v docker-compose >/dev/null 2>&1; then
  exec docker-compose -f "$COMPOSE_FILE" "$@"
fi

echo "Error: Docker Compose is required but was not found." >&2
exit 1
