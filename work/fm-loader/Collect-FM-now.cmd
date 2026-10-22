@echo off
powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0Collect-FM-now.ps1" %*
if errorlevel 1 (
  echo COLLECT_FAILED
  pause
  exit /b 1
)
pause
