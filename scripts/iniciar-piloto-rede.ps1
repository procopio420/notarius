param([string]$Interface = 'Wi-Fi')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv/Scripts/python.exe'
$node = (Get-Command node -ErrorAction Stop).Source
$config = Get-NetIPConfiguration -InterfaceAlias $Interface
$ip = $config.IPv4Address | Where-Object { $_.IPAddress -match '^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)' } | Select-Object -First 1
if (-not $ip) { throw 'A interface escolhida não tem um endereço IPv4 privado.' }
if ((Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8002/health/ -TimeoutSec 5).StatusCode -ne 200) {
    throw 'Inicie o piloto local antes de abrir o acesso pela rede.'
}
if ((Invoke-WebRequest -UseBasicParsing http://127.0.0.1:3002/login -TimeoutSec 15).StatusCode -ne 200) {
    throw 'A interface local não está pronta.'
}
if (@(Get-NetTCPConnection -LocalPort 3443,3080 -State Listen -ErrorAction SilentlyContinue).Count) {
    throw 'As portas 3443 ou 3080 já estão em uso.'
}

$address = $ip.IPAddress
$folder = Join-Path $root ".local/piloto-rede/$address"
& $python (Join-Path $PSScriptRoot 'preparar-certificado-piloto.py') $address
if ($LASTEXITCODE -ne 0) { throw 'Falha ao preparar o certificado local.' }
$script = Join-Path $PSScriptRoot 'servir-piloto-rede.mjs'
$server = Start-Process -FilePath $node -ArgumentList @('"' + $script + '"', $address, $ip.PrefixLength, '"' + $folder + '"') -WorkingDirectory $root -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $folder 'rede.log') -RedirectStandardError (Join-Path $folder 'rede-erros.log')
try {
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        if ($server.HasExited) { throw 'O servidor de rede encerrou. Confira rede-erros.log.' }
        if (Get-NetTCPConnection -LocalAddress $address -LocalPort 3443 -State Listen -ErrorAction SilentlyContinue) { break }
        Start-Sleep -Milliseconds 250
    }
    & $python -c 'import ssl, sys, urllib.request; ctx = ssl.create_default_context(cafile=sys.argv[2]); assert urllib.request.urlopen(sys.argv[1], context=ctx, timeout=30).status == 200' "https://${address}:3443/login" (Join-Path $folder 'autoridade.pem')
    if ($LASTEXITCODE -ne 0) { throw 'O acesso HTTPS pela rede não passou na verificação local.' }
} catch {
    Stop-Process -Id $server.Id -ErrorAction SilentlyContinue
    throw
}
Write-Host "Instalar o certificado no iPhone: http://${address}:3080/notarius.mobileconfig"
Write-Host "Abrir o Notarius no iPhone: https://${address}:3443/login"
