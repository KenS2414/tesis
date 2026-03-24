# Informe del proyecto

Resumen corto
- Proyecto: aplicación Flask pequeña para gestión de estudiantes y pagos.
- Entrypoint: `app.py`. Base de datos: SQLite (`app.db`).

Estructura principal
- `app.py`: modelos (`User`, `Student`, `Payment`), rutas y lógica en un único archivo.
- `init_db.py`: crea tablas y un usuario `admin` por defecto (contraseña `admin123`).
- `requirements.txt`: Flask, Flask-Login, Flask-SQLAlchemy.
- `templates/`: vistas (login, register, dashboard, students, payments).
- `static/style.css`: estilos mínimos.
- `static/uploads/`: directorio usado para almacenar comprobantes subidos.

Modelos y persistencia
- `User`: id, username, password_hash, role. Usa `flask_login`.
- `Student`: datos básicos (nombre, email, fecha nacimiento).
- `Payment`: referencia a `Student`, `amount`, `status`, `proof_filename`.
- URI DB por defecto: `sqlite:///app.db`.

Flujos y rutas clave
- Autenticación: `/login`, `/register`, `/logout`.
- Dashboard: `/dashboard` (requiere login).
- Estudiantes: `/students` (list), `/students/new`, `/students/<id>/edit`, `/students/<id>/delete`.
- Pagos usuario: `/payments` (lista), `/payments/new` (envío de pago con archivo opcional).
- Panel admin de pagos: `/admin/payments`, `/admin/payments/<id>/approve`, `/admin/payments/<id>/reject`.
- Lógica de vinculación: la app intenta relacionar `current_user.username` con `Student.email` para identificar al estudiante que envía pagos.

Plantillas (UI)
- `login.html` / `register.html`: formularios simples (usuario + contraseña).
- `dashboard.html`: enlaces a gestión de estudiantes.
- `students/list.html` y `students/form.html`: CRUD básico para estudiantes.
- `payments/list.html` y `payments/form.html`: envío y visualización de comprobantes; `payments/admin_list.html` para revisión y acciones administrativas.

Observaciones de seguridad y calidad (priorizadas)
1. SECRET_KEY por defecto `dev-secret` si no está en env — cambiar en producción.
2. No hay protección CSRF (usar `Flask-WTF` o `flask-wtf.CSRFProtect`).
3. Validación de uploads: no se verifican extensiones ni tipo MIME; riesgo de subir archivos peligrosos.
4. `init_db.py` crea admin con contraseña conocida; forzar cambio o usar clave segura/solo env.
5. Dependencia `Flask-SQLAlchemy>=3.0` puede requerir adaptaciones si el proyecto fue escrito para 2.x; verificar compatibilidad.
6. Relación usuario→estudiante basada en `username==email` es frágil; documentarlo o implementar campos explícitos para vincular cuentas.

Recomendaciones inmediatas (implementación rápida)
- Forzar `SECRET_KEY` por variable de entorno y evitar valor por defecto.
- Añadir `Flask-WTF` y habilitar CSRF globalmente.
- Limitar tipos de archivo aceptados y tamaño máximo (`app.config['MAX_CONTENT_LENGTH']`).
- Cambiar `init_db.py` para pedir o generar una contraseña segura o desactivar creación automática en entornos reales.
- Añadir validaciones a formularios (email, montos numéricos, formatos de fecha).

Mejoras arquitectónicas sugeridas
- Mover modelos a `models.py` y rutas a blueprints (`auth`, `students`, `payments`) para mantener el proyecto escalable.
- Añadir pruebas unitarias básicas (pytest) para rutas críticas y validación de modelos.
- Añadir logging y manejo de errores centralizado.

Cómo ejecutar localmente (PowerShell)
```
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python init_db.py
python app.py
```

Próximos pasos sugeridos
- ¿Quieres que implemente las correcciones críticas (CSRF + validación de uploads + SECRET_KEY) ahora como cambios en el repo?

---
Generado por auditoría rápida del código y plantillas en el repo.
