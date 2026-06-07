#!/bin/sh
set -eu

: "${NGINX_HOSTNAME:=jpilot.nexxus-tech.com}"
: "${JPILOT_NGINX_RELOAD_SIGNAL:=/var/run/jpilot/reload-nginx}"

envsubst '${NGINX_HOSTNAME}' \
  < /etc/nginx/nginx.conf.template \
  > /etc/nginx/nginx.conf

watch_reload_signals() {
  while true; do
    if [ -f "$JPILOT_NGINX_RELOAD_SIGNAL" ]; then
      nginx -s reload 2>/dev/null || true
      rm -f "$JPILOT_NGINX_RELOAD_SIGNAL"
    fi
    sleep 1
  done
}

mkdir -p "$(dirname "$JPILOT_NGINX_RELOAD_SIGNAL")"
watch_reload_signals &

exec nginx -g 'daemon off;'
