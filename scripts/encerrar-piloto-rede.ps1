$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot 'servir-piloto-rede.mjs'
$listeners = @(Get-NetTCPConnection -LocalPort 3443,3080 -State Listen -ErrorAction SilentlyContinue)
foreach ($processId in @($listeners.OwningProcess | Select-Object -Unique)) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$processId"
    if ($process.CommandLine -and $process.CommandLine.Contains($script)) {
        Stop-Process -Id $processId
    }
}
