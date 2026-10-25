"""Read-only validation used before selecting an existing pilot database."""
from contextlib import closing
from pathlib import Path
import sqlite3
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'apps/notarius-api'))
from apps.processos.backup_local import inspect_database

try:
    database = Path(sys.argv[1]).resolve(strict=True)
    # A real database must never become an unignored Git input.
    ignored = subprocess.run(['git', 'check-ignore', '--quiet', '--', str(database)], cwd=root)
    tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', '--', str(database)],
                             cwd=root, capture_output=True)
    if ignored.returncode != 0 or tracked.returncode == 0:
        raise ValueError()
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as connection:
        inspect_database(connection)
except Exception:
    raise SystemExit('Banco recusado: confira integridade, estrutura e exclusão do Git. Nenhum banco foi alterado.')
print('Banco SQLite conferido em modo somente leitura; conteúdo não exibido.')
