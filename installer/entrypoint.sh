#!/bin/sh
set -eu

# The installer serves its own UI over HTTPS using a throwaway self-signed cert so the
# admin password is never sent in cleartext, even when installing on a remote host.
# This cert is unrelated to the app's cert (which the wizard writes to nginx/ssl/).
CERT=/tmp/installer.crt
KEY=/tmp/installer.key

if [ ! -f "$CERT" ] || [ ! -f "$KEY" ]; then
    echo "[installer] generating ephemeral TLS certificate for the setup UI..."
    openssl req -x509 -newkey rsa:2048 -nodes \
        -keyout "$KEY" -out "$CERT" -days 7 \
        -subj "/CN=localhost" \
        -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" >/dev/null 2>&1
fi

exec uvicorn app:app \
    --host 0.0.0.0 --port 9443 \
    --ssl-keyfile "$KEY" --ssl-certfile "$CERT"
