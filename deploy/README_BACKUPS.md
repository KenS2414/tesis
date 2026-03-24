Postgres backups

This project includes a simple logical backup script and systemd units to
automate backups.

Files added:
- `deploy/backup_postgres.sh` — create logical backups (supports `local` and `docker` modes).
- `deploy/backup_postgres.service` — example systemd service (calls script from `/opt/resis/...`).
- `deploy/backup_postgres.timer` — example systemd timer to run daily.

Backups (Postgres)
-------------------

This repo includes a logical backup helper (`deploy/backup_postgres.sh`) and example `systemd` unit/timer to schedule automatic backups on a Linux host.

What the script does
- Creates a custom-format dump via `pg_dump -F c`.
- Supports `docker` mode (execs into the `db` container and copies the dump) and `local` mode (runs `pg_dump` locally).
- Verifies the dump by running `pg_restore --list` when `pg_restore` is available.

Enable on a server (example)

1. Copy the unit files to `/etc/systemd/system/`:

```bash
sudo cp deploy/backup_postgres.service /etc/systemd/system/
sudo cp deploy/backup_postgres.timer /etc/systemd/system/
```

2. Adjust the service environment or unit to match your install. The example expects the repository mounted at `/srv/resis` and will run the helper as `root`. Edit `/etc/systemd/system/backup_postgres.service` to update `BACKUP_DIR`, `BACKUP_MODE` (`docker` or `local`) and DB credentials if needed.

3. Reload systemd and enable timer:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now backup_postgres.timer
sudo systemctl status backup_postgres.timer
```

4. After the first run check logs and backups:

```bash
sudo journalctl -u backup_postgres.service --no-pager --since "1 hour ago"
ls -lah /var/backups/resis
```

Restore guide (quick)

1. To list contents of a custom-format dump:

```bash
pg_restore --list /path/to/resis-backup-YYYYMMDDHHMMSS.dump
```

2. To restore to a fresh database (example):

```bash
# create database and user (if necessary)
createdb -U postgres resis_restore
pg_restore -U postgres -d resis_restore /path/to/resis-backup-YYYYMMDDHHMMSS.dump
```

3. To restore into the running `db` docker container:

```bash
docker cp /path/to/resis-backup-YYYYMMDDHHMMSS.dump db:/tmp/restore.dump
docker exec -it db bash -c "pg_restore -U resis -d resis /tmp/restore.dump"
```

Retention & encryption (recommendation)
- Keep a retention policy: e.g., daily for 14 days, weekly for 12 weeks, monthly for 12 months.
- For off-host backups encrypt with `gpg --symmetric` or use server-side encrypted S3 buckets. Example encrypt before upload:

```bash
gpg --symmetric --cipher-algo AES256 --output ${FNAME}.gpg ${FNAME}
```

Security notes
- Never store unencrypted backups with production data on public storage.
- Secure the `BACKUP_DIR` with appropriate filesystem permissions and rotate credentials if compromised.

Environment file
----------------

Create `/etc/resis/backup.env` on the host (use the example `deploy/backup.env.example`) and secure it:

```bash
sudo mkdir -p /etc/resis
sudo cp deploy/backup.env.example /etc/resis/backup.env
sudo chown root:root /etc/resis/backup.env
sudo chmod 600 /etc/resis/backup.env
```

Key variables in the env file:
- `BACKUP_MODE`: `docker` or `local`.
- `BACKUP_DIR`: directory on the host where backups will be stored.
- `RETENTION_DAYS`: number of days to keep backups (0 disables automatic deletion).
- `ENCRYPT_BACKUPS`: `true` to enable symmetric GPG encryption of archives.
- `GPG_PASSPHRASE`: passphrase used for symmetric encryption (keep secret).

If you enable `ENCRYPT_BACKUPS=true`, install `gpg` (gnupg) on the host and provide `GPG_PASSPHRASE` in the env file. The script will compress then encrypt the dump producing files named like `resis-backup-<ts>.dump.gz.gpg`.

Security recommendation: store the `GPG_PASSPHRASE` in a secrets manager or a file with strict permissions; do not commit it into the repository.

```bash
# create backups/ and run local dump
bash deploy/backup_postgres.sh local ./backups

# docker mode (runs pg_dump inside container 'db')
bash deploy/backup_postgres.sh docker ./backups
```

Install systemd timer (on server):

```bash
sudo cp deploy/backup_postgres.service /etc/systemd/system/
sudo cp deploy/backup_postgres.timer /etc/systemd/system/
sudo cp deploy/backup_postgres.sh /opt/resis/deploy/backup_postgres.sh
sudo chown root:root /opt/resis/deploy/backup_postgres.sh
sudo chmod 750 /opt/resis/deploy/backup_postgres.sh
sudo systemctl daemon-reload
sudo systemctl enable --now backup_postgres.timer
sudo systemctl status backup_postgres.timer
```

