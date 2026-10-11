$ErrorActionPreference = 'Continue'
$root=$PSScriptRoot
$profile=Join-Path $root 'marktext-user-data'
$reportDir=Join-Path $root 'Verification'
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
$report=Join-Path $reportDir ('MarkText-Verify-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.txt')
$hostData=Join-Path $env:APPDATA 'marktext'
$hostLocal=Join-Path $env:LOCALAPPDATA 'marktext'

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('MarkText portable runtime verification — diagnostic only')
$lines.Add('Timestamp: '+(Get-Date))
$lines.Add('Executable: '+(Join-Path $root 'marktext.exe'))
$lines.Add('Portable profile: '+$profile)
$lines.Add('EXE exists: '+(Test-Path (Join-Path $root 'marktext.exe')))
$lines.Add('Portable user-data exists: '+(Test-Path $profile))
$lines.Add('Portable Crashpad exists: '+(Test-Path (Join-Path $profile 'Crashpad')))
$lines.Add('Portable logs exists: '+(Test-Path (Join-Path $profile 'logs')))
$lines.Add('')
$lines.Add('Host profile residue:')
foreach($p in @($hostData,$hostLocal)) {
    $lines.Add('  '+$p+' exists='+[string](Test-Path $p))
    if(Test-Path $p) {
        Get-ChildItem -LiteralPath $p -Force -ErrorAction SilentlyContinue |
            Select-Object -First 25 |
            ForEach-Object { $lines.Add('    '+$_.Name+' lastModified='+$_.LastWriteTime.ToString('s')) }
    }
}
$lines.Add('')
$lines.Add('INTERPRETATION: Existing AppData folders may be OLD leftovers. To establish a new write,')
$lines.Add('close MarkText, rename the old AppData marktext folder, relaunch and check again.')
$lines.Add('The program must be tested on Windows; this report is not proof of zero system traces.')
$lines | Set-Content -LiteralPath $report -Encoding UTF8
Write-Host "Saved verification report: $report"
Get-Content -LiteralPath $report | Write-Host
