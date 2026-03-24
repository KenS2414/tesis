# Guía Local (Entrada Rápida)

Esta guía queda intencionalmente corta.

Fuente canónica para arranque, migraciones, tests y backups:
- `docs/runbook.md`

Si en algún documento ves pasos distintos, prioriza `docs/runbook.md`.

## Arranque local mínimo (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:FLASK_APP = 'app:create_app'
python init_db.py
python -m flask run
```

La aplicación estará disponible en `http://127.0.0.1:5000`.

## Nota S3/MinIO

En modo local simple, si no configuras S3/MinIO, los comprobantes se guardan en `static/uploads/`.

## Comandos canónicos de pruebas (PowerShell)

### Pruebas rápidas (sin integración)
```powershell
# Evita contaminación por variables previas de sesiones anteriores
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
$env:SECRET_KEY = 'test-local-secret'
& .\venv\Scripts\python.exe -m pytest -q -m "not integration"
```

### Pruebas de integración
```powershell
$env:SECRET_KEY = 'test-ci-secret'
$env:ADMIN_PASSWORD = 'admin-ci-pass'
$env:DATABASE_URL = 'postgresql://resis:resispass@localhost:5432/resis'
$env:S3_ENDPOINT = 'http://localhost:9000'
$env:AWS_ACCESS_KEY_ID = 'minioadmin'
$env:AWS_SECRET_ACCESS_KEY = 'minioadmin'
$env:S3_BUCKET = 'resis-uploads'
& .\venv\Scripts\python.exe -m pytest -q -m integration
```

### Limpieza de variables (opcional al terminar)
```powershell
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:S3_ENDPOINT -ErrorAction SilentlyContinue
Remove-Item Env:S3_BUCKET -ErrorAction SilentlyContinue
Remove-Item Env:AWS_ACCESS_KEY_ID -ErrorAction SilentlyContinue
Remove-Item Env:AWS_SECRET_ACCESS_KEY -ErrorAction SilentlyContinue
```

## Politica actual de imports

La compatibilidad legacy de imports fue retirada.

Regla vigente:
- Soportado desde `app.py`: `create_app`.
- Para base de datos y modelos: importar desde `extensions` y `models`.
- Para helpers S3: importar desde `utils.aws`.
- No usar `from app import app`, `db`, modelos ni helpers utilitarios.
