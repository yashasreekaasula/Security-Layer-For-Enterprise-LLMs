$ErrorActionPreference='Stop'; Set-Location (Split-Path -Parent $PSScriptRoot)
@'
import sqlite3,csv
from pathlib import Path
p=Path('data/company_copilot.db'); out=Path('data/generated/company_knowledge_base.csv'); out.parent.mkdir(parents=True,exist_ok=True)
con=sqlite3.connect(p); cur=con.execute('SELECT * FROM documents')
with out.open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f); w.writerow([c[0] for c in cur.description]); w.writerows(cur)
print('Exported',con.execute('SELECT COUNT(*) FROM documents').fetchone()[0],'documents to',out.resolve()); con.close()
'@ | & .\.venv\Scripts\python.exe -
