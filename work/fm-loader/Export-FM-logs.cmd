@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0Export-FM-logs.ps1" %*
pause
