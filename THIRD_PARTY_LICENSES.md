THIRD-PARTY LICENSES & COMPLIANCE
================================

This project is distributed under the MIT License (see `LICENSE`). It depends
on several third-party libraries. This document highlights notable licenses
found during the project's dependency audit and recommends actions for
compliance.

Full audit outputs are included in `deploy/license_report.csv` and
`deploy/license_report.json` — review those for the complete list.

1) Permissive licenses (typical — generally compatible with MIT)
- Flask (BSD)
- SQLAlchemy (MIT)
- boto3 (Apache-2.0)
- sentry-sdk (BSD/MIT)
- marshmallow / marshmallow-sqlalchemy (MIT/BSD)

These libraries are permissive and typically do not impose distribution constraints beyond attribution. Keep records of their licenses (the audit outputs) when preparing releases.

2) Copyleft or review-required licenses (action recommended)
- `psycopg2-binary` — flagged as LGPL in the audit. LGPL dependencies can impose obligations when distributing binaries. For production packaging consider using a non-binary build of the PostgreSQL driver (compile from source) or review the exact licensing terms and consult legal counsel if you plan to redistribute the application.
- MinIO (server) — AGPL. The MinIO server distribution is AGPL-licensed; while using MinIO as a service for local development is fine, packaging or distributing an AGPL server alongside your product can have copyleft implications. If you plan to redistribute images containing MinIO, review the AGPL terms.

3) Unknown / manual-check entries
If any dependency in `deploy/license_report.json` has the license marked as `UNKNOWN` or `OTHER`, inspect that package's `PKG-INFO` or its repository to identify the license and decide whether replacement is necessary.

Recommended actions
- Add this `THIRD_PARTY_LICENSES.md` to your release notes and include `deploy/license_report.*` in any release artifact.
- For distribution (e.g., shipping Docker images): avoid bundling AGPL components unless you are prepared to comply with AGPL obligations. Consider using alternative S3-compatible servers with permissive licenses for redistribution or keep MinIO only as a development dependency.
- Replace `psycopg2-binary` if redistribution of binary wheels is a concern; consider building `psycopg`/`psycopg2` from source during packaging or pin a source-built wheel.
- Keep a copy of all third-party license texts in `THIRD_PARTY_LICENSES/` (optional) for auditability.

Where to find the audit outputs
- `deploy/license_report.csv` — CSV summary of installed packages and licenses.
- `deploy/license_report.json` — JSON report used by parsing scripts.

If you want, I can:
- extract the full per-package license text files into `THIRD_PARTY_LICENSES/` (automated), or
- replace `psycopg2-binary` with a recommended alternative in `requirements.txt` and update the build instructions.
