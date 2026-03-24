# Tareas asignadas para tu compañero (backend, sin acceso al servidor)

Este archivo describe tareas concretas que puede implementar localmente sin necesidad de acceso al servidor. Cada tarea incluye: descripción, archivos a modificar, criterios de aceptación, tests y comandos para probar localmente.

---

## 1) Módulo `Subject` — Extender modelo y CRUD avanzado
- Qué: Extender `Subject` para incluir `category`, `credits`, `description` y añadir endpoints CRUD robustos (paginación, búsqueda por categoría). Crear migración.
- Archivos a cambiar:
  - `models.py` (añadir campos a `Subject`)
  - `students_bp.py` (extender endpoints `new_subject`, `edit_subject`, `list_students`/subjects)
  - `migrations/` (generar migración con `flask db migrate`)
- Criterios de aceptación:
  - Nuevo esquema aplica correctamente con `flask db upgrade`.
  - Endpoints `POST /students/subjects/new`, `POST /students/subjects/<id>/edit` aceptan y validan los nuevos campos.
  - Búsqueda por `category` funciona en la lista de materias.
- Tests a añadir:
  - `tests/test_subjects_extended.py` con casos de creación, edición, validación y filtrado.
- Cómo probar local:
  ```powershell
  $env:FLASK_APP='app.py'
  & .\venv\Scripts\python.exe -m flask db migrate -m "subjects: add fields"
  & .\venv\Scripts\python.exe -m flask db upgrade
  & .\venv\Scripts\python.exe -m pytest tests/test_subjects_extended.py -q
  ```

---

## 2) Roles `teacher` / `student` — endpoints para gestión de roles
- Qué: Añadir endpoints que permitan a un `admin` asignar roles y crear flujo de registro/edición para `teacher`. Mejorar `User` si es necesario.
- Archivos a cambiar:
  - `models.py` (`User` ya tiene `role`, añadir helper si conviene)
  - `students_bp.py` o `app.py` (nuevo endpoint admin para asignar rol)
  - `utils/auth.py` (verificar decorador y mensajes)
- Criterios de aceptación:
  - `admin` puede cambiar role de un usuario mediante un `POST` protegido.
  - `requires_roles` sigue funcionando para `teacher` y `admin`.
- Tests a añadir:
  - `tests/test_roles.py` con: creación de usuario, cambio de role por admin, verificación de acceso restringido.
- Cómo probar local:
  ```powershell
  & .\venv\Scripts\python.exe -m pytest tests/test_roles.py -q
  ```

---

## 3) Reportes en PDF (gradebook y payments)
- Qué: Implementar utilitario `utils/pdf_reports.py` que genere PDF para:
  - comprobante de pago (cuando admin aprueba)
  - gradebook por materia (lista de alumnos y notas)
  Se puede usar `WeasyPrint` o `ReportLab` (añadir dependencia si hace falta en `requirements.txt`).
- Archivos a añadir/editar:
  - `utils/pdf_reports.py` (nuevo)
  - `students_bp.py` o `payments` admin endpoints para `GET /reports/gradebook?subject_id=..` y `GET /reports/payment/<id>`
- Criterios de aceptación:
  - Al solicitar el endpoint, se devuelve `application/pdf` con contenido razonable.
  - Se añade test que verifica el `Content-Type` y que el PDF no está vacío.
- Tests a añadir:
  - `tests/test_pdf_reports.py` (mock de datos y verificación de headers y tamaño).
- Cómo probar local:
  ```powershell
  & .\venv\Scripts\python.exe -m pip install WeasyPrint   # opcional
  & .\venv\Scripts\python.exe -m pytest tests/test_pdf_reports.py -q
  ```

---

## 4) Import / Export CSV para `students`, `subjects`, `grades`
- Qué: Script reusable `scripts/import_export.py` y endpoints protegidos para subir CSV y exportar datos.
- Archivos a añadir/editar:
  - `scripts/import_export.py` (parser CSV -> DB)
  - `students_bp.py` (endpoints `POST /students/import`, `GET /students/export.csv` para admin)
  - `tests/fixtures/` (CSV de ejemplo)
- Criterios de aceptación:
  - Import valida columnas y crea/actualiza registros correctamente.
  - Export produce CSV con encabezados correctos.
- Tests a añadir:
  - `tests/test_import_export.py` cubriendo parsing, validación y uso del endpoint.
- Cómo probar local:
  ```powershell
  & .\venv\Scripts\python.exe -m pytest tests/test_import_export.py -q
  ```

---

## 5) Gradebook — edición masiva y export CSV (backend)
- Qué: Endpoint `POST /gradebook/<subject_id>/bulk_update` que recibe JSON con lista de `{student_id, score, comment}` y actualiza/crea `Grade` en batch; endpoint `GET /gradebook/<subject_id>.csv` para export.
- Archivos a cambiar:
  - `students_bp.py` (nuevas rutas)
  - `utils/export.py` (opcional)
- Criterios de aceptación:
  - Bulk update procesa JSON en una transacción: o todo OK o rollback.
  - Export CSV se descarga con las notas actuales.
- Tests a añadir:
  - `tests/test_gradebook_bulk.py` para chequear transacción y export.
- Cómo probar local:
  ```powershell
  & .\venv\Scripts\python.exe -m pytest tests/test_gradebook_bulk.py -q
  ```

---

## 6) Tests y fixtures (soporte para todo lo anterior)
- Qué: Añadir/mejorar `tests/conftest.py` con fixtures reutilizables: `app`, `db`, `client`, `admin_user`, `teacher_user`, `sample_students`, `sample_subjects`.
- Archivos a cambiar:
  - `tests/conftest.py` (nuevo o mejora)
  - Ajustar tests existentes para usar las nuevas fixtures.
- Criterios de aceptación:
  - Los nuevos tests pasan localmente con `pytest`.
- Cómo probar local:
  ```powershell
  & .\venv\Scripts\python.exe -m pytest -q
  ```

---

### Reglas al entregar (al crear PR)
- Crear una rama por tarea: `feature/<tarea-breve>` (ej.: `feature/subjects-extended`).
- Incluir tests nuevos y/o actualizar existentes; los tests deben pasar localmente antes del PR.
- Añadir descripción con: archivos modificados, comandos para correr tests, y cómo verificar la funcionalidad.
- No subir credenciales ni cambios en `instance/` o archivos de configuración sensibles.

---

Si quieres, puedo:
- crear los issues automáticamente (archivo `ISSUES.md`) con estos enunciados, o
- generar plantillas de `tests/conftest.py` y CSV de ejemplo en `tests/fixtures/` para que empiece ya.

Indica si quieres que genere `ISSUES.md` y/o `tests/conftest.py` automáticamente. 

---

## Fixtures añadidos (por el asistente)
- Archivo creado: `tests/conftest.py`
- Propósito: proporcionar fixtures reutilizables para facilitar el trabajo del equipo sin acceso al servidor. Incluye:
  - `app`, `client`, `runner` — entorno de prueba con `sqlite:///:memory:` y creación/limpieza de la base de datos.
  - `admin_user`, `teacher_user` — usuarios de prueba con roles y contraseñas predefinidas.
  - `sample_subjects`, `sample_students` — datos de ejemplo para pruebas funcionales.
  - `auth_client` — cliente de test ya autenticado como `admin`.

Cómo usar:
```powershell
& .\venv\Scripts\python.exe -m pytest -q
```

Los tests nuevos o modificados deben usar estas fixtures para ser reproducibles localmente.
