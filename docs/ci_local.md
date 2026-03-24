# Local CI (no GitHub Actions)

This document explains how to run the project's CI locally using Docker Compose.

Prerequisites
- Docker Desktop (or engine) and Docker Compose available locally.
- Python 3.11 and project's `requirements.txt` installed in a virtualenv.

Quick start (Linux / macOS / WSL)

1. Start services and run tests (bash):

```bash
make ci-local
```

This will:
- start `postgres` and `minio` via `docker compose`
- wait for services to be reachable
- create the S3 bucket using `scripts/create_bucket.py`
- run `flask db upgrade`
- run unit tests (`pytest`) and integration tests (`pytest -m integration`)

CI improvements (implemented)
- GitHub Actions ahora está dividido en dos jobs: `unit-tests` (ejecuta `pytest -m "not integration"` con SQLite in-memory) e `integration-tests` (ejecuta `pytest -m integration`). Esto acelera el feedback y aísla regresiones.
- El job `integration-tests` ahora levanta Postgres real, arranca MinIO, crea bucket y ejecuta `python -m flask db upgrade` antes de correr las pruebas.
- MinIO queda fijado a una imagen versionada (`minio/minio:RELEASE.2024-12-13T22-19-12Z`) para reducir flakiness por cambios de `latest`.
- Guardrail activo: CI falla si se recolectan menos de 2 tests marcados como `integration`.
- Ensure `SECRET_KEY` and `DATABASE_URL` are exported before importing the app (prevents pytest collection failures).
- Avoid restarting MinIO on every run; start Postgres and MinIO once per runner and reuse them across jobs when possible.
- Mock S3 in unit tests (use a deterministic fake S3 client) to avoid network I/O in the fast job.

S3 test naming convention
- `tests/test_s3_fakeclient.py`: prueba unitaria de helpers S3 con cliente fake en memoria.
- `tests/test_s3_functional_flow.py`: prueba funcional de flujo de pago con FakeS3 (sin infraestructura externa).
- `tests/test_s3_real_integration.py`: prueba de integración real (Postgres + MinIO).
- `tests/test_minio_e2e.py`: prueba E2E de MinIO real con contenedor efímero.

Quick start (Windows PowerShell)

```powershell
.\scripts\ci_local.ps1
```

Notes and troubleshooting
- If your environment lacks `nc` (netcat) the bash script may fail waiting for ports — run the script from WSL or install `netcat`.
- The scripts set default env vars: `SECRET_KEY`, `ADMIN_PASSWORD`, `DATABASE_URL`, `S3_BUCKET`, `S3_ENDPOINT`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`. Override as needed.
- If you prefer to only run unit tests, run `pytest -q` directly.

CI on a remote server
- You can run the same scripts on a remote VM (e.g., a self-hosted runner) to reproduce CI without GitHub Actions billing.

Fast local feedback suggestions
- Run only unit tests during development for quick checks:

```powershell
$env:SECRET_KEY='test-local-secret'; pytest -q -m "not integration"
```

You can also use the Makefile shortcut:

```bash
make ci-unit
```

Parallel test runner
- To run unit tests in parallel with `-n auto` you need `pytest-xdist` installed. Install it locally with:

```bash
python -m pip install pytest-xdist
```

Note: CI workflows should include `pytest-xdist` in `requirements.txt` (already added) so the `-n auto` flag works in the `unit-tests` job.

- Run integrations separately when needed:

```powershell
$env:SECRET_KEY='test-local-secret'; $env:DATABASE_URL='postgresql://resis:resispass@127.0.0.1:5432/resis'; pytest -q -m integration --durations=20
```

Or via Makefile:

```bash
make ci-integration
```

If you want, I can add these snippets to the repository's `Makefile` or add a short GitHub Actions example that already includes the unit/integration split.
