# Proyecto Flask

Instrucciones rápidas (Windows PowerShell):

1. Crear y activar entorno virtual:

```powershell
## resis — Aplicación Flask mínima

Este repositorio contiene una pequeña aplicación Flask para gestión de usuarios, estudiantes y comprobantes de pago. El proyecto está preparado para desarrollo local y despliegues sencillos (Docker, Gunicorn + nginx).

### Contenido
- `app.py` — punto de entrada de la aplicación.
- `models.py`, `extensions.py` — modelos y extensiones de Flask.
- `init_db.py` — script de inicialización (crea admin si no existe).
- `tests/` — pruebas con `pytest` (incluye S3 funcional con FakeS3 y S3 de integración real con MinIO).
- `Dockerfile`, `docker-compose.yml` — ejemplos para desarrollo y pruebas locales con Postgres + MinIO.
- `deploy/` — ejemplos de `systemd` y `nginx`.

### Requisitos
- Python 3.11+
- Dependencias en `requirements.txt` (incluye `Pillow`, `Flask-Migrate`, `boto3`, `moto` para pruebas si quieres usarlo).

---

### Quickstart (desarrollo, PowerShell)

1. Crear y activar entorno virtual:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
# Sistema de Gestión Integral — Resis (Trabajo de Grado)

[![CI](https://github.com/KenS2414/tesisfinal/actions/workflows/ci.yml/badge.svg)](https://github.com/KenS2414/tesisfinal/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)

Resumen corto
---------------
Proyecto académico: sistema web de gestión integral para U.E. Colegio La Salle Tienda Honda. Centraliza información académica y administrativa (estudiantes, calificaciones, comprobantes) y está preparado para desarrollo local y despliegue en contenedores.

Dónde está cada guía
--------------------
| Tema | Documento canónico |
|---|---|
| Arranque local, migraciones, tests y backups | `docs/runbook.md` |
| Ejecución local rápida (resumen) | `README_LOCAL.md` |
| Despliegue (systemd/nginx/docker compose) | `deploy/README_DEPLOY.md` |
| Backups de Postgres | `deploy/README_BACKUPS.md` |
| TLS / Let's Encrypt | `deploy/README_TLS.md` |

Contenido clave
---------------
- `app.py` — entrada de la app.
- `models.py`, `extensions.py` — modelos y extensiones.
- `init_db.py` — inicialización de la base de datos (crea admin si no existe).
- `deploy/` — ejemplos y helpers para `nginx`, `certbot`, `systemd` y backups.
- `tests/` — pruebas con `pytest` (incluye S3 funcional con FakeS3 y S3 de integración real con MinIO).
- `docker-compose.yml`, `Dockerfile` — entorno de desarrollo con Postgres + MinIO.

Índice
------
1. Quickstart (desarrollo)
2. Ejecutar pruebas
3. Variables de entorno (resumen)
4. Docker (desarrollo)
5. Migraciones y backups
6. Despliegue (producción)
7. Observabilidad y seguridad
8. Licencia y terceros
9. Contribuir

1) Quickstart (desarrollo — PowerShell)
-------------------------------------------------
La guía canónica de arranque y migraciones está en `docs/runbook.md`.

Resumen mínimo:

```powershell
python -m venv venv
.\\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
$env:FLASK_APP='app:create_app'
python init_db.py
python -m flask run
```

2) Ejecutar pruebas
--------------------
```powershell
$env:SECRET_KEY='test-secret'
$env:PYTHONPATH=(Get-Location).Path
pytest -q
```
Las pruebas incluyen mocks para S3 (no requieren credenciales reales).

3) Variables de entorno (resumen)
--------------------------------
Coloca valores en `.env` o exporta en tu sesión. Copia `deploy/backup.env.example` como referencia.

| Variable | Propósito | Ejemplo |
|---|---:|---|
| `SECRET_KEY` | Clave de Flask | `change-me` |
| `DATABASE_URL` | URL de la DB | `postgresql://resis:resispass@db:5432/resis` |
| `S3_BUCKET` | Nombre bucket para uploads | `resis-uploads` |
| `S3_ENDPOINT` | Endpoint S3/MinIO | `http://minio:9000` |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Credenciales S3 | `minioadmin` / `minioadmin` |
| `SENTRY_DSN` | Sentry DSN para errores | (opcional) |

4) Docker (desarrollo local)
----------------------------
Levanta la pila completa (web, db, minio, nginx opcional):

```bash
docker compose up -d --build
```

Aplicar migraciones dentro del contenedor `web`:

```bash
docker compose exec web flask db upgrade
```

Nota: se ha añadido soporte para montar `/etc/letsencrypt` y `/var/www/letsencrypt` si quieres gestionar certificados desde contenedores (ver `deploy/nginx.docker.conf`).

5) Migraciones y backups
-------------------------
Fuente canónica para migraciones y backups:
- `docs/runbook.md`
- `deploy/README_BACKUPS.md`

6) Despliegue (producción)
---------------------------
Resumen rápido:
- Use Gunicorn behind nginx; ejemplos en `deploy/`.
- Obtenga certificados Let's Encrypt; helper `deploy/docker_get_cert.sh` y `deploy/README_TLS.md` incluyen instrucciones para ejecución con Docker.
- Configure secrets en el host (no comitear `.env`), y use `EnvironmentFile` para los servicios systemd cuando sea posible.

7) Observabilidad y seguridad
-----------------------------
- Sentry: configure `SENTRY_DSN` para recibir errores. Más información en `deploy/`.
- Logging: soporte para logs rotativos mediante variables `LOG_TO_FILE` y `LOG_FILE`.
- Hardening recomendado: ClamAV para escaneo de uploads, pip-audit para vulnerabilidades y pinning de dependencias.

8) Licencia y terceros
----------------------
Proyecto bajo licencia MIT — ver `LICENSE`.
Resumen de dependencias y notas legales en `THIRD_PARTY_LICENSES.md`.

9) Contribuir
-------------
- Fork / branch desde `main` → crear PR con tests.
- Sigue el CI (`.github/workflows/ci.yml`) que ejecuta tests con Postgres y MinIO.

Soporte / Contacto
-------------------
Si necesitas ayuda con el despliegue o CI, dime y lo detallo (systemd units, backups en S3, o runbook).

---

Archivos relevantes: `deploy/` (TLS, systemd, backups), `scripts/` (migraciones), `tests/` (suite de pruebas).
Usa `Flask-Migrate`:

