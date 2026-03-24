param(
    [string]$Mode = "local"
)

# Setup
$TIMESTAMP = Get-Date -Format "yyyyMMddHHmmss"
$BACKUP_DIR = $env:BACKUP_DIR
if (-not $BACKUP_DIR) { $BACKUP_DIR = "backups" }
New-Item -ItemType Directory -Force -Path $BACKUP_DIR | Out-Null

# DB defaults (can be overridden by env vars)
$DB_USER = $env:POSTGRES_USER
if (-not $DB_USER) { $DB_USER = "resis" }
$DB_NAME = $env:POSTGRES_DB
if (-not $DB_NAME) { $DB_NAME = "resis" }
$DB_PASS = $env:POSTGRES_PASSWORD
if (-not $DB_PASS) { $DB_PASS = "resispass" }
$DB_HOST = $env:DB_HOST
if (-not $DB_HOST) { $DB_HOST = "localhost" }

if ($Mode -eq "docker") {
    Write-Output "[migrate] Running pre-migration logical dump inside docker-compose (service: db)..."
    $DUMP_NAME = "resis-$TIMESTAMP.dump"
    # run pg_dump inside the db container
    docker-compose exec -T -e PGPASSWORD=$DB_PASS db pg_dump -U $DB_USER -d $DB_NAME -F c -f "/tmp/$DUMP_NAME"
    $containerId = docker-compose ps -q db
    docker cp "$($containerId):/tmp/$DUMP_NAME" "$BACKUP_DIR\$DUMP_NAME"
    # Verify dump integrity inside the container using pg_restore --list
    Write-Output "[migrate] Verifying dump integrity inside container..."
    docker-compose exec -T -e PGPASSWORD=$DB_PASS db pg_restore -l "/tmp/$DUMP_NAME"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[migrate] ERROR: dump integrity check failed"
        exit 1
    }
    # cleanup inside container
    docker-compose exec -T -e PGPASSWORD=$DB_PASS db rm -f "/tmp/$DUMP_NAME" | Out-Null
    Write-Output "[migrate] Dump saved to $BACKUP_DIR\$DUMP_NAME"

    Write-Output "[migrate] Running migrations inside docker-compose (service: web)..."
    docker-compose run --rm -e FLASK_APP=app:create_app web flask db upgrade
    return
}

Write-Output "[migrate] Running pre-migration logical dump locally (if pg_dump available)..."
$DUMP_NAME = "resis-$TIMESTAMP.dump"
if (Get-Command pg_dump -ErrorAction SilentlyContinue) {
    $env:PGPASSWORD = $DB_PASS
    pg_dump -U $DB_USER -h $DB_HOST -d $DB_NAME -F c -f "$BACKUP_DIR\$DUMP_NAME"
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
    Write-Output "[migrate] Dump saved to $BACKUP_DIR\$DUMP_NAME"
    # verify dump integrity locally using pg_restore --list if available
    if (Get-Command pg_restore -ErrorAction SilentlyContinue) {
        Write-Output "[migrate] Verifying dump integrity locally..."
        pg_restore -l "$BACKUP_DIR\$DUMP_NAME"
        if ($LASTEXITCODE -ne 0) {
            Write-Error "[migrate] ERROR: dump integrity check failed"
            exit 1
        }
    } else {
        Write-Output "[migrate] pg_restore not found; skipping integrity check"
    }
} else {
    Write-Output "[migrate] pg_dump not found on PATH; skipping local dump. Install Postgres client tools to enable dumps."
}

Write-Output "[migrate] Running migrations locally using venv..."
if (Test-Path .\venv\Scripts\Activate.ps1) {
    & .\venv\Scripts\Activate.ps1
} elseif (Test-Path .\.venv\Scripts\Activate.ps1) {
    & .\.venv\Scripts\Activate.ps1
}

$env:FLASK_APP = 'app:create_app'
python -m flask db upgrade
