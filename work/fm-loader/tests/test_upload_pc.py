"""Execute the actual PowerShell upload queue; replace only external HTTP."""
import pathlib,subprocess,tempfile

SOURCE=pathlib.Path(__file__).resolve().parents[1]/'Upload-FM-report.ps1'
assert SOURCE.is_file(),'PC upload queue is not implemented'
SCRIPT=r'''
param([string]$Source,[string]$Root)
$ErrorActionPreference='Stop'
. $Source
function Assert($Value,$Message){if(-not $Value){throw $Message}}
$stream=New-Object IO.MemoryStream(,[Text.Encoding]::UTF8.GetBytes('{"ok":true,"id":"fixture"}'))
$parsed=Read-FmUploadReceipt $stream
Assert ($parsed.ok -eq $true -and $parsed.id -eq 'fixture') 'Actual HTTP receipt reader failed'
$stream=New-Object IO.MemoryStream(,[Text.Encoding]::UTF8.GetBytes(('a'*8193)))
$rejected=$false;try {$null=Read-FmUploadReceipt $stream}catch {$rejected=$true}
Assert $rejected 'Oversized HTTP acknowledgement was accepted'
$config=Join-Path $Root 'private.json'
$token='a'*48
@{endpoint='https://example.com/voyah-fm/v1';client='tester-one';token=$token}|ConvertTo-Json|Set-Content -LiteralPath $config -Encoding UTF8
$report=Join-Path $Root 'Voyah-FM-PC-report-20261022-220000.zip'
[IO.File]::WriteAllBytes($report,[byte[]](1,2,3,4,5))
$queue=Join-Path $Root 'queue'
$script:mode='offline';$script:calls=0;$script:stored=@{}
function Invoke-FmUploadRequest($Configuration,$File,$Hash,$Name){
 $script:calls++
 if($script:mode -eq 'offline'){throw 'Network unavailable; secret must not appear'}
 if($script:mode -eq 'lost'){$script:stored[$Hash]=$true;throw 'Response lost'}
 if($script:mode -eq 'bad-receipt'){return @{ok=$true;sha256=('0'*64);id='wrong';bytes=5}}
 $script:stored[$Hash]=$true
 return @{ok=$true;sha256=$Hash;id=($Configuration.client+'/'+$Hash);bytes=(Get-Item -LiteralPath $File).Length}
}
$r=Send-FmReports -ReportPath $report -ConfigurationPath $config -QueueRoot $queue
Assert ($r.Status -eq 'QUEUED' -and $r.Pending -eq 1) 'Offline report was not queued'
Assert (Test-Path -LiteralPath $report) 'Original ZIP was removed'
Assert ($r.Error -notmatch 'secret') 'Transport exception details leaked'
$script:mode='bad-receipt'
$r=Send-FmReports -ReportPath $report -ConfigurationPath $config -QueueRoot $queue
Assert ($r.Pending -eq 1 -and $r.Status -eq 'QUEUED') 'Invalid acknowledgement deleted a queued report'
$script:mode='lost'
$r=Send-FmReports -ReportPath $report -ConfigurationPath $config -QueueRoot $queue
Assert ($r.Pending -eq 1) 'Lost reply must stay pending'
$script:mode='online'
$r=Send-FmReports -ReportPath $report -ConfigurationPath $config -QueueRoot $queue
Assert ($r.Status -eq 'SENT' -and $r.Pending -eq 0 -and $script:stored.Count -eq 1) 'Retry did not drain queue idempotently'
Assert (@(Get-ChildItem -LiteralPath $queue -Recurse -Filter '*.receipt.json').Count -eq 1) 'Receipt missing'
Assert (Test-Path -LiteralPath $report) 'Successful upload removed local original'
$before=$script:calls
@{endpoint='http://example.com/voyah-fm/v1';client='tester-one';token=$token}|ConvertTo-Json|Set-Content -LiteralPath $config -Encoding UTF8
$r=Send-FmReports -ReportPath $report -ConfigurationPath $config -QueueRoot $queue
Assert ($r.Status -eq 'CONFIG_ERROR' -and $script:calls -eq $before) 'Insecure endpoint was used'
$r=Send-FmReports -ReportPath $report -ConfigurationPath (Join-Path $Root 'missing.json') -QueueRoot $queue
Assert ($r.Status -eq 'NOT_CONFIGURED') 'Optional config changed offline collection'
@{endpoint='https://example.com/voyah-fm/v1';client='tester-one';token=$token}|ConvertTo-Json|Set-Content -LiteralPath $config -Encoding UTF8
$full=Join-Path $Root 'full';$script:mode='offline'
for($n=0;$n -lt 32;$n++){
 [IO.File]::WriteAllBytes($report,[byte[]](10,$n,20))
 $r=Send-FmReports -ReportPath $report -ConfigurationPath $config -QueueRoot $full
 Assert ($r.Status -eq 'QUEUED') 'Failed to fill synthetic offline queue'
}
[IO.File]::WriteAllBytes($report,[byte[]](99,98,97));$script:mode='online';$before=$script:calls
$r=Send-FmReports -ReportPath $report -ConfigurationPath $config -QueueRoot $full
Assert ($script:calls -gt $before -and $r.Pending -lt 32) 'A full queue never retries after reconnect'
Assert (Test-Path -LiteralPath $report) 'Full-queue recovery removed original'
Write-Output 'PASS PowerShell upload queue: offline, invalid receipt, lost acknowledgement, idempotent retry, HTTPS config, local ZIP preservation, full-queue recovery'
'''
with tempfile.TemporaryDirectory(prefix='fm-upload-pc-') as td:
    t=pathlib.Path(td);script=t/'test.ps1';script.write_bytes(b'\xef\xbb\xbf'+SCRIPT.encode('utf8'))
    r=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),'-Source',str(SOURCE),'-Root',str(t)],capture_output=True,timeout=30)
    print((r.stdout+r.stderr).decode('utf8','replace'))
    assert r.returncode==0,'Actual PC upload queue failed'
