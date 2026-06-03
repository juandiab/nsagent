#!/usr/bin/env sh
# Build and start the production Docker Compose stack from the repository root.
#
#   ./scripts/prod-up.sh
#
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

COMPOSE_ARGS="-f docker-compose.yml -f docker-compose.prod.yml"

run_compose() {
  if docker compose version >/dev/null 2>&1; then
    # shellcheck disable=SC2086
    docker compose $COMPOSE_ARGS "$@"
    return
  fi
  if command -v docker-compose >/dev/null 2>&1; then
    # shellcheck disable=SC2086
    docker-compose $COMPOSE_ARGS "$@"
    return
  fi
  echo "Error: Docker Compose is required but was not found." >&2
  exit 1
}

# Drop dev frontend container if it is still running from a local stack.
if docker compose version >/dev/null 2>&1; then
  docker compose -f docker-compose.yml stop frontend 2>/dev/null || true
  docker compose -f docker-compose.yml rm -f frontend 2>/dev/null || true
elif command -v docker-compose >/dev/null 2>&1; then
  docker-compose -f docker-compose.yml stop frontend 2>/dev/null || true
  docker-compose -f docker-compose.yml rm -f frontend 2>/dev/null || true
fi

run_compose build
run_compose up -d
