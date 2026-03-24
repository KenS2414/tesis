TLS setup (Certbot on host)
---------------------------------

This document describes obtaining Let's Encrypt certificates on the host (recommended when you manage the server directly).

Prerequisites
- Your domain DNS must point to the server IP.
- `nginx` installed and the `deploy/nginx.conf` deployed (replace `example.com`).
- `certbot` (package `python3-certbot-nginx`) installed.

Basic steps

1. Install certbot (Debian/Ubuntu):

```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

2. Ensure `deploy/nginx.conf` has your `server_name` set to your domain (and optionally `www.`).

3. Create webroot and static paths used by the nginx config (if not present):

```bash
sudo mkdir -p /var/www/letsencrypt /var/www/resis/static
sudo chown -R www-data:www-data /var/www/letsencrypt /var/www/resis/static
```

4. Run the helper script included in this repo to request certs and reload nginx:

```bash
cd /path/to/otro\ proyecto
sudo bash deploy/get_cert.sh example.com
```

5. Test renewal (dry-run):

```bash
sudo certbot renew --dry-run
```

Notes
- The nginx config sets HSTS with `preload`. Submitting your domain to the preload list is irreversible — remove `preload` if you want to opt-in later.
- Certbot will store certs in `/etc/letsencrypt/live/<domain>/`. `deploy/nginx.conf` already references that path; update `server_name` accordingly.
- If you run services in Docker, mount `/etc/letsencrypt` and `/var/www/letsencrypt` into your nginx container and ensure `deploy/nginx.conf` is used by that container.
 - If you run services in Docker, mount `/etc/letsencrypt` and `/var/www/letsencrypt` into your nginx container and ensure `deploy/nginx.conf` is used by that container.

Using Docker Compose
--------------------

This repo includes a docker-friendly nginx config (`deploy/nginx.docker.conf`), a `certbot` service and persistent volumes configured in `docker-compose.yml`, and a helper script `deploy/docker_get_cert.sh`.

1. Start nginx (so ACME HTTP challenge can be served):

```bash
docker compose up -d nginx
```

2. Request a certificate (replace domain and email):

```bash
sudo bash deploy/docker_get_cert.sh example.com you@example.com
```

3. Verify renewal (dry run):

```bash
docker compose run --rm certbot renew --dry-run
```

Notes:
- The helper stores certificates in the `letsencrypt` volume (mounted to `/etc/letsencrypt`). Keep backups of that volume if you migrate hosts.
- You can automate renewal by running `docker compose run --rm certbot renew` from a cron/systemd timer on the host and then reloading the nginx container.

If you want, I can also add a sample systemd unit that executes `docker compose run --rm certbot renew` and reloads the nginx container when certs change.
Systemd timer (recommended)
---------------------------------

You can use a systemd timer to run `certbot renew` automatically and reload `nginx` if certificates were renewed.

1. Copy the provided unit files to `/etc/systemd/system/` on the server:

```bash
sudo cp deploy/certbot-resis-renew.service /etc/systemd/system/
sudo cp deploy/certbot-resis-renew.timer /etc/systemd/system/
```

2. Reload systemd, enable and start the timer:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now certbot-resis-renew.timer
sudo systemctl status certbot-resis-renew.timer
```

3. Verify the service logs after the next run (or trigger manually):

```bash
sudo systemctl start certbot-resis-renew.service
sudo journalctl -u certbot-resis-renew.service --no-pager --since "1 hour ago"
```

The timer is configured to run daily at 03:00 with up to one hour of randomized delay. Adjust `OnCalendar` in `certbot-resis-renew.timer` if you prefer a different schedule.
