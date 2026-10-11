@echo off
setlocal EnableExtensions
set "HERE=%~dp0"
if not exist "%HERE%marktext.exe" (
  echo ERROR: marktext.exe is missing beside this launcher.
  pause
  exit /b 1
)
if not exist "%HERE%marktext-user-data" mkdir "%HERE%marktext-user-data"
start "" /D "%HERE%" "%HERE%marktext.exe" %*
exit /b 0
