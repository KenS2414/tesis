.PHONY: ci-local ci-local-win

ci-local:
	bash scripts/ci_local.sh

ci-local-win:
	powershell -ExecutionPolicy Bypass -File scripts/ci_local.ps1

.PHONY: ci-unit ci-integration

ci-unit:
	# Run fast unit tests (uses current env; set SECRET_KEY if needed)
	pytest -q -m "not integration"

ci-integration:
	# Run integration tests against local Postgres and MinIO
	# Ensure Postgres and MinIO are running and env vars are set
	pytest -q -m integration --durations=20
