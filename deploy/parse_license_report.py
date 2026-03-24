import csv
from pathlib import Path

REPORT = Path(__file__).parent / "license_report.csv"

if not REPORT.exists():
    print(f"License report not found: {REPORT}")
    raise SystemExit(2)

risky = []
permissive = []

encodings = ['utf-8-sig', 'utf-8', 'latin-1']
for enc in encodings:
    try:
        fh = REPORT.open(newline='', encoding=enc)
        reader = csv.DictReader(fh)
        # consume one to validate
        _ = reader.fieldnames
        break
    except Exception:
        try:
            fh.close()
        except Exception:
            pass
else:
    print(f"Failed to open {REPORT} with tried encodings: {encodings}")
    raise SystemExit(3)
    for row in reader:
        name = row.get('Name')
        lic = (row.get('License') or '').strip()
        if not lic:
            risky.append((name, lic))
            continue
        L = lic.upper()
        if 'GPL' in L or 'AGPL' in L or 'LGPL' in L or 'GPL' in L:
            risky.append((name, lic))
        elif 'UNKNOWN' in L or 'PROPRIETARY' in L or 'UNLICENSED' in L:
            risky.append((name, lic))
        else:
            permissive.append((name, lic))

print("Risky or copyleft/unknown licenses:")
for n, l in sorted(risky):
    print(f"- {n}: {l}")

print('\nSummary:')
print(f"Total packages scanned: {len(risky)+len(permissive)}")
print(f"Permissive (likely MIT/BSD/Apache): {len(permissive)}")
print(f"Copyleft/Unknown: {len(risky)}")
