@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
"%~dp0.venv\Scripts\python.exe" "%~dp0scripts\configure_bot.py" %*
set "bot_config_exit=%errorlevel%"
if not "%~1"=="" exit /b %bot_config_exit%
pause
exit /b %bot_config_exit%
