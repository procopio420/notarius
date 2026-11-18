"""Explicit fictional API test. Never reads the operational database or uploads."""
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / 'apps/notarius-api'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_piloto')
import django
django.setup()
from environ import Env
from apps.processos.provedor_documental import ProvedorTesteControlado
from apps.processos.contratos_documentais import EntradaDocumental
from apps.processos.casos_avaliacao_documental import casos
from apps.processos.avaliacao_documental import avaliar_caso

if sys.argv[1:] != ['--autorizado-ate-usd-0.50']:
    raise SystemExit('Exige autorização explícita para o teste pago.')
ledger = root / '.local/orcamento-ia.sqlite3'
report_path = root / '.local/resultado-teste-ia-contexto.json'
if report_path.exists():
    raise SystemExit('Já existe relatório: não repetir automaticamente nem sobrescrever evidências.')
# Read credentials only into the process, never print or persist them.
Env.read_env(root / 'apps/notarius-api/.env', overwrite=False)
provider = ProvedorTesteControlado(os.environ.get('OPENAI_API_KEY', ''), ledger)
report = {'data_utc': datetime.now(timezone.utc).isoformat(), 'modelo': 'gpt-6-luna',
          'apenas_ficticios': True, 'chamadas': [], 'precos_usd_milhao': {'entrada': 0.10, 'saida': 0.50}}
try:
    for case in casos():
        if case['id'] not in ['nome_simples', 'pagina_sem_texto', 'pagamento_futuro']:
            continue
        provider.uso = None
        row = {'caso': case['id']}
        report['chamadas'].append(row)
        try:
            output = provider.analisar(EntradaDocumental.model_validate(case['entrada']))
            row['avaliacao'] = avaliar_caso(case, output.model_dump())
            row['resposta_ficticia'] = output.model_dump()
            if row['avaliacao']['erros']:
                break
        except Exception as error:
            row['falha'] = getattr(error, 'codigo', type(error).__name__)
            row['diagnostico'] = provider.falha_tecnica
            break
        finally:
            row['uso'] = provider.uso
            if provider.uso:
                row['custo_estimado_usd'] = (provider.uso.get('input_tokens', 0) * 0.10 + provider.uso.get('output_tokens', 0) * 0.50) / 1_000_000
finally:
    with sqlite3.connect(f'file:{ledger.as_posix()}?mode=ro', uri=True) as db:
        report['reservado_centavos_usd'] = db.execute('SELECT reservado FROM orcamento WHERE id=1').fetchone()[0]
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'chamadas'}, ensure_ascii=False))
    print(json.dumps([{k:v for k,v in r.items() if k != 'resposta_ficticia'} for r in report['chamadas']], ensure_ascii=False))
