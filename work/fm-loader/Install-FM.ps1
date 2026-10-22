param([string]$Adb='', [string]$Serial='', [string]$Apk=(Join-Path $PSScriptRoot 'Voyah-FM-Radio-0.5.0-beta.apk'), [string]$UploadConfig=(Join-Path $PSScriptRoot 'upload.json'))
$ErrorActionPreference='Stop'
$stage=$null; $archive=$null; $remote=$null; $remoteFiles=@(); $privateConfiguration=$null; $script:UseSu=$false
function Quote-Arg([string]$Value){return '"'+[regex]::Replace([regex]::Replace($Value,'(\\*)"','$1$1\"'),'(\\+)$','$1$1')+'"'}
function Adb-Call([string[]]$TaskArgs,[int]$Timeout=45000){
    $info=New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName=$script:AdbExe
    $info.Arguments=(($TaskArgs|ForEach-Object {Quote-Arg $_}) -join ' ')
    $info.UseShellExecute=$false; $info.CreateNoWindow=$true
    $info.RedirectStandardOutput=$true; $info.RedirectStandardError=$true
    $info.StandardOutputEncoding=[System.Text.Encoding]::UTF8; $info.StandardErrorEncoding=[System.Text.Encoding]::UTF8
    $proc=New-Object System.Diagnostics.Process; $proc.StartInfo=$info
    try {
        [void]$proc.Start()
        $out=$proc.StandardOutput.ReadToEndAsync(); $err=$proc.StandardError.ReadToEndAsync()
        if(-not $proc.WaitForExit($Timeout)){$proc.Kill();throw ('ADB timeout: '+($TaskArgs -join ' '))}
        return [pscustomobject]@{Code=$proc.ExitCode;Text=$out.Result;Error=$err.Result}
    } finally {$proc.Dispose()}
}
function Require-Adb([string[]]$TaskArgs,[int]$Timeout=45000){
    $result=Adb-Call $TaskArgs $Timeout
    if($result.Text.Trim()){Write-Host $result.Text.Trim()}; if($result.Error.Trim()){Write-Host $result.Error.Trim()}
    if($result.Code -ne 0){throw ('ADB failed ('+$result.Code+'): '+($TaskArgs -join ' '))}
}
function Root-Run([string[]]$Command,[int]$Timeout=45000){
    $prefix=@('-s',$script:Serial,'shell'); if($script:UseSu){$prefix+=@('su','0')}
    Require-Adb ($prefix+$Command) $Timeout
}
function Root-Call([string[]]$Command,[int]$Timeout=45000){
    $prefix=@('-s',$script:Serial,'shell'); if($script:UseSu){$prefix+=@('su','0')}
    return Adb-Call ($prefix+$Command) $Timeout
}
function Test-LegacyDiagnostics {
    $result=Root-Call @('pm','path','ru.local.voyah.fmdiagnostics')
    if($result.Code -eq 0 -and $result.Text -match '(?m)^package:'){return $true}
    $message=($result.Text+$result.Error).Trim()
    if($result.Code -in @(0,1) -and (-not $message -or $message -match '^Error: package ru\.local\.voyah\.fmdiagnostics was not found\.?$')){return $false}
    throw 'LEGACY_DIAGNOSTICS_QUERY_FAILED: cannot verify whether the old diagnostics app remains; retry installation.'
}
try {
    Write-Host 'Voyah FM 0.5.0 beta: one FM Radio app. Files stay in /data.'
    # Parse privately: JSON parser exceptions may contain values, including the token.
    if(Test-Path -LiteralPath $UploadConfig -PathType Leaf){
        try {
            if((Get-Item -LiteralPath $UploadConfig).Length -gt 16384){throw 'Invalid'}
            $configuration=ConvertFrom-Json -InputObject ([IO.File]::ReadAllText((Resolve-Path -LiteralPath $UploadConfig).Path))
            if($configuration.endpoint -isnot [string] -or $configuration.client -isnot [string] -or $configuration.token -isnot [string]){throw 'Invalid'}
            $uri=New-Object Uri($configuration.endpoint,[UriKind]::Absolute)
            if($uri.Scheme -ne 'https' -or -not $uri.Host -or $uri.UserInfo -or $uri.Query -or $uri.Fragment -or
               $uri.AbsolutePath -ne '/voyah-fm/v1' -or $configuration.endpoint.Length -gt 512 -or $configuration.endpoint -match '\s' -or
               $configuration.client -cnotmatch '^[a-zA-Z0-9_-]{1,64}$' -or
               $configuration.token -cnotmatch '^[a-zA-Z0-9_-]{32,128}$'){throw 'Invalid'}
            $privateConfiguration=@{endpoint=$configuration.endpoint;client=$configuration.client;token=$configuration.token}|ConvertTo-Json -Compress
        } catch {throw 'UPLOAD_CONFIG_INVALID: private configuration rejected; check HTTPS endpoint, client and token.'}
        Write-Host 'Private upload configuration validated. No report is sent by this installer.'
    } elseif($PSBoundParameters.ContainsKey('UploadConfig')){throw 'UPLOAD_CONFIG_MISSING: the requested private configuration file does not exist.'}
    else {Write-Host 'No private upload configuration supplied; existing device configuration is retained.'}
    # PowerShell transcripts capture parser ErrorRecords even when a catch handles them.
    # Start only after private JSON validation so malformed input cannot expose a token.
    Start-Transcript -Path (Join-Path $PSScriptRoot ('Install-FM-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.log')) -Force | Out-Null
    if(-not $Adb){foreach($candidate in @((Join-Path $PSScriptRoot 'adb/adb.exe'),(Join-Path $PSScriptRoot 'adb.exe'),(Join-Path $env:USERPROFILE 'Downloads/ADB_AppControl/adb/adb.exe'))){if(Test-Path -LiteralPath $candidate){$Adb=$candidate;break}}}
    if(-not $Adb){$Adb='adb.exe'}
    $script:AdbExe=(Get-Command $Adb -ErrorAction Stop).Source
    if(-not $Serial){
        $r=Adb-Call @('devices'); if($r.Code -ne 0){throw $r.Error}
        $devices=@($r.Text -split '\r?\n'|Where-Object {$_ -match '^\S+\s+device$'}|ForEach-Object {($_ -split '\s+')[0]})
        if($devices.Count -ne 1){throw 'Connect exactly one authorized head unit, or use -Serial.'}; $Serial=$devices[0]
    }
    $script:Serial=$Serial; Write-Host ('Device: '+$Serial)
    Write-Host 'Requesting adb root...'
    $r=Adb-Call @('-s',$Serial,'root'); Write-Host (($r.Text+$r.Error).Trim())
    Require-Adb @('-s',$Serial,'wait-for-device') 30000
    $r=Adb-Call @('-s',$Serial,'shell','id','-u')
    if($r.Code -ne 0 -or $r.Text.Trim() -ne '0'){
        $r=Adb-Call @('-s',$Serial,'shell','su','0','id','-u')
        if($r.Code -ne 0 -or $r.Text.Trim() -ne '0'){throw 'Neither adb root nor existing su 0 provides UID0.'}
        $script:UseSu=$true; Write-Host 'Using existing su 0 from ADB shell.'
    } else {Write-Host 'adb root confirmed: UID0.'}
    $r=Adb-Call @('-s',$Serial,'shell','getprop','ro.build.version.sdk')
    if($r.Code -ne 0 -or $r.Text.Trim() -ne '30'){throw 'This tester requires Android11/API30.'}
    $r=Adb-Call @('-s',$Serial,'shell','getenforce')
    if($r.Code -ne 0 -or $r.Text.Trim() -ne 'Permissive'){throw 'This tester requires the existing Permissive policy; it does not change SELinux.'}
    $apkPath=(Resolve-Path -LiteralPath $Apk).Path
    $hashStream=[System.IO.File]::OpenRead($apkPath); $hasher=[System.Security.Cryptography.SHA256]::Create()
    try {Write-Host ('APK SHA256: '+[System.BitConverter]::ToString($hasher.ComputeHash($hashStream)).Replace('-','').ToLowerInvariant())} finally {$hashStream.Dispose();$hasher.Dispose()}
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive=[System.IO.Compression.ZipFile]::OpenRead($apkPath)
    $stage=Join-Path ([System.IO.Path]::GetTempPath()) ('voyah-fm-install-'+[guid]::NewGuid().ToString('N'))
    [void][System.IO.Directory]::CreateDirectory($stage)
    $payload=@('helper.sh','broker.sh','adapter.js','ui.js','radio-ui.dex','template.xml','frida-inject','AdayoDAB.apk','RdsApp.apk')
    foreach($name in $payload){$entry=$archive.GetEntry('assets/'+$name);if(-not $entry){throw ('Missing asset '+$name)};[System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry,(Join-Path $stage $name))}
    foreach($name in @('helper.sh','broker.sh')){
        $scriptBytes=[System.IO.File]::ReadAllBytes((Join-Path $stage $name))
        if([Array]::IndexOf($scriptBytes,[byte]13) -ge 0){throw ('ANDROID_SCRIPT_CRLF_NOT_ALLOWED: '+$name)}
        if($scriptBytes.Length -ge 3 -and $scriptBytes[0] -eq 239 -and $scriptBytes[1] -eq 187 -and $scriptBytes[2] -eq 191){throw ('ANDROID_SCRIPT_BOM_NOT_ALLOWED: '+$name)}
        if($scriptBytes.Length -lt 17 -or [Text.Encoding]::ASCII.GetString($scriptBytes,0,17) -cne "#!/system/bin/sh`n"){throw ('ANDROID_SCRIPT_SHEBANG_INVALID: '+$name)}
    }
    if($privateConfiguration){[IO.File]::WriteAllText((Join-Path $stage 'upload.json'),$privateConfiguration,[Text.UTF8Encoding]::new($false))}
    Write-Host 'Installing FM Radio...'; Require-Adb @('-s',$Serial,'install','-r',$apkPath) 180000
    Write-Host 'The old FM Tester APK is replaced in place; station settings and saved reports are retained.'
    # Stop only our app during deployment; never stop Adayo or RDS.
    Root-Run @('am','force-stop','--user','0','ru.local.voyah.fmloader')
    $remote='/data/local/tmp/voyah-fm-upload-'+[guid]::NewGuid().ToString('N')
    $remoteFiles=$payload+@('bootstrap.sh'); if($privateConfiguration){$remoteFiles+=@('upload.json')}
    # Upload directory must belong to the same adbd UID that performs adb push.
    Require-Adb @('-s',$Serial,'shell','mkdir','-p',$remote)
    Require-Adb @('-s',$Serial,'shell','chmod','700',$remote)
    foreach($name in $payload){Require-Adb @('-s',$Serial,'push',(Join-Path $stage $name),($remote+'/'+$name))}
    if($privateConfiguration){Require-Adb @('-s',$Serial,'push',(Join-Path $stage 'upload.json'),($remote+'/upload.json'))}
    $bootstrap=@'
set -e
umask 077
[ "$(id -u)" = 0 ] || exit 81
echo BOOT_ROOT_CHANNEL_CHECK
getprop init.svc.logcat_sdcard
grep -n -E 'telnetd|load.bin' /system/etc/init.logcat.sh 2>/dev/null || true
grep -n -E 'ensure_telnetd|TELNETD_CMD' /data/local/tmp/load.bin 2>/dev/null || true
if ! grep -q 'telnetd' /system/etc/init.logcat.sh 2>/dev/null && ! grep -q 'ensure_telnetd' /data/local/tmp/load.bin 2>/dev/null; then
 echo BOOT_AUTOSTART_UNCONFIRMED
fi
D=/data/local/tmp/voyah-fm-loader-v1
S=__UPLOAD__
uid=$(cmd package list packages -U ru.local.voyah.fmloader | sed -n 's/.*uid://p' | head -1)
case "$uid" in ''|*[!0-9]*) exit 82;; esac
mkdir -p "$D/mailbox"
chmod 755 "$D"
chown "$uid:$uid" "$D/mailbox"
chmod 700 "$D/mailbox"
if [ -f "$D/broker.pid" ]; then
 p=$(cat "$D/broker.pid")
 case "$p" in ''|*[!0-9]*|0|1) ;; *)
  if [ -f /proc/$p/cmdline ]; then
   cmd=$(tr '\000' ' ' < /proc/$p/cmdline)
   case "$cmd" in *"sh $D/broker.sh "*)
    kill "$p" 2>/dev/null || true
    for n in 1 2 3 4 5; do kill -0 "$p" 2>/dev/null || break; sleep 1; done
    if [ -f /proc/$p/cmdline ]; then
     cmd=$(tr '\000' ' ' < /proc/$p/cmdline)
     case "$cmd" in *"sh $D/broker.sh "*) kill -9 "$p" 2>/dev/null || true; sleep 0.2;; esac
    fi
   ;; esac
  fi;; esac
fi
# Do not replace scripts while an older helper is still finishing a report.
# Keep advisory lock files: unlinking a locked inode would defeat serialization.
exec 0>"$D/operation.lock"
operation_locked=0
n=0
while [ "$n" -lt 95 ]; do
 if flock -n 0; then operation_locked=1; break; fi
 n=$((n+1)); sleep 1
done
[ "$operation_locked" = 1 ] || { echo MIGRATION_HELPER_BUSY; exit 84; }
# BEGIN FM BETA MIGRATION
for stale in "$D/mailbox/request" "$D/mailbox/request.tmp" "$D/mailbox/online" "$D/mailbox/"*.reply "$D/broker.pid" "$D/config.next" "$D/reply.new" "$D/reply.body"; do
 rm -f "$stale"
done
current_pid=$(pidof com.adayo.service.dab 2>/dev/null || true)
for kind in ready used reloaded error; do
 for marker in "$D/runtime/$kind-"*; do
  [ -f "$marker" ] || continue
  marker_pid=${marker##*-}
  case "$marker_pid" in ''|*[!0-9]*) continue;; esac
  [ "$marker_pid" = "$current_pid" ] || rm -f "$marker"
 done
done
echo LEGACY_TESTER_MIGRATION_OK
# END FM BETA MIGRATION
for name in helper.sh broker.sh adapter.js ui.js radio-ui.dex template.xml frida-inject AdayoDAB.apk RdsApp.apk; do
 if ! cmp -s "$S/$name" "$D/$name"; then cp "$S/$name" "$D/$name"; fi
 chown 0:0 "$D/$name"
 chmod 644 "$D/$name"
done
chmod 755 "$D/frida-inject"
echo 0.5.0-beta-v1 > "$D/payload-version"
chmod 644 "$D/payload-version"
__INSTALL_UPLOAD__
exec 0</dev/null
nohup setsid sh "$D/broker.sh" > "$D/broker.log" 2>&1 < /dev/null &
sleep 1
[ -f "$D/mailbox/online" ] || exit 83
echo BROKER_ACTIVATED
'@
    $installUpload=''
    if($privateConfiguration){$installUpload=@'
# BEGIN FM UPLOAD CONFIG
F=/data/user/0/ru.local.voyah.fmloader/files
mkdir -p "$F"
chown "$uid:$uid" "$F"
chmod 700 "$F"
cp "$S/upload.json" "$F/.upload.json.install"
chown "$uid:$uid" "$F/.upload.json.install"
chmod 600 "$F/.upload.json.install"
mv -f "$F/.upload.json.install" "$F/upload.json"
restorecon "$F/upload.json" 2>/dev/null || true
echo UPLOAD_CONFIG_INSTALLED
# END FM UPLOAD CONFIG
'@}
    $bootstrap=$bootstrap.Replace('__UPLOAD__',$remote).Replace('__INSTALL_UPLOAD__',$installUpload).Replace("`r",'')+"`n"
    $bootstrapPath=Join-Path $stage 'bootstrap.sh'
    [System.IO.File]::WriteAllText($bootstrapPath,$bootstrap,[System.Text.UTF8Encoding]::new($false))
    Require-Adb @('-s',$Serial,'push',$bootstrapPath,($remote+'/bootstrap.sh'))
    Root-Run @('sh',($remote+'/bootstrap.sh')) 120000
    Write-Host 'Recording logs before installing missing FM components...'
    Root-Run @('sh','/data/local/tmp/voyah-fm-loader-v1/helper.sh','log-start')
    Root-Run @('sh','/data/local/tmp/voyah-fm-loader-v1/helper.sh','install-components') 180000
    Root-Run @('sh','/data/local/tmp/voyah-fm-loader-v1/helper.sh','check')
    # Remove only our obsolete separate UI after the main package and payload succeed.
    if(Test-LegacyDiagnostics){
        Write-Host 'Removing the old separate FM Diagnostics app...'
        $removed=Root-Call @('pm','uninstall','ru.local.voyah.fmdiagnostics') 90000
        $remaining=Test-LegacyDiagnostics
        if($removed.Code -ne 0 -or $removed.Text.Trim() -ne 'Success' -or $remaining){
            throw 'LEGACY_DIAGNOSTICS_REMOVE_FAILED: FM Radio is installed; retry installation to finish removing the old diagnostics app.'
        }
    }
    Root-Run @('am','start','--user','0','-n','ru.local.voyah.fmloader/.MainActivity')
    Write-Host 'INSTALL_OK. FM Radio opens the OEM radio screen. Automatic logging and boot startup are enabled.'
    Write-Host 'For reports: use the gear menu on the radio screen. Save ZIP keeps a local copy; Send report uploads when configured. Recording continues.'
    Write-Host 'No report was sent by the installer. Collect-FM-now.cmd can create a new report directly on the PC.'
    Write-Host 'Test radio after reboot and after locking the vehicle; keep the report if frequency or sound is lost.'
} catch {
    Write-Host ('INSTALL_FAILED: '+$_)
    exit 1
} finally {
    if($archive){$archive.Dispose()}
    if($remote -match '^/data/local/tmp/voyah-fm-upload-[0-9a-f]{32}$'){
        foreach($name in $remoteFiles){try{[void](Root-Call @('rm','-f',($remote+'/'+$name)))}catch{}}
        try{[void](Root-Call @('rmdir',$remote))}catch{}
    }
    if($stage){
        $resolved=[System.IO.Path]::GetFullPath($stage);$temp=[System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
        if($resolved.StartsWith($temp,[StringComparison]::OrdinalIgnoreCase) -and (Split-Path $resolved -Leaf) -match '^voyah-fm-install-[0-9a-f]{32}$'){Remove-Item -LiteralPath $resolved -Recurse -Force}
    }
    try{Stop-Transcript | Out-Null}catch{}
}
