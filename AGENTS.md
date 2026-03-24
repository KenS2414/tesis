# AGENTS.md - Instrucciones de Comportamiento para Jules

Este repositorio contiene el código fuente de un sistema de gestión escolar (Tesis de Grado).
El objetivo es mantener una arquitectura limpia, escalable y respetuosa con las decisiones técnicas ya tomadas.

## 1. Stack Tecnológico (Estricto)
- *Lenguaje:* Python 3.11+
- *Framework Web:* Flask (Modularizado con Blueprints).
- *Base de Datos:* PostgreSQL.
- *ORM:* SQLAlchemy.
- *Migraciones:* Flask-Migrate (Alembic). Siempre generar migraciones para cambios en modelos.
- *Almacenamiento:* MinIO / S3 (boto3). Los archivos subidos no deben persistir en el sistema de archivos local en producción.
- *Testing:* Pytest.

## 2. Reglas de Código (Python/Flask)
- *Estructura:*
    - Usa extensions.py para inicializar extensiones (db, migrate, s3).
    - Mantén los modelos en models.py (o paquete models/).
    - Las rutas deben estar organizadas en Blueprints, no en app.py.
- *Estilo:* Sigue PEP 8.
- *Configuración:* Usa python-dotenv. Las variables sensibles (SECRET_KEY, S3_KEYS) nunca deben estar harcodeadas.

## 3. Reglas de Entorno y Despliegue
- *Entorno del Desarrollador:* El usuario trabaja principalmente en *Windows (PowerShell)*. Si sugieres comandos de terminal, prioriza la sintaxis compatible o provee ambas (Bash/PowerShell).
- *Docker:* El proyecto se ejecuta en contenedores. Cualquier nueva dependencia debe agregarse a requirements.txt y considerar si requiere cambios en el Dockerfile.

## 4. Reglas de Frontend (Jinja2)
- *Seguridad:* Autoescaping activado.
- *Diseño:* Usa Bootstrap 5. Mantén la consistencia visual del panel administrativo.

## 5. Idioma y Contexto
- *Código:* Variables y funciones en Inglés (ej: get_student_grade).
- *Comentarios y Commits:* Español (ej: "Se agregó validación de notas").
- *Negocio:* Es un sistema escolar. Usa terminología adecuada: "Lapso" (Term), "Materia" (Subject), "Nota" (Grade), "Docente" (Teacher).