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
from apps.tenancy.models import Tenant
from apps.profiles.models import UserProfile
from apps.processos.models import Atendimento
u=get_user_model().objects.create_user('ensaio_local_ficticio',password=PASSWORD)
t=Tenant.objects.create(nome='CARTORIO FICTICIO OPERACIONAL',uf='MT')
p,_=UserProfile.objects.get_or_create(user=u); p.tenants.add(t); p.default_tenant=t; p.save()
other=Tenant.objects.create(nome='CARTORIO FICTICIO ISOLADO',uf='MT')
hidden=Atendimento.objects.create(tenant=other,criado_por=u,titulo='FICTICIO ISOLADO')
print('ENSAIO:'+str(other.pk)+':'+str(hidden.pk))
""".replace('PASSWORD', repr(password))
seed_result = manage('shell', '-c', seed)
other, hidden = seed_result.split('ENSAIO:')[1].strip().split(':')
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

def login():
    status, body, _ = request('/api/v1/auth/login/', 'POST',
                              {'username': 'ensaio_local_ficticio', 'password': password})
    assert status == 200
    return json.loads(body)['token']

try:
    start(source)
    assert request('/api/v1/atendimentos/')[0] in (401, 403)
    assert request('/api/v1/auth/login/', 'POST', {'username': 'ensaio_local_ficticio', 'password': 'incorreta'})[0] == 401
    token = login()
    status, body, _ = request('/api/v1/atendimentos/', 'POST', {'titulo': 'ENSAIO FICTICIO PERSISTENCIA'}, token)
    assert status == 201
    case = json.loads(body)['id']
    path = f'/api/v1/atendimentos/{case}/'
    message = {'texto': 'CONTEUDO FICTICIO SALVO COM ACENTOS: ação', 'client_id': str(uuid.uuid4())}
    assert request(path + 'mensagens/', 'POST', message, token)[0] == 201
    original = b'ARQUIVO INTEIRAMENTE FICTICIO\r\nPreco informado: 12345\r\n'
    boundary = 'notarius-ficticio-' + secrets.token_hex(8)
    multipart = (f'--{boundary}\r\nContent-Disposition: form-data; name="arquivo"; filename="ficticio.txt"\r\nContent-Type: text/plain\r\n\r\n'.encode()
                 + original + f'\r\n--{boundary}--\r\n'.encode())
    status, body, _ = request(path + 'anexos/', 'POST', multipart, token,
                              {'Content-Type': 'multipart/form-data; boundary=' + boundary})
    assert status == 201, status
    attachment = json.loads(body)['id']
    download = path + f'anexos/{attachment}/download/'
    assert request(download, token=token)[1] == original
    assert request(download)[0] in (401, 403)
    assert request(f'/api/v1/atendimentos/{hidden}/', token=token)[0] == 404
    assert request('/api/v1/atendimentos/', token=token, headers={'X-Tenant-ID': other})[0] == 403
    assert request('/api/v1/atendimentos/', token=token, headers={'X-Tenant-ID': 'uuid-invalido'})[0] < 500
    for blocked in ('/media/ficticio.txt', '/api/v1/ai/generate-minuta/', '/api/v1/auth/register/'):
        assert request(blocked, 'POST', {}, token)[0] == 404
    def reopen():
        auth = login()
        status, body, headers = request(path, token=auth)
        assert status == 200 and json.loads(body)['titulo'] == 'ENSAIO FICTICIO PERSISTENCIA'
        assert headers['Cache-Control'] == 'no-store'
        assert json.loads(request(path + 'mensagens/', token=auth)[1])[0]['texto'] == message['texto']
        assert request(download, token=auth)[1] == original
        return auth
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
              'acesso_sem_autenticacao_recusado': True, 'isolamento_cartorio': True,
              'salvar_reiniciar_reabrir': True, 'restaurar_reabrir_em_outro_banco': True,
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
