$ErrorActionPreference = 'Continue'
$root=$PSScriptRoot
$profile=Join-Path $root 'marktext-user-data'
$reportDir=Join-Path $root 'Verification'
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
$report=Join-Path $reportDir ('MarkText-Verify-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.txt')
$hostData=Join-Path $env:APPDATA 'marktext'
$hostLocal=Join-Path $env:LOCALAPPDATA 'marktext'
$runtime=Join-Path $profile 'portable-paths.txt'
$lines=[System.Collections.Generic.List[string]]::new()
$lines.Add('MarkText v1.1 portable diagnostic')
$lines.Add('Verification time: '+(Get-Date))
$lines.Add('Portable exe: '+(Join-Path $root 'marktext.exe'))
$lines.Add('Portable profile: '+$profile)
$lines.Add('')
$lines.Add('=== ACTUAL ELECTRON RUNTIME PATHS ===')
if (Test-Path -LiteralPath $runtime -PathType Leaf) {
    $lines.Add('Runtime path report exists: YES')
    Get-Content -LiteralPath $runtime | ForEach-Object { $lines.Add('  '+$_) }
}
else {
    $lines.Add('Runtime path report exists: NO')
    $lines.Add('If you have launched the new v1.1 EXE, check if a different MarkText instance is still running.')
}
$lines.Add('')
$lines.Add('=== PORTABLE DIRECTORY STATE ===')
foreach($item in @('preferences.json','Crashpad','logs','portable-paths.txt')) {
    $p=Join-Path $profile $item
    if (Test-Path -LiteralPath $p) {
        $fi=Get-Item -LiteralPath $p
        $lines.Add(('PRESENT: {0}; lastModified={1}' -f $p,$fi.LastWriteTime.ToString('s')))
    } else {
        $lines.Add('ABSENT: '+$p)
    }
}
$lines.Add('')
$lines.Add('=== WINDOWS HOST RESIDUE ===')
foreach($p in @($hostData,$hostLocal)) {
    $lines.Add('Host path: '+$p+' exists='+[string](Test-Path -LiteralPath $p))
    if(Test-Path -LiteralPath $p) {
        Get-ChildItem -LiteralPath $p -Force -ErrorAction SilentlyContinue | Select-Object -First 30 | ForEach-Object {
            $lines.Add(('  {0}: lastModified={1}' -f $_.Name,$_.LastWriteTime.ToString('s')))
        }
    }
}
$lines.Add('')
$lines.Add('=== INTERPRETATION ===')
$lines.Add('The runtime path report shows the values Electron is actually using. File existence alone does not prove a new write.')
$lines.Add('For a clean test, close all MarkText processes, rename old host AppData\marktext to marktext-backup, and launch ONLY the new portable build.')
$lines.Add('After launch, check whether a fresh host AppData\marktext directory appears. Do not delete backups yet.')
$lines | Set-Content -LiteralPath $report -Encoding UTF8
Get-Content -LiteralPath $report | Write-Host
Write-Host ''
Write-Host ('Saved diagnostic report: '+$report)
