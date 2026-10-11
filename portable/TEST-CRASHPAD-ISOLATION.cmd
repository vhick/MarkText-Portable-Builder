@echo off
setlocal EnableExtensions
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0TEST-CRASHPAD-ISOLATION.ps1"
echo.
echo Test complete. You can now upload the report from the Verification folder.
pause
