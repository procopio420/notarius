# Start an isolated, fictional purchase-and-sale case for browser QA.
param([Alias('EscrituraRasurada')][switch]$EscrituraCompleta)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$api = Join-Path $root 'apps/notarius-api'
$web = Join-Path $root 'apps/notarius-web'
$python = Join-Path $root '.venv/Scripts/python.exe'
$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
$node = if ($nodeCommand) { $nodeCommand.Source } else {
    Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
}
if (-not (Test-Path -LiteralPath $python) -or -not (Test-Path -LiteralPath $node) -or
    -not (Test-Path -LiteralPath (Join-Path $web 'node_modules/next/dist/bin/next'))) {
    throw 'Dependencias locais do Notarius ausentes.'
}
if (@(Get-NetTCPConnection -State Listen -LocalPort 3012,8012 -ErrorAction SilentlyContinue).Count) {
    throw 'As portas 3012 ou 8012 ja estao em uso. Este teste preserva os processos existentes.'
}
if (Test-Path -LiteralPath (Join-Path $root '.local/chat-ia-habilitado')) {
    throw 'Desative a IA externa antes de iniciar o ensaio ficticio.'
}

$qa = Join-Path $root ('.local/cartao-minuta-browser-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $qa -Force | Out-Null
@'
from pathlib import Path
from config.settings_piloto import *

MEDIA_ROOT = Path(__file__).parent / 'media'
NOTARIUS_MODELO_MINUTA_LOCAL = ''
CORS_ALLOWED_ORIGINS = ['http://localhost:3012', 'http://127.0.0.1:3012']
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
'@ | Set-Content -Encoding ASCII -LiteralPath (Join-Path $qa 'settings_cartao_qa.py')
@'
from rest_framework.test import APIClient
from tests.test_atendimentos import AtendimentoTests
from tests.test_modelo_referencia import ModeloReferenciaTests
from apps.processos.chat_ia import habilitado
from apps.processos.models import Atendimento
from os import environ

assert not habilitado()
reference = environ.get('NOTARIUS_QA_ESCRITURA_COMPLETA') == '1'
fixture = ModeloReferenciaTests() if reference else AtendimentoTests()
fixture.client = APIClient(HTTP_HOST='localhost')
fixture.setUp()
if reference:
    case = fixture.reference_case_with_confirmed_fictitious_document()
    assert fixture.select_reference(case, approved=True, expected=1).status_code == 201
    assert fixture.generate_draft(case).status_code == 200
    Atendimento.objects.filter(pk=case).update(titulo='Escritura de compra e venda - exemplo completo')
else:
    case = fixture.ready_for_draft()
    assert fixture.save_template(case).status_code == 201
state = fixture.client.get(f'/api/v1/atendimentos/{case}/minuta-preparada/')
assert state.data['pronto'] and bool(state.data['versoes']) == reference
print(case)
'@ | Set-Content -Encoding ASCII -LiteralPath (Join-Path $qa 'seed.py')

$variables = @('PYTHONPATH', 'DJANGO_SETTINGS_MODULE', 'NOTARIUS_PILOTO_DB',
    'NEXT_PUBLIC_API_URL', 'NEXT_PUBLIC_PILOTO_LOCAL', 'NEXT_TELEMETRY_DISABLED', 'NOTARIUS_QA_CARTAO_MINUTA', 'NOTARIUS_QA_ESCRITURA_COMPLETA')
$previous = @{}
foreach ($name in $variables) { $previous[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }
$server = $null
Push-Location $api
try {
    $env:PYTHONPATH = $qa
    $env:DJANGO_SETTINGS_MODULE = 'settings_cartao_qa'
    $env:NOTARIUS_PILOTO_DB = Join-Path $qa 'ficticio.sqlite3'
    $env:NEXT_PUBLIC_API_URL = 'http://127.0.0.1:8012/api/v1'
    $env:NEXT_PUBLIC_PILOTO_LOCAL = '1'
    $env:NEXT_TELEMETRY_DISABLED = '1'
    $env:NOTARIUS_QA_CARTAO_MINUTA = '1'
    $env:NOTARIUS_QA_ESCRITURA_COMPLETA = if ($EscrituraCompleta) { '1' } else { '0' }
    & $python manage.py migrate --noinput --verbosity 0
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar o banco ficticio.' }
    $caseOutput = & $python manage.py shell -c "from pathlib import Path; exec((Path(__import__('os').environ['PYTHONPATH']) / 'seed.py').read_text())"
    $case = $caseOutput | Select-Object -Last 1
    if ($LASTEXITCODE -ne 0 -or $case -notmatch '^[a-f0-9-]{36}$') { throw 'Falha ao preparar o caso ficticio.' }
    $apiLog = Join-Path $qa 'api-error.log'
    $server = Start-Process -FilePath $python -ArgumentList @('-u', 'manage.py', 'runserver', '127.0.0.1:8012', '--noreload', '--nothreading') -WorkingDirectory $api -WindowStyle Hidden -RedirectStandardOutput (Join-Path $qa 'api-out.log') -RedirectStandardError $apiLog -PassThru
    $ready = $false
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        if ($server.HasExited) {
            Get-Content -LiteralPath $apiLog -Tail 10
            throw 'A API do ensaio encerrou durante a inicializacao.'
        }
        try { $ready = (Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/health/' -TimeoutSec 1).StatusCode -eq 200 } catch { }
        if ($ready) { break }
        Start-Sleep -Milliseconds 500
    }
    if (-not $ready) { throw 'O PowerShell nao conseguiu acessar a API local na porta 8012.' }
    Write-Host "Caso ficticio: http://127.0.0.1:3012/atendimentos/$case"
    Write-Host 'Conta ficticia: qa_atendimento / test-only. Mantenha esta janela aberta durante o teste.'
    Set-Location $web
    New-Item -ItemType Directory -Path '.next' -Force | Out-Null
    '{"extends":"../tsconfig.json","compilerOptions":{"baseUrl":".."},"include":["../next-env.d.ts","../src/**/*.ts","../src/**/*.tsx"]}' |
        Set-Content -Encoding ASCII -LiteralPath '.next/tsconfig-cartao-minuta-qa.json'
    & $node 'node_modules/next/dist/bin/next' dev --port 3012 --hostname 127.0.0.1
} finally {
    if ($server -and -not $server.HasExited) { Stop-Process -Id $server.Id -ErrorAction SilentlyContinue }
    Pop-Location
    foreach ($name in $variables) { [Environment]::SetEnvironmentVariable($name, $previous[$name], 'Process') }
}
