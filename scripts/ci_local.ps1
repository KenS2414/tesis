Param(
    [string]$S3_BUCKET = "resis-ci-bucket",
    [string]$S3_ENDPOINT = "http://127.0.0.1:9000",
    [string]$AWS_ACCESS_KEY_ID = "minioadmin",
    [string]$AWS_SECRET_ACCESS_KEY = "minioadmin"
)

# Ensure critical env vars are present before any import/commands that may load the app
$env:SECRET_KEY = $env:SECRET_KEY -or "test-local-secret"
$env:ADMIN_PASSWORD = $env:ADMIN_PASSWORD -or "admin-pass"
# ensure DATABASE_URL is a valid SQLAlchemy URL pointing to local db service
$env:DATABASE_URL = $env:DATABASE_URL -or "postgresql://resis:resispass@127.0.0.1:5432/resis"
$env:S3_BUCKET = $env:S3_BUCKET -or $S3_BUCKET
$env:S3_ENDPOINT = $env:S3_ENDPOINT -or $S3_ENDPOINT
$env:AWS_ACCESS_KEY_ID = $env:AWS_ACCESS_KEY_ID -or $AWS_ACCESS_KEY_ID
$env:AWS_SECRET_ACCESS_KEY = $env:AWS_SECRET_ACCESS_KEY -or $AWS_SECRET_ACCESS_KEY

Write-Output "Starting local CI services (Docker Compose)"
# start only the DB service; MinIO may already be running locally
docker compose up -d db

Write-Output "Waiting for Postgres (port 5432)..."
for ($i=0; $i -lt 60; $i++) {
    $pg = Test-NetConnection -ComputerName 127.0.0.1 -Port 5432 -WarningAction SilentlyContinue
    if ($pg.TcpTestSucceeded) { Write-Output "Postgres up"; break }
    Start-Sleep -Seconds 1
}

Write-Output "Checking MinIO availability on $S3_ENDPOINT"
$minioCheck = Test-NetConnection -ComputerName 127.0.0.1 -Port 9000 -WarningAction SilentlyContinue
if ($minioCheck.TcpTestSucceeded) {
    Write-Output "Creating S3 bucket: $S3_BUCKET"
    try {
        & python scripts/create_bucket.py --bucket $S3_BUCKET --endpoint $S3_ENDPOINT --access $AWS_ACCESS_KEY_ID --secret $AWS_SECRET_ACCESS_KEY
    } catch {
        Write-Output "Bucket creation may have failed or already exists"
    }
} else {
    Write-Output "MinIO not reachable at $S3_ENDPOINT - skipping bucket creation"
}

$env:S3_BUCKET = $S3_BUCKET
$env:S3_ENDPOINT = $S3_ENDPOINT
$env:AWS_ACCESS_KEY_ID = $AWS_ACCESS_KEY_ID
$env:AWS_SECRET_ACCESS_KEY = $AWS_SECRET_ACCESS_KEY

# Set defaults for env vars if not already provided
if (-not $env:SECRET_KEY) { $env:SECRET_KEY = "test-local-secret" }
if (-not $env:ADMIN_PASSWORD) { $env:ADMIN_PASSWORD = "admin-pass" }
# ensure DATABASE_URL is a valid SQLAlchemy URL pointing to local db service
if (-not $env:DATABASE_URL) { $env:DATABASE_URL = "postgresql://resis:resispass@127.0.0.1:5432/resis" }

Write-Output "Running DB migrations"
Write-Output "DATABASE_URL=$env:DATABASE_URL"
try {
    flask db upgrade
} catch {
    Write-Output "flask db upgrade failed: $_"
    exit 1
}

Write-Output "Running tests (unit + integration)"
pytest -q
pytest -q -m integration
