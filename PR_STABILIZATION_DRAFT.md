# PR de Estabilizacion - Factory, Runtime y CI Integration

## Titulo sugerido
`stabilization: factory-only app contract, runtime alignment, and hardened integration CI`

## Resumen
Esta PR congela el estado de estabilizacion logrado en el proyecto:
- Migracion completa al enfoque `create_app`.
- Retiro de compatibilidad legacy de imports en `app.py`.
- Alineacion de runtime entre Docker/Compose y despliegue systemd/nginx.
- Endurecimiento real del carril de integration en CI (Postgres + MinIO reales).
- Claridad de naming y documentacion de pruebas S3 (fake/functional/integration real).
- Consolidacion de documentacion operativa en fuente canonica.

## Motivacion
Reducir deuda tecnica y riesgo operacional, evitando contratos ambiguos en el entrypoint, eliminando drift de runtime entre entornos, y mejorando la confiabilidad del CI de integracion.

## Cambios principales

### 1) App factory y contrato publico
- `app.py` queda orientado a `create_app()` como contrato de arranque.
- Se retira compatibilidad legacy de exports del modulo `app` (app/db/modelos/helpers).
- Scripts y tests migrados a imports directos por modulo (`extensions`, `models`, `utils.aws`) y uso de `create_app`.

### 2) Runtime consistente
- Dockerfile y docker-compose usan `app:create_app()` con Gunicorn.
- `deploy/gunicorn.service` unificado en una sola unidad (sin duplicidad), bind a `unix:/run/resis.sock`.
- `deploy/nginx.resis.conf` alineado al mismo socket.
- `deploy/README_DEPLOY.md` actualizado con convenciones por entorno.

### 3) CI endurecido de verdad (integration lane)
- Workflow dividido y consolidado con:
  - `unit-tests` para `-m "not integration"`.
  - `integration-tests` para `-m integration`.
- `integration-tests` ahora:
  - levanta Postgres como service,
  - arranca MinIO,
  - espera disponibilidad de puertos,
  - crea bucket S3,
  - aplica migraciones (`flask db upgrade`),
  - ejecuta tests de integracion.
- Agregado `concurrency` para cancelar runs obsoletos en PR/branch.
- MinIO fijado a imagen versionada para reproducibilidad:
  - `minio/minio:RELEASE.2024-12-13T22-19-12Z`.
- Guardrail de cobertura del lane integration:
  - CI falla si recolecta menos de 2 tests con marker `integration`.

### 4) Suite S3 y naming
- Renombrado de test mal nombrado:
  - `tests/test_s3_integration.py` -> `tests/test_s3_functional_flow.py`.
- Nueva prueba de integracion real:
  - `tests/test_s3_real_integration.py`.
- Estado esperado de pruebas S3:
  - `test_s3_fakeclient.py`: unit/fake client.
  - `test_s3_functional_flow.py`: funcional con FakeS3.
  - `test_minio_e2e.py`: integration real MinIO.
  - `test_s3_real_integration.py`: integration real Postgres + MinIO.

### 5) Documentacion
- Fuente canonica de arranque/migraciones/backups:
  - `docs/runbook.md`.
- `README.md`, `README_LOCAL.md` y `deploy/README_DEPLOY.md` reducidos/ajustados para evitar duplicidad y contradicciones.
- `docs/ci_local.md` actualizado con flujo CI real y convencion S3.
- `pytest.ini` actualizado para aclarar alcance del marker `integration`.

## Validacion ejecutada

### Local no integration
- Comando:
  - `pytest -q -m "not integration"`
- Resultado final:
  - `48 passed, 1 skipped, 2 deselected`

### Local integration
- Comando:
  - `pytest -q -m integration`
- Resultado final:
  - `2 passed, 1 skipped, 48 deselected`

## Riesgos conocidos
- En servidor systemd, para aplicar cambios de unidad se requiere post-despliegue:
  - `systemctl daemon-reload`
  - `systemctl restart gunicorn`
- Esta accion ya esta documentada como post-deploy en `deploy/README_DEPLOY.md`.

## Plan de rollback
- Si falla despliegue:
  1. Restaurar unidad previa de `gunicorn.service`.
  2. Reiniciar gunicorn/nginx.
  3. Revertir commit(s) de runtime si fuese necesario.

## Checklist de salida
- [ ] CI en verde en PR (unit + integration).
- [ ] Revisión de cambios de `deploy/gunicorn.service` y `deploy/nginx.resis.conf` por quien opera servidor.
- [ ] Confirmar despliegue de prueba (staging o entorno equivalente).
- [ ] Aplicar pasos post-deploy systemd en release.

## Notas operativas
Este workspace no tiene metadata Git (`.git`), por lo que la apertura de PR no pudo ejecutarse automaticamente desde aqui. Este documento queda listo para usar como cuerpo de la PR cuando se trabaje desde el clon Git real.
