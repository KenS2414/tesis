# Issues generadas automáticamente

Se listan las tareas descritas en `TASKS_FOR_COMPANION.md` como issues individuales para implementar localmente.

1) subjects-extended
- Resumen: Extender el modelo `Subject` con `category`, `credits`, `description` y CRUD avanzado (paginación, búsqueda por categoría).
- Archivos: models.py, students_bp.py, migrations/
- Tests: tests/test_subjects_extended.py
- Comandos de prueba:
  - $env:FLASK_APP='app.py'
  - python -m flask db migrate -m "subjects: add fields"
  - python -m flask db upgrade
  - python -m pytest tests/test_subjects_extended.py -q

2) roles-management
- Resumen: Endpoints para que `admin` asigne roles (`teacher`/`student`) y flujo de registro/edición para `teacher`.
- Archivos: models.py, students_bp.py o app.py, utils/auth.py
- Tests: tests/test_roles.py

3) pdf-reports
- Resumen: Utilitario `utils/pdf_reports.py` para generar PDFs (comprobante de pago y gradebook). Añadir endpoints que devuelvan `application/pdf`.
- Dependencias: WeasyPrint o ReportLab (actualizar requirements.txt si procede)
- Tests: tests/test_pdf_reports.py

4) import-export-csv
- Resumen: `scripts/import_export.py` y endpoints para importar/exportar CSV de `students`, `subjects`, `grades`.
- Archivos: scripts/import_export.py, students_bp.py, tests/fixtures/
- Tests: tests/test_import_export.py

5) gradebook-bulk
- Resumen: Endpoint `POST /gradebook/<subject_id>/bulk_update` (transaccional) y `GET /gradebook/<subject_id>.csv`.
- Archivos: students_bp.py, utils/export.py (opcional)
- Tests: tests/test_gradebook_bulk.py

6) tests-fixtures
- Resumen: Mejorar/añadir fixtures reutilizables en `tests/conftest.py` para `app`, `db`, `client`, `admin_user`, `teacher_user`, `sample_students`, `sample_subjects`.
- Tests: actualizar tests existentes para usar las fixtures.

Reglas al entregar:
- Crear rama por tarea: feature/<tarea-breve>
- Incluir tests y documentación en la PR
- No subir credenciales ni archivos dentro de `instance/`
