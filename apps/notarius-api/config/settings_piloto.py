"""Local, offline pilot profile. Existing SQLite remains the default."""
from .settings import *  # noqa: F403
import secrets
from django.core.exceptions import ImproperlyConfigured

PILOTO_LOCAL = True
TIME_ZONE = 'America/Cuiaba'
private = BASE_DIR.parent.parent / '.local'
private.mkdir(exist_ok=True)
secret_file = private / 'piloto-secret.key'
try:
    with secret_file.open('x', encoding='utf-8') as output:
        output.write(secrets.token_urlsafe(64))
except FileExistsError:
    pass
SECRET_KEY = secret_file.read_text(encoding='utf-8').strip()
if len(SECRET_KEY) < 50:
    raise ImproperlyConfigured('Segredo local inválido; preserve o arquivo e confira a configuração.')

selection = private / 'piloto-banco.txt'
database = os.environ.get('NOTARIUS_PILOTO_DB') or (
    selection.read_text(encoding='utf-8-sig').strip() if selection.exists() else str(BASE_DIR / 'db.sqlite3'))
database = Path(database)
if not database.is_absolute():
    raise ImproperlyConfigured('O banco do piloto exige caminho absoluto.')
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': database,
                         'OPTIONS': {'timeout': 20}}}
DEBUG = False
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
ROOT_URLCONF = 'config.urls_piloto'
USE_S3 = False
STORAGES = {'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
            'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}}
AI_GENERATION_ENABLED = False
OPENAI_API_KEY = ''
ENABLE_ENOTARIADO = ENABLE_RI_CENTRAL = ENABLE_RTDPJ_CENTRAL = ENABLE_PROTESTO_CENTRAL = False
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = ['http://localhost:3002', 'http://127.0.0.1:3002']
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
MIDDLEWARE = ['apps.base.piloto.PilotoLocalMiddleware', *MIDDLEWARE]
# No request bodies, query strings, headers, response content or exception dumps.
LOGGING = {'version': 1, 'disable_existing_loggers': True,
           'handlers': {'discard': {'class': 'logging.NullHandler'}},
           'root': {'handlers': ['discard'], 'level': 'CRITICAL'},
           'loggers': {name: {'handlers': ['discard'], 'propagate': False}
                       for name in ['django', 'django.request', 'django.server']}}
