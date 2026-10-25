"""Double-click helper: passwords stay in the terminal, never in arguments or files."""
from datetime import datetime
from pathlib import Path
import secrets
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
manage=root/'apps'/'notarius-api'/'manage.py'
folder=root/'.local'/'backups'
folder.mkdir(parents=True,exist_ok=True)
target=folder/f"notarius-{datetime.now():%Y%m%d-%H%M%S}-{secrets.token_hex(2)}.notarius"
result=subprocess.run([sys.executable,str(manage),'backup_local','--saida',str(target)],cwd=root)
raise SystemExit(result.returncode)
