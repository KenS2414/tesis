#!/usr/bin/env bash
set -euo pipefail


echo "Setting environment variables for flask"
export SECRET_KEY=${SECRET_KEY:-test-local-secret}
export ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin-pass}
# ensure DATABASE_URL points to local db instance
export DATABASE_URL=${DATABASE_URL:-postgresql://resis:resispass@127.0.0.1:5432/resis}

echo "Starting local CI services: db (MinIO may already run locally)"
# start only DB to avoid MinIO port conflicts when MinIO is managed externally
docker compose up -d db

echo "Waiting for Postgres to be reachable (port 5432)..."
for i in $(seq 1 60); do
  if nc -z 127.0.0.1 5432; then
    echo "Postgres is up"
    break
  fi
  sleep 1
done

S3_BUCKET=${S3_BUCKET:-resis-ci-bucket}
S3_ENDPOINT=${S3_ENDPOINT:-http://127.0.0.1:9000}
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-minioadmin}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-minioadmin}

echo "Checking MinIO availability at $S3_ENDPOINT"
if nc -z 127.0.0.1 9000; then
  echo "Creating S3 bucket: $S3_BUCKET"
  python scripts/create_bucket.py --bucket "$S3_BUCKET" --endpoint "$S3_ENDPOINT" --access "$AWS_ACCESS_KEY_ID" --secret "$AWS_SECRET_ACCESS_KEY" || true
else
  echo "MinIO not reachable at $S3_ENDPOINT — skipping bucket creation"
fi


echo "Running DB migrations"
flask db upgrade || true

echo "Running unit tests"
pytest -q

echo "Running integration tests (marked integration)"
pytest -q -m integration
