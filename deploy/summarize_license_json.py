import json
from pathlib import Path

F = Path(__file__).parent / 'license_report.json'
if not F.exists():
    print('license_report.json missing')
    raise SystemExit(2)

encs = ['utf-8-sig', 'utf-8', 'latin-1']
text = None
for e in encs:
    try:
        text = F.read_text(encoding=e)
        break
    except Exception:
        continue
if text is None:
    print('Failed to read JSON with tried encodings')
    raise SystemExit(3)
data = json.loads(text)
bad = []
for pkg in data:
    lic = (pkg.get('License') or '').upper()
    name = pkg.get('Name')
    if any(x in lic for x in ('GPL', 'AGPL', 'LGPL', 'UNKNOWN', 'PROPRIETARY')):
        bad.append((name, pkg.get('Version'), pkg.get('License')))

print('Found packages with copyleft/unknown licenses:')
for n,v,l in bad:
    print(f'- {n} {v}: {l}')

print(f"Total scanned: {len(data)}; flagged: {len(bad)}")
