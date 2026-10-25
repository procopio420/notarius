$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$targets = @()
foreach ($port in @(3002, 8002)) {
    foreach ($listener in @(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue)) {
        $owner = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
        if (-not $owner.CommandLine -or $owner.CommandLine.Replace('/', '\').IndexOf($projectRoot, [StringComparison]::OrdinalIgnoreCase) -lt 0) {
            throw "A porta $port pertence a outro processo; nenhum serviço será encerrado."
        }
        $targets += $owner.ProcessId
    }
}
# Validate every owner before stopping any service. Never delete data or lock files.
foreach ($processId in @($targets | Select-Object -Unique)) {
    Stop-Process -Id $processId -ErrorAction SilentlyContinue
}
Write-Host 'Serviços locais encerrados. Banco, anexos e backups foram preservados.'
Write-Host 'Feche a aba do navegador para não continuar usando uma tela antiga.'
