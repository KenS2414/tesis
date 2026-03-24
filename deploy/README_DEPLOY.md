Deployment examples (quick-start)

Canonical note

- For startup, migrations and backups procedures, use `docs/runbook.md` as the canonical source.
- This file only keeps deployment-specific notes (systemd/nginx/docker compose).

Runtime conventions

- Docker Compose: Gunicorn listens on `web:8000` inside the compose network.
- Systemd + Nginx: Gunicorn listens on Unix socket `/run/resis.sock`.
- Keep Nginx and Gunicorn aligned to the same transport in each environment.

1) Systemd + Nginx (simple VM)

- Copy the project to `/var/www/resis` on the server and create a virtualenv there.
- Install requirements: `pip install -r requirements.txt` inside the venv.
- Adjust `deploy/gunicorn.service`: set `User`, `WorkingDirectory` and `PATH` to the venv path.
- Copy `deploy/nginx.conf` to `/etc/nginx/sites-available/resis` and enable it (symlink to `sites-enabled`). Update `server_name` and static `alias` path.
- Start & enable systemd service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn
sudo systemctl restart nginx
```

Post-deploy note (systemd only)

- If you update `deploy/gunicorn.service` in a new release, apply this after deploying files on the server:

```bash
sudo cp /var/www/resis/deploy/gunicorn.service /etc/systemd/system/gunicorn.service
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
sudo systemctl status gunicorn --no-pager -l
```

- This step is required only for systemd-based deployments.
- If you deploy with Docker Compose only, you can skip it.

2) Docker Compose (dev / staging)

- Use the included `docker-compose.yml` and `Dockerfile` to run in containers (Postgres + MinIO):

```bash
docker compose up -d --build
# initialize DB (inside container or run init_db against the running web container)
docker compose exec web python init_db.py
```

Notes:
- Update `.env` or environment variables to set `SECRET_KEY` and `ADMIN_PASSWORD` before running.
- In production prefer managed Postgres and object storage (S3/Blob) and use CI/CD pipelines for builds.
