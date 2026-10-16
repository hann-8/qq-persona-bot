$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
& (Join-Path $projectRoot '.venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'manage.py') stop
if ($LASTEXITCODE -ne 0) { throw 'Project process cleanup failed.' }
