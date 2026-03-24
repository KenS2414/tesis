#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/migrate.sh [local|docker]
# Defaults to local. Use 'docker' to run migrations inside docker-compose service.

MODE=${1:-local}
TIMESTAMP=$(date +%Y%m%d%H%M%S)
BACKUP_DIR=${BACKUP_DIR:-backups}
mkdir -p "$BACKUP_DIR"

# DB defaults (can be overridden by env vars)
DB_USER=${POSTGRES_USER:-resis}
DB_NAME=${POSTGRES_DB:-resis}
DB_PASS=${POSTGRES_PASSWORD:-resispass}
DB_HOST=${DB_HOST:-localhost}

if [ "$MODE" = "docker" ]; then
  echo "[migrate] Running pre-migration logical dump inside docker-compose (service: db)..."
  DUMP_NAME="resis-${TIMESTAMP}.dump"
  # run pg_dump inside the db container and copy the file out
  docker-compose exec -T -e PGPASSWORD="$DB_PASS" db pg_dump -U "$DB_USER" -d "$DB_NAME" -F c -f "/tmp/$DUMP_NAME"
  CONTAINER_ID=$(docker-compose ps -q db)
  docker cp "$CONTAINER_ID":/tmp/$DUMP_NAME "$BACKUP_DIR/"
  # Verify dump integrity using pg_restore --list inside the container
  echo "[migrate] Verifying dump integrity inside container..."
  docker-compose exec -T -e PGPASSWORD="$DB_PASS" db pg_restore -l "/tmp/$DUMP_NAME" > /dev/null
  if [ $? -ne 0 ]; then
    echo "[migrate] ERROR: dump integrity check failed"
    exit 1
  fi
  # cleanup inside container
  docker-compose exec -T -e PGPASSWORD="$DB_PASS" db rm -f "/tmp/$DUMP_NAME" || true
  echo "[migrate] Dump saved to $BACKUP_DIR/$DUMP_NAME"

  echo "[migrate] Running migrations inside docker-compose (service: web)..."
  docker-compose run --rm -e FLASK_APP=app:create_app web flask db upgrade
else
  echo "[migrate] Running pre-migration logical dump locally (if pg_dump available)..."
  DUMP_NAME="resis-${TIMESTAMP}.dump"
  if command -v pg_dump >/dev/null 2>&1; then
    PGPASSWORD="$DB_PASS" pg_dump -U "$DB_USER" -h "$DB_HOST" -d "$DB_NAME" -F c -f "$BACKUP_DIR/$DUMP_NAME"
    echo "[migrate] Dump saved to $BACKUP_DIR/$DUMP_NAME"
    # verify dump integrity locally using pg_restore --list if available
    if command -v pg_restore >/dev/null 2>&1; then
      echo "[migrate] Verifying dump integrity locally..."
      pg_restore -l "$BACKUP_DIR/$DUMP_NAME" > /dev/null
      if [ $? -ne 0 ]; then
        echo "[migrate] ERROR: dump integrity check failed"
        exit 1
      fi
    else
      echo "[migrate] pg_restore not found; skipping integrity check"
    fi
  else
    echo "[migrate] pg_dump not found on PATH; skipping local dump. Install Postgres client tools to enable dumps."
  fi

  echo "[migrate] Running migrations locally using venv..."
  # activate common venv path if present
  if [ -f "venv/bin/activate" ]; then
    # POSIX venv
    # shellcheck disable=SC1091
    . venv/bin/activate
  elif [ -f ".venv/bin/activate" ]; then
    . .venv/bin/activate
  fi
  export FLASK_APP=app:create_app
  python -m flask db upgrade
fi
