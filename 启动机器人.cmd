@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
"%~dp0.venv\Scripts\python.exe" "%~dp0scripts\manage.py" start-desktop %*
set "bot_manage_exit=%errorlevel%"
if /i "%~1"=="--no-pause" exit /b %bot_manage_exit%
pause
exit /b %bot_manage_exit%
