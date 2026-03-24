#!/usr/bin/env bash
# Helper to request a certificate using the `certbot` container and the webroot mounted volume.
# Usage: sudo bash deploy/docker_get_cert.sh example.com you@example.com

set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <domain> <email>"
  exit 2
fi

DOMAIN="$1"
EMAIL="$2"

echo "Ensure nginx is running so HTTP challenge can be served..."
docker compose up -d nginx

echo "Requesting certificate for $DOMAIN (email: $EMAIL)"
docker compose run --rm certbot certonly --webroot -w /var/www/letsencrypt -d "$DOMAIN" --email "$EMAIL" --agree-tos --no-eff-email

echo "Reloading nginx to pick up new certificates"
docker compose exec nginx nginx -s reload || true

echo "Done. Certificates are stored in the 'letsencrypt' volume (mounted at /etc/letsencrypt)."
