"""Read-only audit of the isolated rehearsal and its actual downloaded exports."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import urllib.request
import urllib.error
from uuid import UUID
from docx import Document
from pypdf import PdfReader

parser = argparse.ArgumentParser()
parser.add_argument('pasta')
parser.add_argument('--http', action='store_true', help='Verifica downloads no exercício selecionado em localhost:8002.')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
folder = Path(args.pasta).resolve(strict=True)
assert folder.parent == root / '.local' and folder.name.startswith('etapa4-ficticio-'), 'Use somente a pasta do exercício isolado.'
database = folder / 'exercicio.sqlite3'
def uid(value): return str(UUID(value))
with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as db:
    db.row_factory = sqlite3.Row
    assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    cases = db.execute('SELECT id,titulo FROM processos_atendimento').fetchall()
    assert len(cases) == 1 and cases[0]['titulo'].startswith('EXERCÍCIO FICTÍCIO ETAPA 4')
    case_id = uid(cases[0]['id'])
    drafts = db.execute('SELECT * FROM processos_minutaatendimento ORDER BY versao').fetchall()
    assert len(drafts) == 3 and [d['versao'] for d in drafts] == [1, 2, 3]
    latest = drafts[-1]
    assert latest['tipo'] == 'editada' and 'SIMULADA' in latest['motivo']
    text = latest['corpo']
    assert 'R$ 100.000,00' in drafts[0]['corpo'] and 'R$ 110.000,00' in text and 'R$ 100.000,00' not in text
    assert text.endswith('NOTA DE REVISÃO DO EXERCÍCIO FICTÍCIO. Texto salvo e conferido, sem ato real.')
    reviews = db.execute('SELECT * FROM processos_revisaofinalminuta').fetchall()
    assert len(reviews) == 1 and reviews[0]['minuta_id'] == latest['id']
    assert 'SIMULADA' in reviews[0]['motivo'] and 'EXERCÍCIO' in reviews[0]['motivo']
    assert reviews[0]['texto_sha256'] == hashlib.sha256(text.encode('utf-8')).hexdigest()
    assert db.execute("SELECT COUNT(*) FROM processos_pendenciafichaatendimento WHERE situacao != 'resolvida'").fetchone()[0] == 0
    binding = json.loads(db.execute('SELECT registros FROM processos_vinculacaominutaatendimento ORDER BY versao DESC LIMIT 1').fetchone()[0])
    assert binding['vendedor'] != binding['comprador']
    data = json.loads(latest['dados'])
    assert len(data) == 46
    for key, field in data.items():
        assert field['objeto_id'] == binding[key.split('.')[0]]
        assert field['origem']['tipo'] in ('documento', 'mensagem')
        for occurrence in field['ocorrencias']:
            assert text[occurrence['inicio']:occurrence['fim']] == field['valor']
    originals = db.execute('SELECT id,nome,sha256,conteudo FROM processos_anexoatendimento').fetchall()
    assert len(originals) == 20
    for row in originals:
        assert hashlib.sha256(row['conteudo']).hexdigest() == row['sha256']
        assert hashlib.sha256((folder / row['nome']).read_bytes()).hexdigest() == row['sha256']
    model_states = [bool(row[0]) for row in db.execute('SELECT aprovado FROM processos_modeloatendimento ORDER BY versao')]
    assert model_states == [False, True]
    revisions = db.execute('SELECT COUNT(*) FROM processos_revisaodadoatendimento').fetchone()[0]

word = Document(folder / 'minuta-ficticia-final.docx')
assert '\n'.join(p.text for p in word.paragraphs[3:]) == text
assert not word.styles['Title'].element.xpath('./w:pPr/w:pBdr')
assert not word.paragraphs[0]._p.xpath('./w:pPr/w:pBdr')
def compact(value): return re.sub(r'\s+', '', value)
def extract(path):
    reader = PdfReader(path)
    result = '\n'.join(p.extract_text() for p in reader.pages)
    for metadata in ['Minuta de compra e venda', 'Para revisão. Não constitui documento assinado ou ato concluído.', word.paragraphs[2].text, 'Minuta para revisão']:
        result = result.replace(metadata, '')
    result = re.sub(r'\|?\s*Página\s+\d+', '', result)
    assert compact(result) == compact(text), 'O conteúdo renderizado divergiu do texto salvo.'
    return len(reader.pages)
pdf_pages = extract(folder / 'minuta-ficticia-final.pdf')
word_pages = extract(folder / 'word-final/minuta-ficticia-final.pdf')
assert '25/10/2026' in word.paragraphs[2].text
source_package = json.loads((root / 'docs/piloto-profissional/padrao-acompanhado-v2.json').read_text(encoding='utf-8'))
assert source_package['aprovado'] is False and source_package['modelo']['aprovado'] is False
http_verified = False
if args.http:
    access = json.loads((folder / 'acesso-ficticio.json').read_text(encoding='utf-8'))
    payload = json.dumps({'username': access['usuario'], 'password': access['senha']}).encode()
    login = urllib.request.Request('http://localhost:8002/api/v1/auth/login/', data=payload, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(login, timeout=15) as response:
        token = json.load(response)['token']
    for row in originals:
        url = f"http://localhost:8002/api/v1/atendimentos/{case_id}/anexos/{uid(row['id'])}/download/"
        with urllib.request.urlopen(urllib.request.Request(url, headers={'Authorization':'Token '+token}), timeout=15) as response:
            assert hashlib.sha256(response.read()).hexdigest() == row['sha256']
    try:
        urllib.request.urlopen(url, timeout=10)
        raise AssertionError('Download sem autenticação foi aceito.')
    except urllib.error.HTTPError as error:
        assert error.code in (401, 403)
    http_verified = True

report = {'resultado': 'aprovado', 'dados': 'EXCLUSIVAMENTE FICTÍCIOS; aprovações e revisão simuladas',
          'atendimento_id': case_id, 'minuta_versao': latest['versao'], 'anexos_originais': len(originals),
          'campos_rastreados': len(data), 'revisoes_ficha': revisions, 'versoes_minuta': len(drafts),
          'estados_modelo_no_exercicio': model_states, 'padrao_profissional_oferecido_aprovado': False,
          'sem_pendencias_ativas': True, 'word_texto_exato': True, 'pdf_e_word_renderizado_texto_equivalente': True,
          'word_paginas': word_pages, 'pdf_paginas': pdf_pages, 'originais_http_apos_reinicio': http_verified,
          'hash_texto_salvo': hashlib.sha256(text.encode('utf-8')).hexdigest(),
          'arquivos': {name: hashlib.sha256((folder / name).read_bytes()).hexdigest() for name in ('minuta-ficticia-final.docx','minuta-ficticia-final.pdf')},
          'conferido_utc': datetime.now(timezone.utc).isoformat()}
(folder / 'resultado-final.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=True, indent=2))
