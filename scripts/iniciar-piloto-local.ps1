param([string]$Banco)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$apiFolder = Join-Path $projectRoot 'apps/notarius-api'
$webFolder = Join-Path $projectRoot 'apps/notarius-web'
$pythonPath = Join-Path $projectRoot '.venv/Scripts/python.exe'
$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
$nodePath = if ($nodeCommand) { $nodeCommand.Source } else { Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' }
$privateFolder = Join-Path $projectRoot '.local'
$logFolder = Join-Path $privateFolder 'logs/piloto'
if (-not (Test-Path -LiteralPath $pythonPath) -or -not (Test-Path -LiteralPath $nodePath) -or -not (Test-Path -LiteralPath (Join-Path $webFolder 'node_modules/next/dist/bin/next'))) {
    throw 'Dependências locais ausentes. Não foi instalado nem baixado nenhum componente.'
}
$listeners = @(Get-NetTCPConnection -State Listen -LocalPort 3002,8002 -ErrorAction SilentlyContinue)
if ($listeners.Count) { throw 'Encerre os serviços com scripts/encerrar-piloto-local.ps1 antes de iniciar ou trocar o banco.' }
New-Item -ItemType Directory -Force -Path $logFolder | Out-Null
if ($Banco) {
    $resolved = (Resolve-Path -LiteralPath $Banco).Path
    # Verify integrity/schema before persisting the explicit database selection.
    & $pythonPath (Join-Path $PSScriptRoot 'conferir-banco-piloto.py') $resolved
    if ($LASTEXITCODE -ne 0) { throw 'O banco selecionado não passou na conferência. A seleção anterior foi preservada.' }
    [IO.File]::WriteAllText((Join-Path $privateFolder 'piloto-banco.txt'), $resolved, [Text.UTF8Encoding]::new($false))
}
$selected = Join-Path $privateFolder 'piloto-banco.txt'
$database = if (Test-Path -LiteralPath $selected) { (Get-Content -LiteralPath $selected -Raw).Trim() } else { Join-Path $apiFolder 'db.sqlite3' }
if (-not (Test-Path -LiteralPath $database -PathType Leaf)) { throw 'Banco não encontrado; nenhum banco vazio foi criado. Confira a seleção local.' }
& $pythonPath (Join-Path $PSScriptRoot 'conferir-banco-piloto.py') $database
if ($LASTEXITCODE -ne 0) { throw 'O banco não passou na conferência. Nenhum serviço iniciado.' }
$previousSettings = $env:DJANGO_SETTINGS_MODULE
$previousDatabase = $env:NOTARIUS_PILOTO_DB
$previousApi = $env:NEXT_PUBLIC_API_URL
$previousTelemetry = $env:NEXT_TELEMETRY_DISABLED
$previousPilot = $env:NEXT_PUBLIC_PILOTO_LOCAL
try {
    $env:DJANGO_SETTINGS_MODULE = 'config.settings_piloto'
    $env:NOTARIUS_PILOTO_DB = $database
    $env:NEXT_PUBLIC_API_URL = 'http://localhost:8002/api/v1'
    $env:NEXT_TELEMETRY_DISABLED = '1'
    $env:NEXT_PUBLIC_PILOTO_LOCAL = '1'
    & $pythonPath (Join-Path $apiFolder 'manage.py') check
    if ($LASTEXITCODE -ne 0) { throw 'Falha na configuração. Nenhum serviço iniciado.' }
    & $pythonPath (Join-Path $apiFolder 'manage.py') migrate --check
    if ($LASTEXITCODE -ne 0) { throw 'Há migrações pendentes. Faça backup e aplique-as antes de iniciar; nenhuma migração automática foi feita.' }
    $manageArgument = '"' + (Join-Path $apiFolder 'manage.py') + '"'
    $apiProcess = Start-Process -FilePath $pythonPath -ArgumentList @($manageArgument, 'runserver', '127.0.0.1:8002', '--noreload', '--nothreading') -WorkingDirectory $apiFolder -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logFolder 'api-out.log') -RedirectStandardError (Join-Path $logFolder 'api-error.log') -PassThru
    try {
        $ready = $false
        for ($attempt = 0; $attempt -lt 30; $attempt++) {
            if ($apiProcess.HasExited) { throw 'A API encerrou durante a inicialização. Confira os logs privados.' }
            try { $ready = (Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8002/health/' -TimeoutSec 1).StatusCode -eq 200 } catch { }
            if ($ready) { break }
            Start-Sleep -Milliseconds 500
        }
        if (-not $ready) { throw 'A API não ficou pronta no prazo.' }
        $webProcess = Start-Process -FilePath $nodePath -ArgumentList @('node_modules/next/dist/bin/next', 'dev', '--turbopack', '--port', '3002', '--hostname', '127.0.0.1') -WorkingDirectory $webFolder -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logFolder 'web-out.log') -RedirectStandardError (Join-Path $logFolder 'web-error.log') -PassThru
        $ready = $false
        for ($attempt = 0; $attempt -lt 30; $attempt++) {
            if ($webProcess.HasExited) { throw 'A interface encerrou durante a inicialização.' }
            try { $ready = (Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:3002/login' -TimeoutSec 2).StatusCode -eq 200 } catch { }
            if ($ready) { break }
            Start-Sleep -Milliseconds 500
        }
        if (-not $ready) { throw 'A interface não ficou pronta no prazo. Confira os logs privados.' }
    } catch {
        & (Join-Path $PSScriptRoot 'encerrar-piloto-local.ps1')
        throw
    }
} finally {
    $env:DJANGO_SETTINGS_MODULE = $previousSettings
    $env:NOTARIUS_PILOTO_DB = $previousDatabase
    $env:NEXT_PUBLIC_API_URL = $previousApi
    $env:NEXT_TELEMETRY_DISABLED = $previousTelemetry
    $env:NEXT_PUBLIC_PILOTO_LOCAL = $previousPilot
}
Write-Host 'Piloto local pronto: http://localhost:3002/atendimentos'
Write-Host 'Use sua conta existente e confira o cartório. Acesso somente neste computador.'
