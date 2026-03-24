import os
import sqlite3
import sys
from pathlib import Path

db = Path('app.db')
print('DB path:', db.resolve())
print('DB exists:', db.exists())
if not db.exists():
    sys.exit(0)
conn = sqlite3.connect(db)
cur = conn.cursor()
for t in ('student','subject','grade','user'):
    try:
        cur.execute(f"select count(*) from {t}")
        print(t, cur.fetchone()[0])
    except Exception as e:
        print(t, 'ERR', e)
try:
    cur.execute("select id,first_name,last_name from student order by id desc limit 5")
    print('latest_students:', cur.fetchall())
except Exception as e:
    print('latest_students ERR', e)
conn.close()
