$ErrorActionPreference = 'Stop'
$folder = Join-Path (Split-Path -Parent $PSScriptRoot) '.local/ia-minuta'
$exe = Join-Path $folder 'runtime/llama-server.exe'
$model = Join-Path $folder 'qwen3-4b-instruct.gguf'
if (-not (Test-Path -LiteralPath $exe) -or -not (Test-Path -LiteralPath $model)) {
    throw 'O motor e os pesos da IA local precisam estar na pasta .local/ia-minuta.'
}
$listener = Get-NetTCPConnection -State Listen -LocalPort 18082 -ErrorAction SilentlyContinue
if ($listener) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
    if ($listener.LocalAddress -ne '127.0.0.1' -or $process.ExecutablePath -ne $exe) {
        throw 'A porta da IA local está em uso por outro serviço.'
    }
} else {
    $arguments = @('--model', ('"' + $model + '"'), '--alias', 'qwen3-4b-instruct',
        '--host', '127.0.0.1', '--port', '18082', '--ctx-size', '8192', '--parallel', '1',
        '--n-gpu-layers', 'auto', '--no-webui', '--no-slots', '--no-cache-prompt', '--offline', '--log-disable')
    $process = Start-Process -FilePath $exe -ArgumentList $arguments -WorkingDirectory $folder `
        -WindowStyle Hidden -RedirectStandardOutput (Join-Path $folder 'server-out.log') `
        -RedirectStandardError (Join-Path $folder 'server-error.log') -PassThru
}
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    if ($process.HasExited) { throw 'A IA local encerrou durante a inicialização. Confira server-error.log.' }
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:18082/health' -TimeoutSec 1
        if ($health.status -eq 'ok') { return }
    } catch { }
    Start-Sleep -Milliseconds 400
}
throw 'A IA local ainda não respondeu. Confira server-error.log.'
