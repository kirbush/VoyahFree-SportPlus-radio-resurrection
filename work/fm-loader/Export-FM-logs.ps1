param(
    [string]$Adb='',
    [string]$Serial='',
    [string]$Destination='',
    [switch]$AllReports
)
$ErrorActionPreference='Stop'
function Quote-WindowsArgument([string]$Value) {
    $escaped=[regex]::Replace($Value,'(\\*)"','$1$1\"')
    $escaped=[regex]::Replace($escaped,'(\\+)$','$1$1')
    return '"'+$escaped+'"'
}
function Start-AdbProcess([string[]]$TaskArguments) {
    $info=New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName=$script:AdbExe
    $info.Arguments=(($TaskArguments | ForEach-Object {Quote-WindowsArgument $_}) -join ' ')
    $info.UseShellExecute=$false; $info.CreateNoWindow=$true
    $info.RedirectStandardOutput=$true; $info.RedirectStandardError=$true
    $info.StandardOutputEncoding=[System.Text.Encoding]::UTF8
    $info.StandardErrorEncoding=[System.Text.Encoding]::UTF8
    $proc=New-Object System.Diagnostics.Process
    $proc.StartInfo=$info
    [void]$proc.Start()
    return $proc
}
function Read-AdbText([string[]]$TaskArguments) {
    $proc=Start-AdbProcess $TaskArguments
    try {
        $outputTask=$proc.StandardOutput.ReadToEndAsync()
        $errorTask=$proc.StandardError.ReadToEndAsync()
        if(-not $proc.WaitForExit(20000)){$proc.Kill();throw 'ADB не ответил за 20 секунд.'}
        return [pscustomobject]@{Code=$proc.ExitCode;Text=$outputTask.Result;Error=$errorTask.Result}
    } finally {$proc.Dispose()}
}
function Copy-AdbBinary([string[]]$TaskArguments,[string]$Target) {
    $proc=Start-AdbProcess $TaskArguments
    $stream=$null
    try {
        $errorTask=$proc.StandardError.ReadToEndAsync()
        $stream=[System.IO.File]::Open($Target,[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::Write,[System.IO.FileShare]::None)
        $copyTask=$proc.StandardOutput.BaseStream.CopyToAsync($stream)
        if(-not $copyTask.Wait(60000)){$proc.Kill();throw 'Передача отчёта превысила 60 секунд.'}
        if(-not $proc.WaitForExit(5000)){$proc.Kill();throw 'ADB не завершил передачу.'}
        if($proc.ExitCode -ne 0){throw ('ADB не смог прочитать архив: '+$errorTask.Result)}
    } finally {
        if($null -ne $stream){$stream.Dispose()}
        if(-not $proc.HasExited){$proc.Kill()}
        $proc.Dispose()
    }
}
function Test-ReportZip([string]$Path) {
    $archive=[System.IO.Compression.ZipFile]::OpenRead($Path)
    try {
        foreach($required in @('environment.txt','diagnostics.txt')){
            if($null -eq $archive.GetEntry($required)){throw ('В ZIP отсутствует '+$required)}
        }
        foreach($entry in $archive.Entries){
            $inputStream=$entry.Open()
            try {$inputStream.CopyTo([System.IO.Stream]::Null)}finally{$inputStream.Dispose()}
        }
    } finally {$archive.Dispose()}
}
try {
    if(-not $Adb){
        foreach($candidate in @((Join-Path $PSScriptRoot 'adb.exe'),(Join-Path $PSScriptRoot 'adb/adb.exe'),(Join-Path $PSScriptRoot '../adb/adb.exe'),(Join-Path $env:USERPROFILE 'Downloads/ADB_AppControl/adb/adb.exe'))){
            if(Test-Path -LiteralPath $candidate){$Adb=$candidate;break}
        }
        if(-not $Adb){$command=Get-Command adb -CommandType Application -ErrorAction SilentlyContinue;if($command){$Adb=$command.Source}}
        if(-not $Adb){
            Add-Type -AssemblyName System.Windows.Forms
            $pick=New-Object System.Windows.Forms.OpenFileDialog
            $pick.Title='Выберите adb.exe';$pick.Filter='ADB (adb.exe)|adb.exe'
            try {if($pick.ShowDialog() -ne 'OK'){Write-Host 'Выгрузка отменена.';return};$Adb=$pick.FileName}finally{$pick.Dispose()}
        }
    }
    $script:AdbExe=(Resolve-Path -LiteralPath $Adb).Path
    if(-not $Serial){
        $result=Read-AdbText @('devices')
        if($result.Code -ne 0){throw ('Ошибка ADB: '+$result.Error)}
        $devices=@($result.Text -split '\r?\n' | Where-Object {$_ -match '^\S+\s+device\s*$'} | ForEach-Object {($_ -split '\s+')[0]})
        if($devices.Count -ne 1){throw 'Подключите по USB одно ГУ с разрешённой USB-отладкой. Для нескольких устройств укажите -Serial.'}
        $Serial=$devices[0]
    }
    if($Serial -notmatch '^[a-zA-Z0-9_.:-]+$'){throw 'Недопустимый идентификатор ADB.'}
    $identity=Read-AdbText @('-s',$Serial,'shell','id','-u')
    $directRoot=$identity.Code -eq 0 -and $identity.Text.Trim() -eq '0'
    $rootCommand="sh -c 'ls -1 /data/user/0/ru.local.voyah.fmloader/files/Voyah-FM-report-*.zip 2>/dev/null'"
    if(-not $directRoot){$rootCommand='su 0 '+$rootCommand}
    $listed=Read-AdbText @('-s',$Serial,'shell',$rootCommand)
    $privatePattern='^/data/user/0/ru\.local\.voyah\.fmloader/files/Voyah-FM-report-[0-9]{8}-[0-9]{6}\.zip$'
    $remoteFiles=@($listed.Text -split '\r?\n' | Where-Object {$_ -cmatch $privatePattern} | Sort-Object -Unique)
    $private=$true
    if($remoteFiles.Count -eq 0){
        $private=$false
        $publicCommand='ls -1 /sdcard/Download/Voyah-FM-report-*.zip /sdcard/Downloads/Voyah-FM-report-*.zip /storage/emulated/0/Download/Voyah-FM-report-*.zip /sdcard/Documents/Voyah-FM-report-*.zip 2>/dev/null'
        $listed=Read-AdbText @('-s',$Serial,'shell',$publicCommand)
        $publicPattern='^/(sdcard|storage/emulated/0)/(Download|Downloads|Documents)/Voyah-FM-report-[0-9]{8}-[0-9]{6}\.zip$'
        $remoteFiles=@($listed.Text -split '\r?\n' | Where-Object {$_ -cmatch $publicPattern} | Sort-Object -Unique)
    }
    if($remoteFiles.Count -eq 0){throw 'Отчёт не найден. На ГУ нажмите «Сохранить отчёт ZIP». Если root через ADB недоступен, сохраните ZIP в Downloads и повторите выгрузку.'}
    $remoteFiles=@($remoteFiles | Sort-Object -Descending)
    if(-not $AllReports){$remoteFiles=@($remoteFiles[0])}
    $interactive=-not $Destination
    if($interactive){
        if([System.Threading.Thread]::CurrentThread.GetApartmentState() -ne 'STA'){throw 'Для выбора папки запустите Export-FM-logs.cmd или PowerShell с параметром -STA.'}
        Add-Type -AssemblyName System.Windows.Forms
        $dialog=New-Object System.Windows.Forms.FolderBrowserDialog
        $dialog.Description='Выберите папку на ПК для отчёта Voyah FM'
        $dialog.ShowNewFolderButton=$true
        $dialog.SelectedPath=[Environment]::GetFolderPath('MyDocuments')
        try {if($dialog.ShowDialog() -ne 'OK'){Write-Host 'Выгрузка отменена.';return};$Destination=$dialog.SelectedPath}finally{$dialog.Dispose()}
    }
    $folder=[System.IO.Path]::GetFullPath($Destination)
    [void][System.IO.Directory]::CreateDirectory($folder)
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $saved=@()
    foreach($remote in $remoteFiles){
        $name=($remote -split '/')[-1]
        $base=[System.IO.Path]::GetFileNameWithoutExtension($name)
        $final=Join-Path $folder $name
        $number=2
        while(Test-Path -LiteralPath $final){$final=Join-Path $folder ($base+'-'+$number+'.zip');$number++}
        $temporary=Join-Path $folder ('.voyah-fm-'+[guid]::NewGuid().ToString('N')+'.partial')
        $transfer=@('-s',$Serial,'exec-out')
        if($private -and -not $directRoot){$transfer+=@('su','0')}
        try {
            Write-Host ('Копирую '+$name+'…')
            Copy-AdbBinary ($transfer+@('cat',$remote)) $temporary
            Test-ReportZip $temporary
            $algorithm=[System.Security.Cryptography.SHA256]::Create()
            $hashStream=[System.IO.File]::OpenRead($temporary)
            try {$hash=[BitConverter]::ToString($algorithm.ComputeHash($hashStream)).Replace('-','').ToLowerInvariant()}
            finally {$hashStream.Dispose();$algorithm.Dispose()}
            $remoteHash=Read-AdbText ($transfer+@('sha256sum',$remote))
            if($remoteHash.Code -eq 0 -and $remoteHash.Text -match '^([a-fA-F0-9]{64})\s'){
                if($hash -ne $Matches[1].ToLowerInvariant()){throw 'Контрольная сумма не совпала. Архив не сохранён; повторите передачу.'}
            }
            [System.IO.File]::Move($temporary,$final)
            $saved+=,$final
            Write-Host ('Сохранено: '+$final)
            Write-Host ('SHA256: '+$hash)
        } finally {
            # Only this exact, newly-created partial file may be removed.
            if([System.IO.File]::Exists($temporary)){[System.IO.File]::Delete($temporary)}
        }
    }
    if($interactive){[void][System.Windows.Forms.MessageBox]::Show(($saved -join "`r`n"),'Отчёты Voyah FM сохранены','OK','Information')}
} catch {
    Write-Error $_
    exit 1
}
