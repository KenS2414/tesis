#!/usr/bin/env bash
set -euo pipefail

# Usage: ./get_cert.sh example.com [www.example.com]
DOMAIN=${1:-}
if [ -z "$DOMAIN" ]; then
  echo "Usage: $0 <domain> [www-domain]"
  exit 2
fi
WWW_DOMAIN=${2:-www.$DOMAIN}

echo "Requesting certificates for: $DOMAIN and $WWW_DOMAIN"

if ! command -v certbot >/dev/null 2>&1; then
  echo "certbot not found. Install certbot (e.g. sudo apt install certbot python3-certbot-nginx)"
  exit 1
fi

sudo certbot --nginx -d "$DOMAIN" -d "$WWW_DOMAIN"

echo "Reloading nginx"
sudo systemctl reload nginx

echo "Done. Verify: sudo certbot certificates"
