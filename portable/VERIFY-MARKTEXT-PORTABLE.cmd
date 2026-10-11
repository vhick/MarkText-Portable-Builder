@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0VERIFY-MARKTEXT-PORTABLE.ps1"
echo.
pause
