param([string]$Adb='', [string]$Serial='', [string]$Destination='', [string]$UploadConfig='')
$ErrorActionPreference='Stop'
function Quote-WindowsArgument([string]$Value) {
    $escaped=[regex]::Replace($Value,'(\\*)"','$1$1\"')
    $escaped=[regex]::Replace($escaped,'(\\+)$','$1$1')
    return '"'+$escaped+'"'
}
function Read-AdbText([string[]]$TaskArguments,[int]$TimeoutMs=20000) {
    $info=New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName=$script:AdbExe
    $info.Arguments=(($TaskArguments | ForEach-Object {Quote-WindowsArgument $_}) -join ' ')
    $info.UseShellExecute=$false; $info.CreateNoWindow=$true
    $info.RedirectStandardOutput=$true; $info.RedirectStandardError=$true
    $info.StandardOutputEncoding=[System.Text.Encoding]::UTF8
    $info.StandardErrorEncoding=[System.Text.Encoding]::UTF8
    $proc=New-Object System.Diagnostics.Process; $proc.StartInfo=$info
    try {
        [void]$proc.Start()
        $outputTask=$proc.StandardOutput.ReadToEndAsync(); $errorTask=$proc.StandardError.ReadToEndAsync()
        if(-not $proc.WaitForExit($TimeoutMs)){$proc.Kill();throw 'ADB не ответил вовремя. Проверьте USB и повторите сбор.'}
        return [pscustomobject]@{Code=$proc.ExitCode;Text=$outputTask.Result;Error=$errorTask.Result}
    } finally { $proc.Dispose() }
}
$script:ProbeNotes=New-Object 'System.Collections.Generic.List[string]'
function Read-OptionalRootProbe([string[]]$TaskArguments,[int]$TimeoutMs=5000) {
    try {return Read-AdbText $TaskArguments $TimeoutMs}
    catch {
        [void]$script:ProbeNotes.Add((($TaskArguments -join ' ')+' : '+$_.Exception.Message))
        return [pscustomobject]@{Code=-1;Text='';Error=$_.Exception.Message}
    }
}
$stage=$null; $temporary=$null
try {
    if(-not $Adb){
        foreach($candidate in @((Join-Path $PSScriptRoot 'adb/adb.exe'),(Join-Path $PSScriptRoot 'adb.exe'),(Join-Path $PSScriptRoot '../adb/adb.exe'))){
            if(Test-Path -LiteralPath $candidate){$Adb=$candidate;break}
        }
        if(-not $Adb){$found=Get-Command adb -CommandType Application -ErrorAction SilentlyContinue;if($found){$Adb=$found.Source}}
        if(-not $Adb){throw 'Распакуйте архив целиком: рядом с файлом запуска должна быть папка adb.'}
    }
    $script:AdbExe=(Resolve-Path -LiteralPath $Adb).Path
    if(-not $Serial){
        $devices=Read-AdbText @('devices')
        if($devices.Code -ne 0){throw ('Ошибка ADB: '+$devices.Error)}
        $authorized=@($devices.Text -split '\r?\n' | Where-Object {$_ -match '^\S+\s+device\s*$'} | ForEach-Object {($_ -split '\s+')[0]})
        if($authorized.Count -ne 1){throw 'Подключите по USB одно ГУ и разрешите USB-отладку. Затем запустите сбор ещё раз.'}
        $Serial=$authorized[0]
    }
    if($Serial -notmatch '^[a-zA-Z0-9_.:-]+$'){throw 'Недопустимый идентификатор устройства.'}
    $interactive=-not $Destination
    if($interactive){
        if([Threading.Thread]::CurrentThread.GetApartmentState() -ne 'STA'){throw 'Запустите Collect-FM-now.cmd для выбора папки.'}
        Add-Type -AssemblyName System.Windows.Forms
        $dialog=New-Object System.Windows.Forms.FolderBrowserDialog
        $dialog.Description='Выберите папку на ПК для отчёта радио';$dialog.ShowNewFolderButton=$true
        $dialog.SelectedPath=[Environment]::GetFolderPath('MyDocuments')
        try {if($dialog.ShowDialog() -ne 'OK'){Write-Host 'Сбор отменён.';return};$Destination=$dialog.SelectedPath}finally{$dialog.Dispose()}
    }
    $folder=[IO.Path]::GetFullPath($Destination);[void][IO.Directory]::CreateDirectory($folder)
    $mode='limited'
    $identity=Read-AdbText @('-s',$Serial,'shell','id','-u')
    if($identity.Code -eq 0 -and $identity.Text.Trim() -eq '0'){$mode='root'}
    else {
        $identity=Read-OptionalRootProbe @('-s',$Serial,'shell','su','0','id','-u')
        if($identity.Code -eq 0 -and $identity.Text.Trim() -eq '0'){$mode='su'}
        else {
            $requestRoot=Read-OptionalRootProbe @('-s',$Serial,'root')
            if($requestRoot.Code -eq 0){
                $wait=Read-OptionalRootProbe @('-s',$Serial,'wait-for-device') 10000
                if($wait.Code -eq 0){$identity=Read-OptionalRootProbe @('-s',$Serial,'shell','id','-u');if($identity.Code -eq 0 -and $identity.Text.Trim() -eq '0'){$mode='root'}}
            }
        }
    }
    $payload=[IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'Collect-FM-state.sh'))
    if([Array]::IndexOf($payload,[byte]13) -ge 0 -or ($payload.Length -ge 3 -and $payload[0] -eq 239 -and $payload[1] -eq 187 -and $payload[2] -eq 191)){throw 'Повреждён Android-скрипт. Распакуйте исходный архив заново.'}
    $remoteScript=[Text.Encoding]::UTF8.GetString($payload)
    if(-not $remoteScript.StartsWith("#!/system/bin/sh`n")){throw 'Неверный файл Collect-FM-state.sh.'}
    $quoted="'"+$remoteScript.Replace("'","'\''")+"'"
    $command='sh -c '+$quoted
    if($mode -eq 'su'){$command='su 0 '+$command}
    Write-Host 'Собираю отчёт. Радио можно оставить открытым. Подождите до трёх минут.'
    if($mode -eq 'limited'){Write-Host 'Root недоступен: будет сохранён ограниченный отчёт.'}
    $result=Read-AdbText @('-s',$Serial,'exec-out',$command) 180000
    if($result.Code -ne 0){throw ('Сбор прерван: '+$result.Error)}
    if($result.Text -notmatch '(?m)^VOYAH_PC_DIAGNOSTIC_BEGIN\r?$' -or $result.Text -notmatch '(?m)^VOYAH_PC_DIAGNOSTIC_END\r?$'){throw 'Получен неполный ответ ГУ. Проверьте USB и повторите сбор.'}
    $tempRoot=[IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    $stage=Join-Path $tempRoot ('voyah-fm-collect-'+[guid]::NewGuid().ToString('N'))
    [void][IO.Directory]::CreateDirectory($stage)
    $encoding=New-Object Text.UTF8Encoding($false)
    [IO.File]::WriteAllText((Join-Path $stage 'environment.txt'),("Voyah FM PC collector 2`nTime="+[DateTimeOffset]::Now.ToString('o')+"`nADB_SERIAL=$Serial`nROOT_MODE=$mode`n"),$encoding)
    [IO.File]::WriteAllText((Join-Path $stage 'diagnostics.txt'),$result.Text,$encoding)
    [IO.File]::WriteAllText((Join-Path $stage 'collection.txt'),("ROOT_MODE=$mode`nADB_EXIT="+$result.Code+"`nROOT_PROBE_NOTES:`n"+($script:ProbeNotes -join "`n")+"`nSTDERR:`n"+$result.Error),$encoding)
    $base='Voyah-FM-PC-report-'+(Get-Date -Format 'yyyyMMdd-HHmmss')
    $final=Join-Path $folder ($base+'.zip');$number=2
    while(Test-Path -LiteralPath $final){$final=Join-Path $folder ($base+'-'+$number+'.zip');$number++}
    $temporary=Join-Path $folder ('.voyah-fm-'+[guid]::NewGuid().ToString('N')+'.partial')
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::CreateFromDirectory($stage,$temporary)
    $zip=[IO.Compression.ZipFile]::OpenRead($temporary)
    try {foreach($name in @('environment.txt','diagnostics.txt','collection.txt')){if($null -eq $zip.GetEntry($name)){throw ('Неполный ZIP: '+$name)}}}finally{$zip.Dispose()}
    [IO.File]::Move($temporary,$final);$temporary=$null
    Write-Host ('COLLECT_OK: '+$final)
    $message='Отправьте этот ZIP:'+"`r`n"+$final
    if(-not $UploadConfig){$UploadConfig=Join-Path $PSScriptRoot 'upload.json'}
    if([IO.File]::Exists($UploadConfig)){
        try {
            . (Join-Path $PSScriptRoot 'Upload-FM-report.ps1')
            $upload=Send-FmReports -ReportPath $final -ConfigurationPath $UploadConfig
            Write-Host ('UPLOAD_'+$upload.Status+' Pending='+$upload.Pending)
            if($upload.Status -eq 'SENT'){$message='Отчёт отправлен на сервер. Копия сохранена:'+"`r`n"+$final}
            elseif($upload.Status -eq 'QUEUED'){$message='Отчёт сохранён и ждёт отправки. При следующем запуске сборщика отправка повторится.'+"`r`n"+$final}
            else {$message='Отчёт сохранён, но не отправлен. Сообщите разработчику код UPLOAD_'+$upload.Status+"`r`n"+$final}
        } catch {Write-Host 'UPLOAD_UNAVAILABLE: local ZIP preserved'}
    }
    if($interactive){[void][Windows.Forms.MessageBox]::Show($message,'Отчёт радио сохранён','OK','Information')}
} catch {Write-Error $_;exit 1}
finally {
    if($temporary -and [IO.File]::Exists($temporary)){[IO.File]::Delete($temporary)}
    if($stage){
        $resolved=[IO.Path]::GetFullPath($stage)
        $prefix=[IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')+'\'
        if($resolved.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase) -and [IO.Path]::GetFileName($resolved) -match '^voyah-fm-collect-[0-9a-f]{32}$'){
            if([IO.Directory]::Exists($resolved)){[IO.Directory]::Delete($resolved,$true)}
        }
    }
}
