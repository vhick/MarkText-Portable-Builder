param(
    [Parameter(Mandatory=$true)][string]$SourceRoot,
    [Parameter(Mandatory=$true)][string]$BuilderRoot,
    [Parameter(Mandatory=$true)][string]$OutputRoot
)
$ErrorActionPreference = 'Stop'
$SourceRoot=[IO.Path]::GetFullPath($SourceRoot)
$BuilderRoot=[IO.Path]::GetFullPath($BuilderRoot)
$OutputRoot=[IO.Path]::GetFullPath($OutputRoot)
$dist=Join-Path $SourceRoot 'dist'
if (-not (Test-Path -LiteralPath $dist -PathType Container)) {
    throw "MarkText build output directory missing: $dist"
}
$zips = @(Get-ChildItem -LiteralPath $dist -File -Filter 'marktext-win-x64-*.zip')
if ($zips.Count -ne 1) {
    throw "Expected ONE upstream portable ZIP in $dist; found $($zips.Count)."
}
$work=Join-Path $env:RUNNER_TEMP 'MarkTextPortableAssembly'
if (Test-Path -LiteralPath $work) { Remove-Item -LiteralPath $work -Recurse -Force }
New-Item -ItemType Directory -Path $work -Force | Out-Null
Expand-Archive -LiteralPath $zips[0].FullName -DestinationPath $work -Force
$exes=@(Get-ChildItem -LiteralPath $work -Recurse -File -Filter 'marktext.exe')
if ($exes.Count -ne 1) {
    throw "Expected one marktext.exe in upstream ZIP; found $($exes.Count)."
}
$appDir=$exes[0].DirectoryName
New-Item -ItemType Directory -Path (Join-Path $appDir 'marktext-user-data') -Force | Out-Null
foreach($name in @('LAUNCH-MARKTEXT-PORTABLE.cmd','VERIFY-MARKTEXT-PORTABLE.cmd','VERIFY-MARKTEXT-PORTABLE.ps1','TEST-CRASHPAD-ISOLATION.cmd','TEST-CRASHPAD-ISOLATION.ps1')) {
    Copy-Item -LiteralPath (Join-Path $BuilderRoot "portable\$name") -Destination (Join-Path $appDir $name) -Force
}
@'
MarkText Crashpad Isolation v1.2 - EXPERIMENTAL Windows x64
=====================================

1. Extract the entire ZIP into a permanent directory.
2. Keep the marktext-user-data directory BESIDE marktext.exe.
3. Run marktext.exe directly or LAUNCH-MARKTEXT-PORTABLE.cmd.
4. Run VERIFY-MARKTEXT-PORTABLE.cmd after testing preferences and reopening the app.
5. The v1.1 patch redirects Electron storage. The v1.2 test also disables MarkText crashReporter.start().
6. Do not delete your original installation/profile until the Windows runtime test passes.
7. TEST BUILD ONLY: native crash-report collection is disabled. Not an official or production release.

IMPORTANT: RUN TEST-CRASHPAD-ISOLATION.cmd and report the results.

Upstream may still read or write some external state (recent documents,
file associations, native keychain, etc.). Do not promise zero Windows traces.
'@ | Set-Content -LiteralPath (Join-Path $appDir 'READ-ME-PORTABLE.txt') -Encoding UTF8
@'
EXPERIMENTAL V1.2 CRASHPAD ISOLATION
===================================
This is a DIAGNOSTIC TEST build only.
The explicit MarkText crashReporter.start() call is disabled.
Native crash minidumps are not collected by this call.
Other native processes may still initialize Crashpad independently.
Keep your existing working MarkText build as your backup.
Use TEST-CRASHPAD-ISOLATION.cmd to check a clean AppData path.
'@ | Set-Content -LiteralPath (Join-Path $appDir 'THIS-IS-A-TEST-BUILD.txt') -Encoding UTF8
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$revision=(git -C $SourceRoot rev-parse --short=12 HEAD).Trim()
$final=Join-Path $OutputRoot "MarkText-Crashpad-Isolation-TEST-Windows-x64-$revision.zip"
Compress-Archive -Path (Join-Path $work '*') -DestinationPath $final -CompressionLevel Optimal -Force
Write-Host "Portable ZIP assembled: $final" -ForegroundColor Green
