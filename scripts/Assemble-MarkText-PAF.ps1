param(
    [Parameter(Mandatory=$true)][string]$SourceRoot,
    [Parameter(Mandatory=$true)][string]$BuilderRoot,
    [Parameter(Mandatory=$true)][string]$OutputRoot
)
$ErrorActionPreference = 'Stop'

$SourceRoot = [IO.Path]::GetFullPath($SourceRoot)
$BuilderRoot = [IO.Path]::GetFullPath($BuilderRoot)
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
$dist = Join-Path $SourceRoot 'dist'
if (-not (Test-Path -LiteralPath $dist -PathType Container)) {
    throw "Upstream dist directory not found: $dist"
}

$archives = @(Get-ChildItem -LiteralPath $dist -File -Filter 'marktext-win-x64-*.zip')
if ($archives.Count -ne 1) {
    throw "Expected ONE upstream Windows x64 app ZIP; found $($archives.Count)."
}

$work = Join-Path $env:RUNNER_TEMP 'MarkTextPAFAppAssembly'
if (Test-Path -LiteralPath $work) {
    Remove-Item -LiteralPath $work -Recurse -Force
}
New-Item -ItemType Directory -Path $work -Force | Out-Null
$extracted = Join-Path $work 'Extracted'
New-Item -ItemType Directory -Path $extracted -Force | Out-Null
Expand-Archive -LiteralPath $archives[0].FullName -DestinationPath $extracted -Force

$executables = @(Get-ChildItem -LiteralPath $extracted -File -Recurse -Filter 'marktext.exe')
if ($executables.Count -ne 1) {
    throw "Expected ONE marktext.exe in upstream ZIP; found $($executables.Count)."
}
$originalAppDir = $executables[0].DirectoryName

# CRITICAL: Do NOT create an adjacent App\MarkText\marktext-user-data marker.
# That folder belongs only in the top-level PortableApps Data directory.
if (Test-Path -LiteralPath (Join-Path $originalAppDir 'marktext-user-data')) {
    throw 'Upstream archive contains marktext-user-data beside the EXE. Refusing to package a replaceable settings folder.'
}

$staging = Join-Path $work 'Package'
$appBinary = Join-Path $staging 'App-Binary'
New-Item -ItemType Directory -Path $appBinary -Force | Out-Null
Get-ChildItem -LiteralPath $originalAppDir -Force |
    Copy-Item -Destination $appBinary -Recurse -Force

if (-not (Test-Path -LiteralPath (Join-Path $appBinary 'marktext.exe') -PathType Leaf)) {
    throw 'Failed to copy marktext.exe into App-Binary.'
}
if (Test-Path -LiteralPath (Join-Path $appBinary 'marktext-user-data')) {
    throw 'An adjacent profile appeared during packaging. Refusing unsafe artifact.'
}

# Keep release metadata outside App-Binary so users can copy only application files.
$revision = (git -C $SourceRoot rev-parse HEAD).Trim()
@"
MarkText PAF-COMPATIBLE BINARY
============================
Source commit: $revision

NOT a finished .paf.exe installer.

Copy the CONTENTS of App-Binary into:
  MarkTextPortable\App\MarkText\

The PortableApps launcher MUST set:
  ProgramExecutable=MarkText\marktext.exe
  CommandLineArguments='--user-data-dir "%PAL:DataDir%\marktext-user-data"'

The data folder MUST be:
  MarkTextPortable\Data\marktext-user-data\

Do NOT put a marktext-user-data folder beside App\MarkText\marktext.exe.
Do NOT launch App\MarkText\marktext.exe directly; use MarkTextPortable.exe.
Native MarkText Crashpad reporter starts are intentionally disabled.
This is a locally-built modified edition, not an official MarkText release.
"@ | Set-Content -LiteralPath (Join-Path $staging 'HOW-TO-INSTALL-IN-PAF.txt') -Encoding UTF8

[ordered]@{
    build_type = 'MarkText PortableApps compatible binary';
    upstream_commit = $revision;
    launcher_required = 'MarkTextPortable.exe';
    launcher_profile_argument = '--user-data-dir "%PAL:DataDir%\marktext-user-data"';
    app_binary_destination = 'MarkTextPortable/App/MarkText';
    user_data_destination = 'MarkTextPortable/Data/marktext-user-data';
    explicit_crash_reporting = 'disabled';
    replaces_existing_standalone_build = $false;
    tested_in_windows_runtime = $false;
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $staging 'PAF-BUILD-METADATA.json') -Encoding UTF8

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$shortSha = $revision.Substring(0, [Math]::Min(12, $revision.Length))
$target = Join-Path $OutputRoot "MarkText-PAF-Binary-Windows-x64-$shortSha.zip"
Compress-Archive -Path (Join-Path $staging '*') -DestinationPath $target -CompressionLevel Optimal -Force
Write-Host "PAF-compatible binary ZIP assembled: $target" -ForegroundColor Green
