$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$apiFolder = Join-Path $projectRoot 'apps/notarius-api'
$webFolder = Join-Path $projectRoot 'apps/notarius-web'
$pythonPath = Join-Path $projectRoot '.venv/Scripts/python.exe'
$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
$nodePath = if ($nodeCommand) { $nodeCommand.Source } else { Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' }
$logFolder = Join-Path $projectRoot '.local/logs'
if (-not (Test-Path -LiteralPath $pythonPath) -or -not (Test-Path -LiteralPath $nodePath)) {
    throw 'O ambiente Python/Node deste projeto não está preparado. Solicite a configuração antes de iniciar o teste.'
}
if (-not (Test-Path -LiteralPath (Join-Path $webFolder 'node_modules/next/dist/bin/next'))) {
    throw 'As dependências da interface não estão instaladas.'
}
New-Item -ItemType Directory -Force -Path $logFolder | Out-Null
function Test-ProjectPort([int]$port) {
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue)
    foreach ($listener in $listeners) {
        $owner = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
        if (-not $owner.CommandLine -or $owner.CommandLine.Replace('/', '\').IndexOf($projectRoot, [StringComparison]::OrdinalIgnoreCase) -lt 0) {
            throw "A porta $port está ocupada por outro processo. Não vou encerrar nenhum programa automaticamente."
        }
    }
    return $listeners.Count -gt 0
}
# Validate both ports before starting either service.
$apiRunning = Test-ProjectPort 8002
$webRunning = Test-ProjectPort 3002
if (-not $apiRunning) {
    & $pythonPath (Join-Path $apiFolder 'manage.py') migrate --noinput
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao preparar o banco; nenhum servidor foi iniciado.' }
    $manageArgument = '"' + (Join-Path $apiFolder 'manage.py') + '"'
    Start-Process -FilePath $pythonPath -ArgumentList @($manageArgument, 'runserver', '127.0.0.1:8002', '--noreload') -WorkingDirectory $apiFolder -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logFolder 'api-out.log') -RedirectStandardError (Join-Path $logFolder 'api-error.log') | Out-Null
}
if (-not $webRunning) {
    Start-Process -FilePath $nodePath -ArgumentList @('node_modules/next/dist/bin/next', 'dev', '--turbopack', '--port', '3002', '--hostname', '127.0.0.1') -WorkingDirectory $webFolder -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logFolder 'web-out.log') -RedirectStandardError (Join-Path $logFolder 'web-error.log') | Out-Null
}
Write-Host 'Teste local iniciado ou já em execução. Abra http://localhost:3002/atendimentos'
Write-Host 'Este acesso funciona neste computador. Use somente dados fictícios.'
