param([Parameter(Mandatory=$true)][string]$Arquivo,
      [Parameter(Mandatory=$true)][string]$Destino)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
& (Join-Path $projectRoot '.venv/Scripts/python.exe') (Join-Path $projectRoot 'apps/notarius-api/manage.py') conferir_backup_local --settings=config.settings_piloto --arquivo $Arquivo --recuperar-em $Destino
if ($LASTEXITCODE -ne 0) { throw 'Restauração recusada. O banco em uso foi preservado.' }
Write-Host 'Cópia recuperada, sem trocar o banco em uso. Para utilizá-la, encerre o sistema e inicie com -Banco apontando para esta cópia.'
