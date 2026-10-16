$projectRoot = Split-Path -Parent $PSScriptRoot
& (Join-Path $projectRoot '.venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'manage.py') test
exit $LASTEXITCODE
