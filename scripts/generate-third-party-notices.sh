#!/usr/bin/env sh
# Regenerate THIRD_PARTY_NOTICES.txt at the repository root.
# Requires: Node.js (npm), Python 3, and pip.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
OUT="$ROOT/THIRD_PARTY_NOTICES.txt"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

FRONTEND_CSV="$TMP/frontend.csv"
BACKEND_PLAIN="$TMP/backend.txt"
MCP_PLAIN="$TMP/mcp.txt"
INSTALLER_PLAIN="$TMP/installer.txt"

section() {
  printf '\n%s\n%s\n' "$1" "$(printf '%.0s-' $(seq 1 72))"
}

{
  cat <<'HEADER'
THIRD-PARTY NOTICES
===================

JPilot (Nexxus-Tech SAS) includes open-source software components.
The Nexxus application code is proprietary and licensed under the End-User
License Agreement (EULA), not under the licenses below. The following notices
apply only to bundled third-party components.

This file is provided for Docker and self-hosted distributions. Regenerate with:
  ./scripts/generate-third-party-notices.sh

HEADER
  printf 'Generated: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  section "Runtime base images (Docker)"
  cat <<'BASE'
- python:3.12-slim — Python Software Foundation License; Debian packages under
  their respective licenses (see image documentation).
- node:20-alpine — Node.js MIT license; Alpine packages under their respective
  licenses.
- mongo:latest — MongoDB Server Side Public License (SSPL); see MongoDB, Inc.
- nginx (custom build) — nginx BSD-2-Clause; OpenSSL Apache-style license.

BASE

  if command -v npm >/dev/null 2>&1 && [ -f "$ROOT/frontend/package.json" ]; then
    (cd "$ROOT/frontend" && npm install --silent >/dev/null 2>&1)
    (cd "$ROOT/frontend" && npx --yes license-checker --production --csv >"$FRONTEND_CSV")
    section "Frontend production dependencies (npm)"
    # Skip header row; print name and license columns
    tail -n +2 "$FRONTEND_CSV" | while IFS= read -r line; do
      # CSV: "name","license","repository"
      name=$(printf '%s' "$line" | cut -d',' -f1 | tr -d '"')
      license=$(printf '%s' "$line" | cut -d',' -f2 | tr -d '"')
      printf '  %s — %s\n' "$name" "$license"
    done
  fi

  gen_python() {
    dir=$1
    label=$2
    req=$3
    out=$4
    if [ ! -f "$dir/$req" ]; then
      return 0
    fi
    venv="$TMP/venv-$label"
    python3 -m venv "$venv"
    "$venv/bin/pip" install -q -r "$dir/$req" pip-licenses
    "$venv/bin/pip-licenses" --format=plain >"$out"
    section "$label (Python pip)"
    cat "$out" | tail -n +3 | while read -r name ver lic _; do
      printf '  %s %s — %s\n' "$name" "$ver" "$lic"
    done
  }

  gen_python "$ROOT/backend-api" "Backend API" requirements.txt "$BACKEND_PLAIN"
  gen_python "$ROOT/mcp-server" "MCP server" requirements.txt "$MCP_PLAIN"
  gen_python "$ROOT/installer" "Installer wizard" requirements.txt "$INSTALLER_PLAIN"

  section "Full license texts"
  cat <<'FOOTER'
For components under MIT, BSD, ISC, or Apache-2.0, the standard license text
applies and is available from each project repository or from the dependency
install path in a built image.

For copyleft or special licenses (e.g. MPL-2.0 on DOMPurify, SSPL on MongoDB),
comply with the corresponding license terms when redistributing those components.

Questions: contact@nexxus-tech.com — Nexxus-Tech SAS, Bogotá D.C., Colombia.
FOOTER
} >"$OUT"

echo "Wrote $OUT"
