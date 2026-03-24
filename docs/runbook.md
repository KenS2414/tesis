# Runbook — Staging / Migrations / Backups

Breve guía para levantar staging, ejecutar migraciones y realizar backups/restores.

## Fuente canónica
- Esta es la fuente canónica para arranque del entorno y migraciones.
- Si encuentras pasos distintos en otros documentos, prioriza este archivo.
- Documentos resumidos que remiten aquí: `README.md`, `README_LOCAL.md`, `deploy/README_DEPLOY.md`.

## Checklist operativo (pre-release y despliegue)

Usar esta lista en cada salida a staging/producción. Marcar cada punto solo cuando quede validado.

### A) Pre-release (antes de desplegar)
- [ ] Variables de entorno críticas presentes: `SECRET_KEY`, `DATABASE_URL`, `S3_BUCKET`, `S3_ENDPOINT`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`.
- [ ] `FLASK_APP=app:create_app` en entorno de ejecución.
- [ ] Backup de base de datos ejecutado y verificado.
- [ ] Validación rápida de pruebas sin integración:
	- `pytest -q -m "not integration"`
- [ ] Validación de pruebas de integración (si el entorno lo permite):
	- `pytest -q -m integration`
- [ ] Confirmar migraciones pendientes y plan de rollback documentado.

### B) Ventana de despliegue
- [ ] Levantar/actualizar servicios del entorno.
- [ ] Aplicar migraciones:
	- `flask db upgrade`
- [ ] Confirmar salud de aplicación:
	- `GET /health` responde `ok`.
	- `GET /ready` responde `ready`.
- [ ] Verificar conectividad a almacenamiento S3/MinIO con carga/lectura de un archivo de prueba.
- [ ] Verificar login con usuario administrador y acceso al dashboard.

### C) Verificación funcional mínima (smoke test)
- [ ] Crear/editar estudiante.
- [ ] Asignar docente a materia.
- [ ] Registrar al menos una nota por lapso.
- [ ] Registrar/consultar un pago.
- [ ] Generar un reporte PDF básico.

### D) Post-deploy inmediato
- [ ] Revisar logs de aplicación sin errores críticos repetitivos.
- [ ] Revisar errores 5xx en proxy/app.
- [ ] Confirmar que no hubo regresión de permisos por rol (admin/docente/estudiante).
- [ ] Confirmar que el flujo de uploads sigue operativo.

### E) Rollback (si falla el despliegue)
- [ ] Detener cambios y comunicar incidente.
- [ ] Restaurar versión previa de servicio (gunicorn/nginx) según entorno.
- [ ] Restaurar backup de base de datos si hubo cambios irreversibles.
- [ ] Revalidar `GET /health` y login admin tras recuperación.

### Evidencia sugerida por release
- Fecha/hora de inicio y fin de ventana.
- Responsable de ejecución.
- Resultado de comandos clave (`flask db upgrade`, pruebas, health/ready).
- Incidentes encontrados y resolución aplicada.

## Prerrequisitos
- Docker Desktop instalado y funcionando
- Variables de entorno (en `env` o en el host): `SECRET_KEY`, `DATABASE_URL` (opcional para Postgres), `S3_BUCKET`, `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` (si aplica)
- `flask` CLI disponible (entorno virtual activado)

## Levantar servicios (docker-compose)
En la raíz del repo:
```powershell
docker compose up -d
```
Ver logs:
```powershell
docker compose logs -f web
```

## Variables de entorno temporales (PowerShell)
```powershell
$env:SECRET_KEY = 'valor_seguro_local'
$env:FLASK_APP = 'app:create_app'
# Si usas Postgres local en compose, puedes exportar DATABASE_URL
$env:DATABASE_URL = 'postgresql://postgres:password@db:5432/resis'
```

## Migraciones
Aplicar migraciones después de levantar servicios:
```powershell
flask db upgrade
```
Si usas SQLite no olvides que el archivo DB está en `instance/` por defecto (copia de seguridad fácil).

## Ejecutar tests
```powershell
# Pruebas rápidas (sin integración)
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
$env:SECRET_KEY = 'test-local-secret'
pytest -q -m "not integration"

# Pruebas de integración (requiere Postgres + MinIO)
$env:SECRET_KEY = 'test-ci-secret'
$env:ADMIN_PASSWORD = 'admin-ci-pass'
$env:DATABASE_URL = 'postgresql://resis:resispass@localhost:5432/resis'
$env:S3_ENDPOINT = 'http://localhost:9000'
$env:AWS_ACCESS_KEY_ID = 'minioadmin'
$env:AWS_SECRET_ACCESS_KEY = 'minioadmin'
$env:S3_BUCKET = 'resis-uploads'
pytest -q -m integration
```

## Backups
Postgres (desde host con conexión a la DB container o usando `docker exec`):
```bash
# Dump completo (desde host, con psql/pg_dump instalado)
pg_dump -h localhost -p 5432 -U postgres -F c -b -v -f resis_backup.dump resis

# O dentro del container
docker exec -it <db_container> pg_dump -U postgres -F c -b -v -f /tmp/resis_backup.dump resis
docker cp <db_container>:/tmp/resis_backup.dump ./resis_backup.dump
```

SQLite:
```powershell
# Solo copia el archivo de la base de datos
cp instance/resis.db backups/resis-sqlite-$(Get-Date -Format yyyyMMddHHmm).db
```

MinIO / S3 (usar `mc` o `aws`):
```bash
# usando mc (minio client)
mc alias set local http://localhost:9000 minioadmin minioadmin
mc cp --recursive ./uploads local/mybucket/uploads-backup-$(date +%Y%m%d)

# usando aws cli (con endpoint override)
AWS_ACCESS_KEY_ID=minioadmin AWS_SECRET_ACCESS_KEY=minioadmin aws s3 sync s3://mybucket ./s3-backup --endpoint-url http://localhost:9000
```

## Restore (Postgres)
```bash
# restablecer DB vacía y restaurar contenido
pg_restore -h localhost -p 5432 -U postgres -d resis ./resis_backup.dump
```

## Notas operativas
- Antes de `flask db upgrade` en staging/producción: siempre crear backup de la DB.
- Mantener `SECRET_KEY` fuera del repo; usar secretos del orquestador o variables de entorno protegidas en CI.
- CI: configurar secrets `DATABASE_URL`, `SECRET_KEY`, `S3_*` en GitHub Actions.
- Para datos grandes de uploads, usar MinIO en staging y sincronizar con S3 en prod.

## Comandos rápidos útiles
```powershell
# parar servicios
docker compose down
# ver contenedores
docker compose ps
# entrar al web container
docker compose exec web sh
```

---
Creado por el equipo de desarrollo. Ajusta rutas y credenciales según tu entorno.
