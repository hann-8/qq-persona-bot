@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo 请先关闭本项目bot。本工具只核验并备份归档清理阻断记录，不结束任何进程。
"%~dp0.venv\Scripts\python.exe" -X utf8 "%~dp0scripts\manage.py" cleanup recover %*
set "bot_cleanup_exit=%errorlevel%"
if %bot_cleanup_exit% neq 0 (
  echo 恢复未完成，请保留上方原因。不要删除uv.lock或手工删除清理台账。
) else (
  echo 清理状态已就绪。请使用“启动机器人.cmd”手动启动。
)
if /i "%~1"=="--no-pause" exit /b %bot_cleanup_exit%
pause
exit /b %bot_cleanup_exit%
