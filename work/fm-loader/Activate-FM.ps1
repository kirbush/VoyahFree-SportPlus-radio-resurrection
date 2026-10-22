param([string]$Adb='', [string]$Serial='', [string]$Apk=(Join-Path $PSScriptRoot 'Voyah-FM-Tester-0.3.apk'))
$ErrorActionPreference='Stop'
if(-not $Adb){
    $candidate=Join-Path $env:USERPROFILE 'Downloads/ADB_AppControl/adb/adb.exe'
    if(Test-Path -LiteralPath $candidate){$Adb=$candidate}else{$Adb='adb'}
}
function Invoke-Adb {
    & $Adb -s $Serial @args
    if($LASTEXITCODE -ne 0){throw "ADB failed: $($args -join ' ')"}
}
if(-not $Serial){
    $devices=@(& $Adb devices | Select-Object -Skip 1 | Where-Object {$_ -match '^\S+\s+device$'} | ForEach-Object {($_ -split '\s+')[0]})
    if($devices.Count -ne 1){throw 'Connect exactly one authorized ADB device or specify -Serial.'}
    $Serial=$devices[0]
}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$stage=Join-Path ([System.IO.Path]::GetTempPath()) ('voyah-fm-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $stage | Out-Null
$archive=[System.IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $Apk).Path)
try {
    Invoke-Adb install -r $Apk
    Invoke-Adb shell mkdir -p /data/local/tmp/fm-loader-upload
    foreach($name in @('helper.sh','broker.sh','adapter.js','template.xml','frida-inject','AdayoDAB.apk','RdsApp.apk')){
        $entry=$archive.GetEntry('assets/'+$name)
        if(-not $entry){throw "Missing payload: $name"}
        $target=Join-Path $stage $name
        [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry,$target)
        Invoke-Adb push $target ('/data/local/tmp/fm-loader-upload/'+$name)
    }
    $script=@'
set -e
D=/data/local/tmp/voyah-fm-loader-v1
S=/data/local/tmp/fm-loader-upload
uid=$(cmd package list packages -U ru.local.voyah.fmloader | sed -n 's/.*uid://p' | head -1)
case "$uid" in ''|*[!0-9]*) exit 1;; esac
mkdir -p "$D/mailbox"
chmod 755 "$D"
chown "$uid:$uid" "$D/mailbox"
chmod 700 "$D/mailbox"
if [ -f "$D/broker.pid" ]; then
p=$(cat "$D/broker.pid")
case "$p" in ''|*[!0-9]*) ;; *)
if [ -f /proc/$p/cmdline ]; then
cmd=$(tr '\000' ' ' < /proc/$p/cmdline)
case "$cmd" in *"sh $D/broker.sh "*) kill "$p"; sleep 1;; esac
fi;; esac
fi
for name in helper.sh broker.sh adapter.js template.xml frida-inject AdayoDAB.apk RdsApp.apk; do
    if ! cmp -s "$S/$name" "$D/$name"; then cp "$S/$name" "$D/$name"; fi
    chown 0:0 "$D/$name"
    chmod 644 "$D/$name"
done
chmod 755 "$D/frida-inject"
echo 0.3-preflight-v1 > "$D/payload-version"
chmod 644 "$D/payload-version"
nohup setsid sh "$D/broker.sh" > "$D/broker.log" 2>&1 < /dev/null &
sleep 1
[ -f "$D/mailbox/online" ] || exit 83
echo BROKER_ACTIVATED
'@
    $scriptPath=Join-Path $stage 'activate.sh'
    [System.IO.File]::WriteAllText($scriptPath,$script.Replace("`r",'')+"`n",[System.Text.UTF8Encoding]::new($false))
    Invoke-Adb push $scriptPath /data/local/tmp/fm-loader-activate.sh
    Invoke-Adb shell su 0 sh /data/local/tmp/fm-loader-activate.sh
    Write-Host 'Fallback activation complete. Open Voyah FM Tester. The app normally activates itself through the existing local root channel.'
} finally {
    $archive.Dispose()
    # Delete only this verified unique staging directory.
    $resolvedStage=[System.IO.Path]::GetFullPath($stage)
    $tempRoot=[System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
    if($resolvedStage.StartsWith($tempRoot,[StringComparison]::OrdinalIgnoreCase) -and (Split-Path $resolvedStage -Leaf) -match '^voyah-fm-[0-9a-f]{32}$'){
        Remove-Item -LiteralPath $resolvedStage -Recurse -Force
    }
}
