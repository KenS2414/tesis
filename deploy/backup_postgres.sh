#!/usr/bin/env bash
set -euo pipefail

# Simple Postgres logical backup helper
# Usage:
#  - When run by systemd the service provides environment via /etc/resis/backup.env
#  - You can still call manually: deploy/backup_postgres.sh [local|docker] [backup-dir]

MODE=${1:-${BACKUP_MODE:-local}}
BACKUP_DIR=${2:-${BACKUP_DIR:-./backups}}
RETENTION_DAYS=${RETENTION_DAYS:-14}
ENCRYPT=${ENCRYPT_BACKUPS:-false}
GPG_PASSPHRASE=${GPG_PASSPHRASE:-}

TIMESTAMP=$(date +%Y%m%d%H%M%S)
BASE_NAME="resis-backup-${TIMESTAMP}"
DUMP_NAME="${BASE_NAME}.dump"

TMPDIR=$(mktemp -d)
trap 'rm -rf "${TMPDIR}"' EXIT

mkdir -p "$BACKUP_DIR"

if [ "$MODE" = "docker" ]; then
  echo "Creating backup from docker container 'db'..."
  CONTAINER=db
  docker exec -t "$CONTAINER" pg_dump -U ${PGUSER:-resis} -F c ${PGDATABASE:-resis} -f /tmp/${DUMP_NAME}
  docker cp "$CONTAINER":/tmp/${DUMP_NAME} "$TMPDIR/${DUMP_NAME}"
  docker exec -t "$CONTAINER" rm -f /tmp/${DUMP_NAME} || true
else
  echo "Creating local backup..."
  pg_dump -U ${PGUSER:-resis} -F c ${PGDATABASE:-resis} -f "$TMPDIR/${DUMP_NAME}"
fi

echo "Verifying backup integrity with pg_restore --list"
if command -v pg_restore >/dev/null 2>&1 ; then
  if ! pg_restore --list "$TMPDIR/${DUMP_NAME}" >/dev/null 2>&1 ; then
    echo "Backup integrity check FAILED for ${DUMP_NAME}" >&2
    exit 3
  fi
else
  echo "pg_restore not available; skipping integrity list check"
fi

# Compress and optionally encrypt
if [ "${ENCRYPT}" = "true" ]; then
  echo "Compressing and encrypting backup..."
  gzip -c "$TMPDIR/${DUMP_NAME}" > "$BACKUP_DIR/${DUMP_NAME}.gz"
  if [ -z "${GPG_PASSPHRASE}" ]; then
    echo "GPG_PASSPHRASE is empty; cannot encrypt" >&2
    exit 4
  fi
  if ! command -v gpg >/dev/null 2>&1 ; then
    echo "gpg not available; install gnupg to enable encryption" >&2
    exit 5
  fi
  gpg --batch --yes --passphrase "${GPG_PASSPHRASE}" --symmetric --cipher-algo AES256 -o "$BACKUP_DIR/${DUMP_NAME}.gz.gpg" "$BACKUP_DIR/${DUMP_NAME}.gz"
  rm -f "$BACKUP_DIR/${DUMP_NAME}.gz"
  FINAL_NAME="${DUMP_NAME}.gz.gpg"
else
  echo "Compressing backup..."
  gzip -c "$TMPDIR/${DUMP_NAME}" > "$BACKUP_DIR/${DUMP_NAME}.gz"
  FINAL_NAME="${DUMP_NAME}.gz"
fi

echo "Backup created: ${BACKUP_DIR}/${FINAL_NAME}"

# Retention cleanup
if [ -n "${RETENTION_DAYS}" ] && [ "${RETENTION_DAYS}" -gt 0 ] 2>/dev/null; then
  echo "Removing backups older than ${RETENTION_DAYS} days"
  find "$BACKUP_DIR" -type f -name 'resis-backup-*' -mtime +"${RETENTION_DAYS}" -print -delete || true
fi

exit 0
