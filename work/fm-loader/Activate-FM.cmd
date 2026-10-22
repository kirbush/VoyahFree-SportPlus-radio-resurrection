@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0Activate-FM.ps1" %*
pause
