# Optional upload-only client. Never changes ADB or FM state.
function Get-FmUploadHash([string]$Path) {
    $stream=[IO.File]::OpenRead($Path);$hash=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($hash.ComputeHash($stream))).Replace('-','').ToLowerInvariant()}
    finally {$hash.Dispose();$stream.Dispose()}
}
function Read-FmUploadReceipt([IO.Stream]$Stream) {
    $reader=New-Object IO.StreamReader($Stream,[Text.Encoding]::UTF8)
    try {
        $chars=New-Object char[] 8193;$length=$reader.ReadBlock($chars,0,$chars.Length)
        if($length -gt 8192){throw 'Invalid upload receipt'}
        $body=[string]::new($chars,0,$length)
        return ConvertFrom-Json -InputObject $body
    } finally {$reader.Dispose()}
}
function Invoke-FmUploadRequest($Configuration,[string]$File,[string]$Hash,[string]$Name) {
    [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
    $request=[Net.HttpWebRequest]::Create($Configuration.endpoint+'/reports/'+$Hash)
    $request.Method='PUT';$request.ContentType='application/zip';$request.Accept='application/json'
    $request.AllowAutoRedirect=$false;$request.Timeout=15000;$request.ReadWriteTimeout=15000
    $request.KeepAlive=$false;$request.AllowWriteStreamBuffering=$false
    $request.Headers['Authorization']='Bearer '+$Configuration.token
    $request.Headers['X-FM-Source']='pc';$request.Headers['X-FM-Report-Name']=$Name
    $inputFile=[IO.File]::OpenRead($File);$response=$null
    try {
        $request.ContentLength=$inputFile.Length
        $destination=$request.GetRequestStream()
        try {$inputFile.CopyTo($destination)} finally {$destination.Dispose()}
        $response=$request.GetResponse()
        if([int]$response.StatusCode -notin @(200,201)){throw 'Upload rejected'}
        return Read-FmUploadReceipt $response.GetResponseStream()
    } finally {$inputFile.Dispose();if($response){$response.Dispose()};$request.Abort()}
}
function Add-FmUploadQueueFile([string]$Source,[string]$Target,[string]$Metadata,[string]$Name,[string]$Hash) {
    $temporary=Join-Path ([IO.Path]::GetDirectoryName($Target)) ('.'+[guid]::NewGuid().ToString('N')+'.partial')
    try {
        [IO.File]::Copy($Source,$temporary,$false)
        if((Get-FmUploadHash $temporary) -ne $Hash){throw 'Report changed during copy'}
        [IO.File]::WriteAllText($Metadata,(@{name=$Name;sha256=$Hash}|ConvertTo-Json),[Text.Encoding]::UTF8)
        [IO.File]::Move($temporary,$Target)
    } finally {if([IO.File]::Exists($temporary)){[IO.File]::Delete($temporary)}}
}
function Send-FmReports([string]$ReportPath,[string]$ConfigurationPath,[string]$QueueRoot='') {
    if(-not [IO.File]::Exists($ConfigurationPath)){return [pscustomobject]@{Status='NOT_CONFIGURED';Pending=0;Sent=0;Error=''}}
    $mutex=$null;$held=$false;$temporary=$null
    try {
        if((Get-Item -LiteralPath $ConfigurationPath).Length -gt 16384){throw 'Configuration too large'}
        $configuration=ConvertFrom-Json -InputObject ([IO.File]::ReadAllText($ConfigurationPath))
        $uri=New-Object Uri($configuration.endpoint,[UriKind]::Absolute)
        if($uri.Scheme -ne 'https' -or $uri.UserInfo -or $uri.Query -or $uri.Fragment -or
           $uri.AbsolutePath -ne '/voyah-fm/v1' -or $configuration.endpoint.Length -gt 512 -or
           $configuration.client -notmatch '^[a-zA-Z0-9_-]{1,64}$' -or
           $configuration.token -cnotmatch '^[a-zA-Z0-9_-]{32,128}$'){throw 'Invalid private configuration'}
        if(-not $QueueRoot){$QueueRoot=Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'Voyah-FM/upload-queue'}
        $algorithm=[Security.Cryptography.SHA256]::Create()
        try {$namespace=([BitConverter]::ToString($algorithm.ComputeHash([Text.Encoding]::UTF8.GetBytes($configuration.endpoint+"`n"+$configuration.client)))).Replace('-','').ToLowerInvariant()}
        finally {$algorithm.Dispose()}
        $queue=Join-Path ([IO.Path]::GetFullPath($QueueRoot)) $namespace
        [void][IO.Directory]::CreateDirectory($queue)
        $mutex=New-Object Threading.Mutex($false,('Local\VoyahFMUpload-'+$namespace))
        try {$held=$mutex.WaitOne(3000)}catch [Threading.AbandonedMutexException]{$held=$true}
        if(-not $held){return [pscustomobject]@{Status='BUSY';Pending=0;Sent=0;Error='Another upload is in progress'}}
        $name=[IO.Path]::GetFileName($ReportPath)
        if($name -notmatch '^Voyah-FM-(PC-)?report-[0-9]{8}-[0-9]{6}(-[0-9]+)?\.zip$'){throw 'Invalid report name'}
        $length=(Get-Item -LiteralPath $ReportPath).Length
        if($length -le 0 -or $length -gt 16MB){throw 'Invalid report size'}
        $hash=Get-FmUploadHash $ReportPath
        $queuedFile=Join-Path $queue ($hash+'.zip');$metadata=Join-Path $queue ($hash+'.meta.json')
        $receipt=Join-Path $queue ($hash+'.receipt.json')
        $deferredAdmission=$false
        if(-not [IO.File]::Exists($queuedFile) -and -not [IO.File]::Exists($receipt)){
            $pending=@(Get-ChildItem -LiteralPath $queue -File -Filter '*.zip')
            $bytes=($pending|Measure-Object -Property Length -Sum).Sum
            if($pending.Count -ge 32 -or $bytes+$length -gt 64MB){$deferredAdmission=$true}
            else {Add-FmUploadQueueFile $ReportPath $queuedFile $metadata $name $hash}
        }
        $sent=0;$errorCode='';$clock=[Diagnostics.Stopwatch]::StartNew()
        foreach($file in @(Get-ChildItem -LiteralPath $queue -File -Filter '*.zip'|Sort-Object LastWriteTimeUtc|Select-Object -First 5)){
            if($clock.Elapsed.TotalSeconds -gt 35){break}
            $id=$file.BaseName
            if($id -cnotmatch '^[0-9a-f]{64}$'){continue}
            try {
                $meta=ConvertFrom-Json -InputObject ([IO.File]::ReadAllText((Join-Path $queue ($id+'.meta.json'))))
                if($meta.sha256 -ne $id -or $meta.name -notmatch '^Voyah-FM-(PC-)?report-[0-9]{8}-[0-9]{6}(-[0-9]+)?\.zip$' -or
                   (Get-FmUploadHash $file.FullName) -ne $id){throw 'Invalid queue entry'}
                $ack=Invoke-FmUploadRequest $configuration $file.FullName $id $meta.name
                if($ack.ok -ne $true -or $ack.sha256 -cne $id -or $ack.id -cne ($configuration.client+'/'+$id) -or $ack.bytes -ne $file.Length){throw 'Invalid upload receipt'}
                $record=Join-Path $queue ($id+'.receipt.json')
                [IO.File]::WriteAllText($record,($ack|ConvertTo-Json),[Text.Encoding]::UTF8)
                [IO.File]::Delete($file.FullName)
                [IO.File]::Delete((Join-Path $queue ($id+'.meta.json')))
                $sent++
            } catch {$errorCode=$_.Exception.GetType().Name;break}
        }
        if($deferredAdmission){
            $pending=@(Get-ChildItem -LiteralPath $queue -File -Filter '*.zip')
            $bytes=($pending|Measure-Object -Property Length -Sum).Sum
            if($pending.Count -ge 32 -or $bytes+$length -gt 64MB){return [pscustomobject]@{Status='QUEUE_FULL';Pending=$pending.Count;Sent=$sent;Error='Local ZIP preserved; upload queue is full'}}
            Add-FmUploadQueueFile $ReportPath $queuedFile $metadata $name $hash
        }
        $remaining=@(Get-ChildItem -LiteralPath $queue -File -Filter '*.zip').Count
        foreach($old in @(Get-ChildItem -LiteralPath $queue -File -Filter '*.receipt.json'|Sort-Object LastWriteTimeUtc -Descending|Select-Object -Skip 128)){
            if($old.Name -cmatch '^[0-9a-f]{64}\.receipt\.json$'){[IO.File]::Delete($old.FullName)}
        }
        $status=if([IO.File]::Exists($receipt)){'SENT'}else{'QUEUED'}
        return [pscustomobject]@{Status=$status;Pending=$remaining;Sent=$sent;Error=$errorCode}
    } catch {return [pscustomobject]@{Status='CONFIG_ERROR';Pending=0;Sent=0;Error=$_.Exception.GetType().Name}}
    finally {
        if($temporary -and [IO.File]::Exists($temporary)){[IO.File]::Delete($temporary)}
        if($held){$mutex.ReleaseMutex()};if($mutex){$mutex.Dispose()}
    }
}
