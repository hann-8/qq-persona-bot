param([switch]$ChannelOnly)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$startMode = if ($ChannelOnly) { 'start-channel' } else { 'start-text' }
& (Join-Path $projectRoot '.venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'manage.py') $startMode
if ($LASTEXITCODE -ne 0) { throw 'Channel startup failed; inspect local logs.' }
