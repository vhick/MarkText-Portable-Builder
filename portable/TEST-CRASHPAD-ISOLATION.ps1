$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$exe = Join-Path $root 'marktext.exe'
$profile = Join-Path $root 'marktext-user-data'
$host = Join-Path $env:APPDATA 'marktext'
$reportDir = Join-Path $root 'Verification'
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
$report = Join-Path $reportDir ('Crashpad-Isolation-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.txt')
$lines = [System.Collections.Generic.List[string]]::new()

function Add([string]$msg) {
    Write-Host $msg
    $lines.Add($msg)
}

function Snapshot([string]$when) {
    Add ("=== " + $when + " ===")
    Add ("Host AppData folder exists: " + (Test-Path -LiteralPath $host))
    Add ("Host Crashpad exists: " + (Test-Path -LiteralPath (Join-Path $host 'Crashpad')))
    if (Test-Path -LiteralPath $host -PathType Container) {
        Get-ChildItem -LiteralPath $host -Force -ErrorAction SilentlyContinue |
            Select-Object -First 25 |
            ForEach-Object { Add (("  {0} lastWrite={1}" -f $_.Name,$_.LastWriteTime.ToString('o'))) }
    }
    $pathReport = Join-Path $profile 'portable-paths.txt'
    Add ("Portable path report exists: " + (Test-Path -LiteralPath $pathReport -PathType Leaf))
    if (Test-Path -LiteralPath $pathReport -PathType Leaf) {
        Get-Content -LiteralPath $pathReport | ForEach-Object { Add ('  ' + $_) }
    }
}

Add 'MarkText v1.2 Crashpad-isolation runtime test (EXPERIMENTAL)'
Add ('Started at: ' + (Get-Date -Format 'o'))
Add ('Executable: ' + $exe)
Add ('Host directory: ' + $host)
Add ''

if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
    Add 'ERROR: marktext.exe does not exist next to this test script.'
    $lines | Set-Content -LiteralPath $report -Encoding UTF8
    exit 1
}
if (Get-Process -Name marktext -ErrorAction SilentlyContinue) {
    Add 'ERROR: Close ALL marktext.exe processes in Task Manager, then run this test again.'
    $lines | Set-Content -LiteralPath $report -Encoding UTF8
    exit 1
}

if (Test-Path -LiteralPath $host) {
    Add 'Cannot perform a clean creation test because the original host folder still exists.'
    Add 'In File Explorer, rename %APPDATA%\marktext to marktext-before-isolation-test.'
    Add 'Keep that backup; this script will NOT rename or delete anything.'
    $lines | Set-Content -LiteralPath $report -Encoding UTF8
    exit 2
}

Snapshot 'Before launch'
Add ''
Add 'Launching this experimental executable. Wait for the MarkText editor to open.'
Start-Process -FilePath $exe -WorkingDirectory $root
Read-Host 'Once MarkText is fully open, press Enter to record the first check' | Out-Null
Snapshot 'While MarkText is running'
Add ''
Read-Host 'Now close MarkText normally, wait a moment, then press Enter' | Out-Null
Snapshot 'After MarkText exits'
Add ''

if (Test-Path -LiteralPath $host) {
    Add 'RESULT: HOST APPDATA RECREATED. Disabling the explicit reporter was NOT sufficient.'
} else {
    Add 'RESULT: No host AppData marktext folder detected during this observed launch.'
    Add 'This points toward the removed reporter call but does not prove all future launches are trace-free.'
}
Add 'This experimental build does not collect native crash minidumps through MarkText crashReporter.start().'
Add ('Saved report: ' + $report)
$lines | Set-Content -LiteralPath $report -Encoding UTF8
