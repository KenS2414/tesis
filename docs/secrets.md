# Gestión de secretos y variables de entorno

Resumen corto:

- Nunca comitees secretos (SECRET_KEY, ADMIN_PASSWORD, credenciales de DB, claves de almacenamiento). Usa variables de entorno o un gestor de secretos.
- `.env` es válido solo para desarrollo local. Debe estar en `.gitignore`. Usa `.env.example` para documentar qué variables son necesarias.

Guía rápida — opciones recomendadas

1) GitHub Actions (staging / CI / deploy)

  - Define Secrets en el repositorio: `Settings → Secrets and variables → Actions → New repository secret`.
  - Ejemplo de secretos a crear:
    - `SECRET_KEY`
    - `DATABASE_URL` (postgres://...)
    - `ADMIN_PASSWORD` (solo si quieres usarlo en init)
    - `S3_ACCESS_KEY`, `S3_SECRET` (si usas object storage)

  - En tu workflow usa los secretos así:

    ```yaml
    env:
      SECRET_KEY: ${{ secrets.SECRET_KEY }}
      DATABASE_URL: ${{ secrets.DATABASE_URL }}
    ```

  - Ya en este repo el workflow CI exporta `SECRET_KEY` vía `$GITHUB_ENV`; recomendamos reemplazar la asignación directa por el uso de `secrets.SECRET_KEY` en el job `env`.

2) Docker / docker-compose (staging/local)

  - No incluyas valores secretos en `docker-compose.yml`. En su lugar, lee variables desde el entorno o un archivo `.env` que no esté versionado.

  - Ejemplo (no incluyas el archivo `.env` en el repo):

    ```yaml
    services:
      web:
        image: myapp:latest
        environment:
          - SECRET_KEY
          - DATABASE_URL
        env_file:
          - .env   # .env must be in .gitignore
    ```

3) Systemd / service (Linux)

  - Define variables de entorno en el unit file con `Environment=` o carga desde un archivo protegido:

    ```ini
    [Service]
    Environment="SECRET_KEY=shh-secret"
    EnvironmentFile=/etc/myapp/env
    ```

  - Asegura permisos (0600) para `/etc/myapp/env` y que sea accesible solo por el usuario del servicio.

4) Secret managers (producción recomendado)

  - Para entornos críticos usa Azure Key Vault, AWS Secrets Manager, HashiCorp Vault o similar.
  - Despliega una inicialización que recupera secretos durante el arranque del contenedor/pod (no commit). Por ejemplo, en Kubernetes montas un Secret o usas CSI driver.

5) Rotación y buenas prácticas

  - Rota `SECRET_KEY` y credenciales periódicamente si es posible.
  - Nunca loguees valores de secretos.
  - Para pruebas locales usa valores débiles en `.env` (solo dev).

6) Ajustes para este repo

  - `README.md` ahora incluye instrucciones de migraciones y despliegue; agrega referencia a este documento.
  - CI actual: reemplaza la escritura into `$GITHUB_ENV` por `env:` with `${{ secrets.SECRET_KEY }}` for production branches. Para pruebas de CI se puede seguir usando un test secret.

Si quieres, aplico los cambios en `.github/workflows/ci.yml` para leer `secrets.SECRET_KEY` y `secrets.DATABASE_URL` desde `env` (con fallback para tests). ¿Lo hago ahora?

## Nombres de Secrets a configurar en GitHub

Configura estos secrets en `Settings → Secrets and variables → Actions` para entornos de staging/production:

- `SECRET_KEY` — clave secreta principal para Flask.
- `DATABASE_URL` — URL de la base de datos (ej. `postgresql://user:pass@host:5432/dbname`).
- `ADMIN_PASSWORD` — (opcional) contraseña para `init_db.py` si la quieres fijar.
- `S3_ACCESS_KEY` — (opcional) acceso a S3 / compatible object storage.
- `S3_SECRET` — (opcional) secreto para S3.
- `S3_BUCKET` — (opcional) nombre del bucket donde se guardan uploads.

Nota importante para AWS / S3 compatible:

- Para AWS estándar, en lugar de `S3_ACCESS_KEY`/`S3_SECRET` puedes usar los nombres comunes:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_SESSION_TOKEN` (opcional, si usas credenciales temporales)
  - `S3_REGION` (ej. `us-east-1`)
  - `S3_ENDPOINT` (opcional, para MinIO o S3 compatible)

En GitHub Actions configura estos valores como Secrets. Ejemplo rápido de env en un workflow:

```yaml
env:
  AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
  AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  S3_BUCKET: ${{ secrets.S3_BUCKET }}
  S3_REGION: ${{ secrets.S3_REGION }}
  S3_ENDPOINT: ${{ secrets.S3_ENDPOINT }}
```

Si usas MinIO en staging, `S3_ENDPOINT` apunta al endpoint HTTP(S) y `S3_REGION` puede quedar vacío o `us-east-1`.
- `SMTP_URL` / `SMTP_HOST` — (opcional) servidor SMTP para notificaciones.
- `SMTP_USER` / `SMTP_PASSWORD` — (opcional) credenciales SMTP.

Snippet listo para pegar en tu workflow GitHub Actions (en el job, bajo `env:`):

```yaml
env:
  SECRET_KEY: ${{ secrets.SECRET_KEY }}
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
  ADMIN_PASSWORD: ${{ secrets.ADMIN_PASSWORD }}
  S3_ACCESS_KEY: ${{ secrets.S3_ACCESS_KEY }}
  S3_SECRET: ${{ secrets.S3_SECRET }}
  S3_BUCKET: ${{ secrets.S3_BUCKET }}
  SMTP_HOST: ${{ secrets.SMTP_HOST }}
  SMTP_USER: ${{ secrets.SMTP_USER }}
  SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
```

Para entornos de CI/PR puedes usar valores de prueba o variables de fallback, pero no comites secretos reales.

