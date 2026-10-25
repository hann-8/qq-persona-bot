param([switch]$ChannelOnly)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$startArgs = @('start-desktop')
if ($ChannelOnly) { $startArgs += '--channel-only' }
& (Join-Path $projectRoot '.venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'manage.py') @startArgs
if ($LASTEXITCODE -ne 0) { throw 'Channel startup failed; inspect local logs.' }
