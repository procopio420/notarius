"""Synthetic HTTP save/restart/reopen and encrypted recovery, never the active DB."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

root = Path(__file__).resolve().parents[1]
api = root / 'apps/notarius-api'
sys.path.insert(0, str(api))
from apps.processos.modelo_referencia import BASE_REFERENCIA_V3, REFERENCIA
folder = root / '.local/verificacao-piloto' / (datetime.now().strftime('%Y%m%d-%H%M%S-') + secrets.token_hex(3))
folder.mkdir(parents=True)
source = folder / 'ficticio.sqlite3'
recovered = folder / 'recuperado.sqlite3'
password = secrets.token_urlsafe(24)
env = {**os.environ, 'DJANGO_SETTINGS_MODULE': 'config.settings_piloto',
       'NOTARIUS_PILOTO_DB': str(source), 'PYTHONIOENCODING': 'utf-8'}

def manage(*arguments, input=None):
    result = subprocess.run([sys.executable, str(api / 'manage.py'), *arguments],
                            cwd=api, env=env, text=True, input=input, capture_output=True, timeout=90)
    if result.returncode:
        raise RuntimeError('Comando do ensaio fictício falhou: ' + arguments[0])
    return result.stdout

manage('migrate', '--noinput')
seed = """
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.conf import settings
from apps.tenancy.models import Tenant
from apps.profiles.models import UserProfile
from apps.processos.models import Atendimento
from unittest.mock import patch
with patch('apps.processos.management.commands.criar_conta_piloto.getpass', return_value=PASSWORD):
    call_command('criar_conta_piloto', banco=str(settings.DATABASES['default']['NAME']),
                 usuario='ensaio_local_ficticio')
u=get_user_model().objects.get(username='ensaio_local_ficticio')
assert not u.is_superuser and not u.is_staff
assert u.profile.tenants.count() == 1
get_user_model().objects.create_user('ensaio_sem_acesso', password=PASSWORD)
other=Tenant.objects.create(nome='CARTORIO FICTICIO ISOLADO',uf='MT')
second=get_user_model().objects.create_user('ensaio_local_ficticio_b', password=PASSWORD)
profile,_=UserProfile.objects.get_or_create(user=second, defaults={'default_tenant': other})
profile.default_tenant=other; profile.save(update_fields=['default_tenant']); profile.tenants.add(other)
hidden=Atendimento.objects.create(tenant=other,criado_por=second,titulo='FICTICIO ISOLADO')
print('ENSAIO:'+str(other.pk)+':'+str(hidden.pk)+':'+str(u.profile.default_tenant_id))
""".replace('PASSWORD', repr(password))
seed_result = manage('shell', '-c', seed)
other, hidden, tenant_a = seed_result.split('ENSAIO:')[1].strip().split(':')
with socket.socket() as listener:
    listener.bind(('127.0.0.1', 0))
    port = listener.getsockname()[1]
base = f'http://127.0.0.1:{port}'
server = None
log = None

def request(path, method='GET', data=None, token=None, headers=None):
    headers = dict(headers or {})
    if token:
        headers['Authorization'] = 'Token ' + token
    if isinstance(data, dict):
        data = json.dumps(data).encode()
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(base + path, method=method, data=data, headers=headers)
    try:
        response = urllib.request.urlopen(req, timeout=20)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        body = response.read()
        return response.status, body, response.headers

def start(database):
    global server, log
    env['NOTARIUS_PILOTO_DB'] = str(database)
    log = (folder / 'servidor-ficticio.log').open('ab')
    server = subprocess.Popen([sys.executable, str(api / 'manage.py'), 'runserver',
                               f'127.0.0.1:{port}', '--noreload', '--nothreading'],
                              cwd=api, env=env, stdout=log, stderr=log)
    for _ in range(80):
        if server.poll() is not None:
            raise RuntimeError('Servidor fictício encerrou antes de ficar pronto.')
        try:
            if request('/health/')[0] == 200:
                return
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(.2)
    raise RuntimeError('Servidor fictício não iniciou no prazo.')

def stop():
    global server, log
    if server is not None:
        server.terminate()
        server.wait(timeout=15)
        server = None
    if log:
        log.close()
        log = None

def login(username='ensaio_local_ficticio'):
    status, body, _ = request('/api/v1/auth/login/', 'POST',
                              {'username': username, 'password': password})
    assert status == 200
    result = json.loads(body)
    assert set(result) == {'token', 'user'}
    assert 'tenants' not in result['user'] and 'default_tenant' not in result['user']
    return result['token']


def json_request(path, token, data=None, expected=200):
    status, body, _ = request(path, 'GET' if data is None else 'POST', data, token)
    assert status == expected, (path, status, body.decode(errors='replace'))
    return json.loads(body)


def upload_reference(path, token, original):
    boundary = 'notarius-ficticio-' + secrets.token_hex(8)
    multipart = (f'--{boundary}\r\nContent-Disposition: form-data; name="arquivo"; filename="ficticio.txt"\r\nContent-Type: text/plain\r\n\r\n'.encode()
                 + original + f'\r\n--{boundary}--\r\n'.encode())
    status, body, _ = request(path + 'anexos/', 'POST', multipart, token,
                              {'Content-Type': 'multipart/form-data; boundary=' + boundary})
    assert status == 201, status
    return json.loads(body)


def prepare_reference(path, token, attachment):
    model_path = path + 'modelo-minuta/'
    reference = json_request(model_path, token)['referencia']
    assert reference['versao'] == REFERENCIA['versao'] and reference['aprovado'] is False
    model = {**BASE_REFERENCIA_V3, 'justificativa': 'Ensaio fictício da escritura de compra e venda'}
    json_request(model_path, token, {**model, 'aprovado': False, 'versao_esperada': 0}, expected=201)
    draft_path = path + 'minuta-preparada/'
    initial = json_request(draft_path, token)
    assert not initial['pronto'] and not initial['versoes']

    json_request(f"{path}anexos/{attachment['id']}/organizacao/", token, {
        'client_id': str(uuid.uuid4()), 'versao_esperada': 0, 'leitura_versao': attachment['leitura_versao'],
        'finalidade': 'caso', 'tipo_documento': 'Fonte fictícia de ensaio',
        'vinculos': [{'objeto_id': None, 'paginas': []}], 'conferi': True,
        'motivo': 'Classificação simulada do documento fictício',
    }, expected=201)

    def pending():
        return json_request(path + 'conferencia/', token)['pendencias']

    def answer(question, value='', **fields):
        json_request(path + 'responder/', token, {
            'chave': question['chave'], 'assinatura': question['assinatura'],
            'versao_esperada': question['versao'], 'client_id': str(uuid.uuid4()),
            'valor': value, 'confirmar': True, 'justificativa': 'Conferência fictícia explícita', **fields,
        }, expected=201)

    answer(next(q for q in pending() if q['chave'] == f"anexo:{attachment['id']}"))
    for question in pending():
        # Each question carries a fingerprint; take the current copy before deciding.
        fresh = next(q for q in pending() if q['chave'] == question['chave'])
        candidate = next(c for c in fresh['candidatos'] if c.get('anexo_id') == attachment['id'])
        answer(fresh, candidate['valor'], fonte_documental={
            'pagina_id': candidate['id'], 'trecho': candidate['trecho'], 'canal': candidate['canal'],
            'organizacao_versao': candidate['organizacao_versao'],
        })
    assert not pending()
    current = json_request(draft_path, token)
    assert request(draft_path, 'POST', {'assinatura_esperada': current['assinatura']}, token)[0] == 400
    json_request(model_path, token, {**model, 'aprovado': True, 'versao_esperada': 1}, expected=201)
    current = json_request(draft_path, token)
    first, = json_request(draft_path, token, {'assinatura_esperada': current['assinatura']})['versoes']
    assert '{{' not in first['corpo'] and first['dados']['preco']['origem']['anexo_id'] == attachment['id']

    title = 'ESCRITURA DE COMPRA E VENDA'
    start = first['corpo'].index(title)
    styles = {'negrito': [[start, start + len(title)]]}
    edit = {'minuta_id': first['id'], 'versao_esperada': first['versao'], 'client_id': str(uuid.uuid4()),
            'corpo': first['corpo'] + '\n\nNota de teste: edição fictícia persistida.',
            'formatacao': styles, 'motivo': 'Edição simulada no ensaio de recuperação'}
    second = json_request(path + 'editar-minuta/', token, edit, expected=201)
    assert request(path + 'editar-minuta/', 'POST', {**edit, 'client_id': str(uuid.uuid4())}, token)[0] == 409
    review_path = f"{path}minutas/{second['id']}/revisar/"
    json_request(review_path, token, {'versao_esperada': second['versao'], 'motivo': 'Revisão fictícia',
                                     'conferi_texto': True, 'conferi_dados': True, 'conferi_fontes': True}, expected=201)
    versions = json_request(draft_path, token)['versoes']
    edited, previous = versions
    assert edited['corpo'] == edit['corpo'] and edited['formatacao'] == styles and previous == first
    assert edited['dados']['preco']['origem'] == first['dados']['preco']['origem']
    assert edited['revisao_final']['texto_corresponde']
    compare = json_request(f"{path}comparar-minutas/?base={first['id']}&destino={second['id']}", token)
    assert compare['texto_alterado'] and compare['formatacao_alterada']
    return versions


try:
    start(source)
    assert request('/api/v1/atendimentos/')[0] in (401, 403)
    assert request('/api/v1/auth/login/', 'POST', {'username': 'ensaio_local_ficticio', 'password': 'incorreta'})[0] == 401
    token = login()
    status, body, _ = request('/api/v1/auth/me/', token=token)
    assert status == 200 and 'tenants' not in json.loads(body)['user']
    assert request('/api/v1/auth/tenants/', token=token)[0] == 404
    assert request('/api/v1/auth/set-default-tenant/', 'POST', {}, token)[0] == 404
    status, body, _ = request('/api/v1/atendimentos/', 'POST', {'titulo': 'ENSAIO FICTICIO PERSISTENCIA'}, token)
    assert status == 201
    case = json.loads(body)['id']
    path = f'/api/v1/atendimentos/{case}/'
    message = {'texto': 'Preço: R$ 100.000,00', 'client_id': str(uuid.uuid4())}
    status, body, _ = request(path + 'mensagens/', 'POST', message, token)
    assert status == 201
    saved_message = json.loads(body)['id']
    status, body, _ = request(path + 'chat-ia/', token=token)
    assert status == 200 and json.loads(body)['habilitado'] is False
    assert request(path + 'chat-ia/', 'POST', {'mensagem_id': saved_message}, token)[0] == 400
    original = (root / 'docs/teste-escrevente/04-estrutura-referencia-ficticia.txt').read_bytes()
    attachment = upload_reference(path, token, original)
    download = path + f"anexos/{attachment['id']}/download/"
    assert request(download, token=token)[1] == original
    assert request(download)[0] in (401, 403)
    assert request(f'/api/v1/atendimentos/{hidden}/', token=token)[0] == 404
    assert request('/api/v1/atendimentos/', token=token, headers={'X-Tenant-ID': other})[0] == 403
    assert request('/api/v1/atendimentos/', token=token, headers={'X-Tenant-ID': 'uuid-invalido'})[0] < 500
    for blocked in ('/media/ficticio.txt', '/api/v1/ai/generate-minuta/', '/api/v1/auth/register/'):
        assert request(blocked, 'POST', {}, token)[0] == 404
    versions = prepare_reference(path, token, attachment)
    saved_models = json_request(path + 'modelo-minuta/', token)['versoes']
    assert len(saved_models) == 2 and saved_models[0]['aprovado'] and not saved_models[1]['aprovado']
    path_b = f'/api/v1/atendimentos/{hidden}/'
    token_b = login('ensaio_local_ficticio_b')
    original_b = original.replace(b'R$ 120.000,00 (cento e vinte mil reais)',
                                  b'R$ 125.000,00 (cento e vinte e cinco mil reais)')
    original_b = original_b.replace(b'R$ 80.000,00 em', b'R$ 85.000,00 em')
    assert original_b != original
    attachment_b = upload_reference(path_b, token_b, original_b)
    versions_b = prepare_reference(path_b, token_b, attachment_b)
    assert 'R$ 125.000,00' in versions_b[0]['corpo'] and versions_b[0]['corpo'] != versions[0]['corpo']
    download_b = path_b + f"anexos/{attachment_b['id']}/download/"
    saved_models_b = json_request(path_b + 'modelo-minuta/', token_b)['versoes']
    library = '/api/v1/atendimentos/biblioteca-modelos/'
    library_a = json_request(path + 'publicar-modelo/', token, {
        'modelo_id': saved_models[0]['id'], 'nome': 'Modelo fictício A', 'confirmar_sem_dados': True,
    }, expected=201)
    library_b = json_request(path_b + 'publicar-modelo/', token_b, {
        'modelo_id': saved_models_b[0]['id'], 'nome': 'Modelo fictício B', 'confirmar_sem_dados': True,
    }, expected=201)

    def verify_isolation(auth_a, auth_b):
        for auth, own_case, own_model, foreign_model, own_path, foreign_path, foreign_download, foreign_version in (
            (auth_a, case, library_a, library_b, path, path_b, download_b, versions_b[0]),
            (auth_b, hidden, library_b, library_a, path_b, path, download, versions[0]),
        ):
            assert [row['id'] for row in json_request('/api/v1/atendimentos/', auth)] == [own_case]
            assert [row['id'] for row in json_request(library, auth)['modelos']] == [own_model['id']]
            for denied in (foreign_path, foreign_download, foreign_path + 'anexos/', foreign_path + 'modelo-minuta/',
                           foreign_path + 'minuta-preparada/', foreign_path + 'ficha-detalhada/',
                           f"{foreign_path}minutas/{foreign_version['id']}/exportar/?formato=docx"):
                assert request(denied, token=auth)[0] == 404, denied
            reference = json_request(own_path + 'modelo-minuta/', auth)['referencia']['modelo']
            assert request(own_path + 'modelo-minuta/', 'POST', {**reference, 'aprovado': False,
                'justificativa': 'Ensaio fictício de referência de outro ambiente', 'versao_esperada': 2,
                'referencia_id': foreign_model['id']}, auth)[0] == 404
        assert request('/api/v1/atendimentos/', token=auth_b, headers={'X-Tenant-ID': tenant_a})[0] == 403

    # A member of the second space cannot choose the first space through a header.
    verify_isolation(token, token_b)

    def reopen():
        auth = login()
        status, body, headers = request(path, token=auth)
        assert status == 200 and json.loads(body)['titulo'] == 'ENSAIO FICTICIO PERSISTENCIA'
        assert headers['Cache-Control'] == 'no-store'
        assert json.loads(request(path + 'mensagens/', token=auth)[1])[0]['texto'] == message['texto']
        assert request(download, token=auth)[1] == original
        assert json_request(path + 'modelo-minuta/', auth)['versoes'] == saved_models
        assert json_request(path + 'minuta-preparada/', auth)['versoes'] == versions
        auth_b = login('ensaio_local_ficticio_b')
        assert request(download_b, token=auth_b)[1] == original_b
        assert json_request(path_b + 'modelo-minuta/', auth_b)['versoes'] == saved_models_b
        assert json_request(path_b + 'minuta-preparada/', auth_b)['versoes'] == versions_b
        verify_isolation(auth, auth_b)
        unauthorized = login('ensaio_sem_acesso')
        for denied in (path, download, path + 'modelo-minuta/', path + 'minuta-preparada/'):
            assert request(denied, token=unauthorized)[0] in (403, 404)
    stop()
    start(source)
    reopen()
    stop()
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    backup = folder / 'copia-ficticia.notarius'
    # Windows getpass reads the console rather than piped stdin. Only the
    # interactive prompt is simulated; execute the real commands in new processes.
    backup_password = secrets.token_urlsafe(24)
    env['NOTARIUS_SYNTHETIC_BACKUP_PASSWORD'] = backup_password
    for command, options in [('backup_local', {'saida': str(backup)}),
                             ('conferir_backup_local', {'arquivo': str(backup), 'recuperar_em': str(recovered)})]:
        code = ("import os; from unittest.mock import patch; from django.core.management import call_command; "
                f"p=patch('apps.processos.management.commands.{command}.getpass', "
                "return_value=os.environ['NOTARIUS_SYNTHETIC_BACKUP_PASSWORD']); p.start(); "
                f"call_command({command!r}, **{options!r}); p.stop()")
        manage('shell', '-c', code)
    del env['NOTARIUS_SYNTHETIC_BACKUP_PASSWORD']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    start(recovered)
    reopen()
    stop()
    assert password.encode() not in (folder / 'servidor-ficticio.log').read_bytes()
    assert original not in (folder / 'servidor-ficticio.log').read_bytes()
    report = {'resultado': 'aprovado', 'dados': 'exclusivamente ficticios',
              'login_real_http': True, 'login_incorreto_recusado': True,
              'conta_individual_restrita': True, 'chat_externo_recusado': True,
              'acesso_sem_autenticacao_recusado': True, 'isolamento_cartorio': True,
              'salvar_reiniciar_reabrir': True, 'restaurar_reabrir_em_outro_banco': True,
              'modelo_compra_venda_preservado': True, 'historico_minutas_e_fontes_preservado': True,
              'formatacao_e_revisao_final_preservadas': True, 'conta_sem_acesso_bloqueada': True,
              'isolamento_bidirecional_dois_ambientes': True, 'bibliotecas_e_reuso_isolados': True,
              'original_binario_sha256': hashlib.sha256(original).hexdigest(),
              'banco_fonte_preservado_na_restauracao': True,
              'rotas_externas_legadas_ausentes': True,
              'conteudo_e_senha_ausentes_no_log_do_ensaio': True,
              'entrada_interativa_senha_simulada_no_ensaio': True,
              'concluido_utc': datetime.now(timezone.utc).isoformat()}
    (folder / 'resultado.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True))
    print('Evidencia local: ' + str(folder.relative_to(root)))
finally:
    stop()
