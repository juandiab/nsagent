#!/bin/sh
set -eu

: "${NGINX_HOSTNAME:=jpilot.nexxus-tech.com}"

envsubst '${NGINX_HOSTNAME}' \
  < /etc/nginx/nginx.conf.template \
  > /etc/nginx/nginx.conf

exec nginx -g 'daemon off;'
