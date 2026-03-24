# Ejecuta y prepara el entorno en PowerShell
if (-not (Test-Path venv)) { python -m venv venv }
. .\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:FLASK_APP = 'app:create_app'
$env:FLASK_ENV = 'development'
# Para desarrollo local, copia .env.example a .env y edítalo con tus valores.
# No deje valores secretos en este script.
python -m flask run --host=0.0.0.0
