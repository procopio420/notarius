"""Persistent synthetic HTTP rehearsal. Never targets or approves the operational DB."""
from pathlib import Path
from datetime import datetime, timezone
from io import BytesIO
from types import SimpleNamespace
import hashlib
import json
import os
import re
import secrets
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / 'apps/notarius-api'
FOLDER = ROOT / '.local' / ('etapa4-ficticio-' + datetime.now().strftime('%Y%m%d-%H%M%S-') + secrets.token_hex(3))
FOLDER.mkdir(parents=True)
DATABASE = FOLDER / 'exercicio.sqlite3'
PASSWORD = secrets.token_urlsafe(20)
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_piloto'
os.environ['NOTARIUS_PILOTO_DB'] = str(DATABASE)
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, str(API))
sys.path.insert(0, str(ROOT / 'packages'))
subprocess.run([sys.executable, str(API / 'manage.py'), 'migrate', '--noinput'],
               cwd=API, check=True, stdout=subprocess.DEVNULL)
import django
django.setup()
from django.contrib.auth import get_user_model
from apps.profiles.models import UserProfile
from apps.tenancy.models import Tenant
from django.db import connections
user = get_user_model().objects.create_user('exercicio_etapa4', password=PASSWORD)
tenant = Tenant.objects.create(nome='EXERCÍCIO FICTÍCIO ETAPA 4 — APROVAÇÕES SIMULADAS', uf='MT')
profile, _ = UserProfile.objects.get_or_create(user=user)
profile.tenants.add(tenant)
profile.default_tenant = tenant
profile.save()
(FOLDER / 'acesso-ficticio.json').write_text(json.dumps({'usuario':'exercicio_etapa4', 'senha':PASSWORD}), encoding='utf-8')
connections.close_all()
with socket.socket() as listener:
    listener.bind(('127.0.0.1', 0))
    PORT = listener.getsockname()[1]
BASE = f'http://127.0.0.1:{PORT}'
TOKEN = None
SERVER = None
LOG = (FOLDER / 'servidor-ficticio.log').open('ab')
TRACE = []

def request(path, data=None, method=None, raw=False, headers=None, expected=(200, 201)):
    headers = dict(headers or {})
    if TOKEN:
        headers['Authorization'] = 'Token ' + TOKEN
    if isinstance(data, dict):
        data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(BASE + path, method=method or ('POST' if data is not None else 'GET'), data=data, headers=headers)
    try:
        response = urllib.request.urlopen(req, timeout=180)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        body = response.read()
        status = response.status
    if status not in expected:
        raise RuntimeError(f'HTTP {status} em {path}: ' + body.decode('utf-8', errors='replace')[:1000])
    return body if raw else json.loads(body) if body else None

def start():
    global SERVER
    SERVER = subprocess.Popen([sys.executable, str(API / 'manage.py'), 'runserver',
        f'127.0.0.1:{PORT}', '--noreload', '--nothreading'], cwd=API, env=os.environ.copy(), stdout=LOG, stderr=LOG)
    for _ in range(100):
        if SERVER.poll() is not None:
            raise RuntimeError('Servidor fictício não iniciou.')
        try:
            if urllib.request.urlopen(BASE + '/health/', timeout=1).status == 200:
                return
        except OSError:
            time.sleep(.2)
    raise RuntimeError('Servidor fictício excedeu prazo de inicialização.')

def stop():
    global SERVER
    if SERVER:
        SERVER.terminate()
        SERVER.wait(timeout=15)
        SERVER = None

def login():
    global TOKEN
    TOKEN = request('/api/v1/auth/login/', {'username': 'exercicio_etapa4', 'password': PASSWORD})['token']

def note(text):
    TRACE.append(text)
    print(text, flush=True)

def cpf(seed):
    for n in (9, 10):
        seed += str((sum(int(seed[i]) * (n + 1 - i) for i in range(n)) * 10 % 11) % 10)
    return seed

try:
    start(); login()
    case = request('/api/v1/atendimentos/', {'titulo': 'EXERCÍCIO FICTÍCIO ETAPA 4 — SEM HOMOLOGAÇÃO PROFISSIONAL'})['id']
    base = f'/api/v1/atendimentos/{case}/'
    def call(path, data=None, **options):
        return request(base + path + '/', data, **options)
    package = call('modelo-minuta')['padrao_piloto']
    assert package['aprovado'] is False and package['modelo']['aprovado'] is False
    model = dict(package['modelo'])
    draft_model = call('modelo-minuta', model)
    def generate(expected=(200,)):
        state = call('minuta-preparada')
        return call('minuta-preparada', {'assinatura_esperada': state['assinatura']}, expected=expected)
    generate(expected=(400,))
    diagnosis = call('analise-documental')
    assert diagnosis['disponivel'] is False
    note('Cadastro, rascunho não aprovado e IA indisponível conferidos por HTTP.')
    ids = {}
    def sheet(): return call('ficha-detalhada')
    def alter(data):
        current = sheet()
        for field in data.get('campos', []):
            row = next(o for o in current['objetos'] if o['id'] == data['objeto_id'])
            field['contexto_assinatura'] = next(f for f in row['campos'] if f['chave'] == field['chave'])['contexto_assinatura']
        return call('ficha-detalhada', {'client_id': str(uuid4()), 'modelo_id': current['modelo_id'],
                    'justificativa': 'DECISÃO SIMULADA NO EXERCÍCIO FICTÍCIO, SEM ACEITE PROFISSIONAL.', **data})
    for position in model['registros_minuta']:
        links = {k + '_id': ids[v] for k, v in position['vinculos'].items()}
        if position['tipo'] == 'complemento':
            links['escopo'] = 'pessoa' if 'pessoa_a_id' in links else 'imovel' if 'imovel_id' in links else 'atendimento'
        ids[position['chave']] = alter({'operacao': 'criar', 'tipo': position['tipo'], **links})['objeto_id']
    def value(alias, key, position):
        person = 'ALFA' if alias == 'vendedor' else 'BETA'
        values = {'nome': 'PESSOA FICTÍCIA ' + person, 'cpf': cpf('123456789' if alias == 'vendedor' else '987654321'),
            'nacionalidade': 'NACIONALIDADE FICTÍCIA', 'profissao': 'PROFISSÃO FICTÍCIA',
            'estado_civil': 'ESTADO CIVIL FICTÍCIO PARA REVISÃO', 'documento_tipo': 'DOCUMENTO DE TESTE',
            'documento_numero': 'TESTE-0007-' + person, 'orgao_emissor': 'EMISSOR FICTÍCIO',
            'endereco': 'ENDEREÇO FICTÍCIO SEM LOCALIZAÇÃO REAL',
            'matricula': 'MATRÍCULA FICTÍCIA 0007', 'registro': 'REGISTRO IMOBILIÁRIO FICTÍCIO',
            'titularidade': 'Titularidade de exercício atribuída à pessoa fictícia ALFA, sem título real.',
            'aquisicao': 'Aquisição fictícia criada somente para testar a rastreabilidade, sem instrumento real.',
            'onus': 'Texto de exercício sobre ônus. Não é certidão nem declaração negativa de um imóvel real.',
            'preco': 'R$ 100.000,00', 'situacao_pagamento': 'previsto',
            'condicoes': 'Previsão fictícia de pagamento futuro de R$ 100.000,00. Sem declaração de recebimento.',
            'abertura': 'EXERCÍCIO INTEIRAMENTE FICTÍCIO. Minuta de teste, sem comparecimento ou ato real.',
            'encerramento': 'Encerramento de exercício. Não houve leitura, aceite ou assinatura de ato real.',
            'categoria': position.get('categoria', ''), 'situacao': 'informado'}
        if position['tipo'] == 'papel': return ('vendedor' if alias == 'papel_vendedor' else 'comprador') if key == 'tipo_papel' else 'direta'
        if key == 'descricao': return 'IMÓVEL INEXISTENTE DO EXERCÍCIO FICTÍCIO, sem correspondência com propriedade real.'
        if key == 'conteudo':
            return {'transmissao': 'Transmissão fictícia para teste, sem produzir direito ou ato real.',
                    'declaracao_vendedor': 'Declaração fictícia atribuída à parte ALFA somente no exercício.',
                    'declaracao_comprador': 'Declaração fictícia atribuída à parte BETA somente no exercício.',
                    'consulta_vendedor': 'Consulta de exercício relativa à pessoa ALFA; nenhuma consulta real foi feita.',
                    'consulta_comprador': 'Consulta de exercício relativa à pessoa BETA; nenhuma consulta real foi feita.',
                    'certidoes': 'Documento fictício do imóvel usado neste exercício, sem certidão real.',
                    'observacoes': 'Todos os dados, confirmações, decisões e aprovações deste banco são simulados. Sem validade profissional.'}.get(alias, position['rotulo'] + ': conteúdo exclusivamente fictício, sem afirmar providência ou declaração real.')
        return values[key]
    originals = {}
    for position in model['registros_minuta']:
        alias = position['chave']
        keys = [m['marcador'].split('.')[1] for m in package['mapa_campos'] if m['marcador'].startswith(alias + '.')]
        if position['tipo'] == 'negociacao': keys = ['preco', 'situacao_pagamento', 'condicoes']
        if position['tipo'] == 'complemento': keys = ['categoria', 'situacao', *keys]
        values = {key: value(alias, key, position) for key in keys}
        content = ('DOCUMENTO INTEIRAMENTE FICTÍCIO DO EXERCÍCIO ETAPA 4\n' + '\n'.join(k + ': ' + v for k, v in values.items())).encode('utf-8')
        name = 'FICTICIO-' + alias + '.txt'
        (FOLDER / name).write_bytes(content)
        boundary = 'ficticio-' + secrets.token_hex(8)
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="arquivo"; filename="{name}"\r\nContent-Type: text/plain\r\n\r\n'.encode() + content + f'\r\n--{boundary}--\r\n'.encode())
        file = call('anexos', body, headers={'Content-Type': 'multipart/form-data; boundary=' + boundary})
        assert hashlib.sha256(call(f"anexos/{file['id']}/download", raw=True)).hexdigest() == hashlib.sha256(content).hexdigest()
        owner = ids[alias] if position['tipo'] in ('pessoa', 'imovel') else ids[next(iter(position['vinculos'].values()))] if position['vinculos'] else None
        call(f"anexos/{file['id']}/organizacao", {'client_id': str(uuid4()), 'versao_esperada': 0,
             'leitura_versao': 1, 'finalidade': 'caso', 'tipo_documento': 'Fonte fictícia do exercício',
             'vinculos': [{'objeto_id': owner, 'paginas': []}], 'conferi': True,
             'motivo': 'CLASSIFICAÇÃO EXPLÍCITA SIMULADA, NENHUMA ASSOCIAÇÃO POR NOME.'})
        page = file['paginas'][0]
        fields = [{'chave': key, 'valor': val, 'valor_original': val, 'situacao': 'confirmado',
                   'versao_esperada': 0, 'confirmar': True, 'conferir_fonte': True, 'origem': 'documento',
                   'pagina_id': page['id'], 'leitura_versao': 1, 'organizacao_versao': 1, 'trecho_origem': val,
                   'canal_origem': 'texto'} for key, val in values.items()]
        alter({'operacao': 'salvar', 'objeto_id': ids[alias], 'campos': fields})
        originals[alias] = {'arquivo_id': file['id'], 'pagina_id': page['id'], 'sha256': hashlib.sha256(content).hexdigest()}
        note('Anexo e ficha com fonte documental explícita: ' + alias)
    # Fully populated facts cannot approve a model.
    generate(expected=(400,))
    approval = dict(model, aprovado=True, versao_esperada=draft_model['versao'],
                    justificativa='APROVAÇÃO SIMULADA EXCLUSIVAMENTE NO BANCO FICTÍCIO ETAPA 4; NÃO HOMOLOGA O PADRÃO.')
    approved_model = call('modelo-minuta', approval)
    def bind():
        current = call('vinculacao-minuta')
        return call('vinculacao-minuta', {'client_id': str(uuid4()), 'modelo_id': current['modelo_id'],
                    'versao_esperada': current['versao'], 'escopo_assinatura': current['escopo_assinatura'],
                    'registros': ids, 'exclusoes': [], 'conferir': True, 'motivo': 'VINCULAÇÃO SIMULADA POR ID NO EXERCÍCIO.'})
    bind()
    def resolve():
        rows = call('pendencias-ficha', {'operacao': 'atualizar'})['pendencias']
        for row in rows:
            if row['situacao'] == 'resolvida': continue
            context = row['contexto']
            if row['tipo'] == 'comparacao_fontes':
                current = context.get('revisao_atual')
                if not current or current['situacao'] != 'confirmado': continue
                revisions = [current['id']]
            elif row['tipo'] == 'pagina': revisions = context['usos_atuais']
            else: continue
            action = 'vincular' if revisions else 'nao_utilizar'
            call('pendencias-ficha', {'operacao': 'resolver', 'client_id': str(uuid4()),
                 'pendencia_id': row['id'], 'assinatura': row['assinatura'], 'versao_esperada': row['versao'],
                 'acao': action, 'revisoes_ids': revisions, 'evidencias_ids': [e['id'] for e in context.get('evidencias', [])],
                 'confirmei_revisao': True, 'justificativa': 'DECISÃO SIMULADA: todas as evidências do exercício conferidas; escolhida a revisão atual. Não é decisão profissional real.'})
        pending = call('conferencia')['pendencias']
        if pending: raise RuntimeError('Pendências não resolvidas no exercício: ' + json.dumps([(p['chave'],p['pergunta']) for p in pending], ensure_ascii=True))
    resolve()
    first = generate()['versoes'][0]
    export = f"minutas/{first['id']}/exportar"
    request(base + export + '/?formato=docx', expected=(409,), raw=True)
    note('Modelo original respeitado; aprovação simulada isolada, geração e bloqueio sem revisão final verificados.')
    # Correct price manually; retained documentary old price must remain visible.
    alter({'operacao': 'salvar', 'objeto_id': ids['negocio'], 'campos': [{
        'chave': 'preco', 'valor': 'R$ 110.000,00', 'valor_original': 'R$ 110.000,00', 'situacao': 'confirmado',
        'versao_esperada': 1, 'confirmar': True, 'conferir_fonte': True, 'origem': 'manual'}]})
    request(base + export + '/?formato=pdf', expected=(409,), raw=True)
    assert call('minuta-preparada')['versoes'][0]['desatualizada']
    generate(expected=(400,))
    alter({'operacao': 'salvar', 'objeto_id': ids['negocio'], 'campos': [{
        'chave': 'condicoes', 'valor': 'Previsão fictícia de pagamento futuro de R$ 110.000,00. Sem declaração de recebimento.',
        'situacao': 'confirmado', 'versao_esperada': 1, 'confirmar': True, 'conferir_fonte': True, 'origem': 'manual'}]})
    resolve()
    second = generate()['versoes'][0]
    text = second['corpo'] + '\n\nNOTA DE REVISÃO DO EXERCÍCIO FICTÍCIO. Texto salvo e conferido, sem ato real.'
    edited = call('editar-minuta', {'minuta_id': second['id'], 'versao_esperada': second['versao'],
                  'client_id': str(uuid4()), 'corpo': text, 'motivo': 'EDIÇÃO MANUAL SIMULADA, SEM VALIDADE PROFISSIONAL.'})
    compared = request(base + f"comparar-minutas/?base={second['id']}&destino={edited['id']}")
    assert compared['texto_alterado']
    call(f"minutas/{edited['id']}/revisar", {'versao_esperada': edited['versao'],
         'motivo': 'REVISÃO FINAL SIMULADA EXCLUSIVAMENTE PARA TESTAR EXPORTAÇÕES DO EXERCÍCIO.',
         'conferi_texto': True, 'conferi_dados': True, 'conferi_fontes': True})
    note('Correção, dependências reabertas, nova minuta, edição, comparação e revisão final simulada concluídas.')
    stop(); start(); login()
    latest = call('minuta-preparada')['versoes'][0]
    assert latest['id'] == edited['id'] and latest['corpo'] == text and latest['revisao_final']['texto_corresponde']
    for fmt in ('docx', 'pdf'):
        content = request(base + f"minutas/{edited['id']}/exportar/?formato={fmt}", raw=True)
        (FOLDER / ('minuta-ficticia-final.' + fmt)).write_bytes(content)
    from docx import Document
    from pypdf import PdfReader
    from apps.processos.exportacao import descricao
    from apps.processos.models import MinutaAtendimento
    word = Document(FOLDER / 'minuta-ficticia-final.docx')
    assert '\n'.join(p.text for p in word.paragraphs[3:]) == text
    pdf = PdfReader(FOLDER / 'minuta-ficticia-final.pdf')
    extracted = '\n'.join(p.extract_text() for p in pdf.pages)
    for metadata in ['Minuta de compra e venda', 'Para revisão. Não constitui documento assinado ou ato concluído.',
                     descricao(MinutaAtendimento.objects.get(pk=edited['id'])), 'Minuta para revisão']:
        extracted = extracted.replace(metadata, '')
    extracted = re.sub(r'Página\s+\d+', '', extracted)
    assert re.sub(r'\s+', '', extracted) == re.sub(r'\s+', '', text)
    assert 'R$ 110.000,00' in text and 'R$ 100.000,00' not in text
    for alias, file in originals.items():
        assert hashlib.sha256(call(f"anexos/{file['arquivo_id']}/download", raw=True)).hexdigest() == file['sha256']
    report = {'resultado': 'aprovado', 'tipo': 'EXERCÍCIO FICTÍCIO, APROVAÇÕES SIMULADAS, SEM HOMOLOGAÇÃO',
              'atendimento_id': case, 'modelo_oferecido_aprovado': False, 'modelo_simulado_id': approved_model['id'],
              'minuta_final_id': edited['id'], 'minuta_final_versao': edited['versao'],
              'banco': str(DATABASE.relative_to(ROOT)), 'anexos': len(originals), 'paginas_pdf': len(pdf.pages),
              'fontes': 'documentos classificados/páginas/trechos e mensagens manuais de correção preservados',
              'reabertura_apos_reinicio': True, 'conteudo_word_pdf_conferido': True,
              'ia_disponivel': False, 'concluido_utc': datetime.now(timezone.utc).isoformat(), 'percurso': TRACE}
    (FOLDER / 'resultado.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (FOLDER / 'acesso-ficticio.json').write_text(json.dumps({'usuario':'exercicio_etapa4', 'senha':PASSWORD}, ensure_ascii=False), encoding='utf-8')
    (FOLDER / 'texto-salvo.txt').write_text(text, encoding='utf-8')
    note('Exercício concluído; exportações e banco fictício em ' + str(FOLDER.relative_to(ROOT)))
finally:
    stop(); LOG.close(); connections.close_all()
