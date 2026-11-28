$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$root='D:\OrdivonStudio';$maintenanceRoot="$root\maintenance";New-Item -ItemType Directory -Force -Path $maintenanceRoot|Out-Null
$lockPath="$root\d-drive-offline-compact-r3.request.lock";$lock=$null
try {$lock=[IO.File]::Open($lockPath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)} catch {throw 'Another R3 D-drive maintenance request is already active'}
function Sha([string]$p){'sha256:'+(Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLowerInvariant()}
function Json-Sha([object]$Value) {
  $utf8=New-Object System.Text.UTF8Encoding($false)
  $bytes=$utf8.GetBytes(($Value|ConvertTo-Json -Depth 10))
  $hash=[System.Security.Cryptography.SHA256]::Create()
  try {'sha256:'+([BitConverter]::ToString($hash.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()} finally {$hash.Dispose()}
}
function Atomic-Json([string]$Path,[object]$Value,[switch]$NoClobber) {
  $tmp=$Path+'.tmp-'+$PID;$tmpOwned=$false
  $json=$Value|ConvertTo-Json -Depth 10
  $utf8=New-Object System.Text.UTF8Encoding($false);$bytes=$utf8.GetBytes($json)
  try {
    $stream=[System.IO.File]::Open($tmp,[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::Write,[System.IO.FileShare]::None)
    $tmpOwned=$true
    try {$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)} finally {$stream.Dispose()}
    if($NoClobber){[System.IO.File]::Move($tmp,$Path)}else{Move-Item -Force $tmp $Path}
  } finally {if($tmpOwned -and (Test-Path -LiteralPath $tmp)){Remove-Item -LiteralPath $tmp -Force}}
}
$maintenanceId=('cap-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8))
$tx="$maintenanceRoot\$maintenanceId";New-Item -ItemType Directory -Force -Path $tx|Out-Null
$gate="$root\d-drive-compact-gate-r3.py";$controller="$root\d-drive-offline-compact-r3.ps1";$request="$maintenanceRoot\active-request.json";$runReceipt="$tx\run.json"
$authorizerTask='Ordivon-DDrive-Compact-Authorize'
$recoveryTaskName='Ordivon WSL Control Plane Recovery';$recoveryTaskWasEnabled=$false;$recoveryTaskSuppressed=$false;$recoveryTaskRestored=$false
$status='failed';$errorText=$null;$requestPublished=$false;$expectedRequestDigest=$null;$controllerInvoked=$false
try {
  if(Test-Path -LiteralPath $request){throw 'active-request already exists before new R3 transaction'}
  $authTask=Get-ScheduledTask -TaskName $authorizerTask -ErrorAction Stop
  if($authTask.State -eq 'Running'){
    Stop-ScheduledTask -TaskName $authorizerTask
    $authStopDeadline=(Get-Date).AddSeconds(15)
    do {Start-Sleep -Milliseconds 250;$authTask=Get-ScheduledTask -TaskName $authorizerTask} while($authTask.State -eq 'Running' -and (Get-Date)-lt $authStopDeadline)
    if($authTask.State -eq 'Running'){throw 'stale authorizer instance did not stop'}
  }
  $authBefore=(Get-ScheduledTaskInfo -TaskName $authorizerTask).LastRunTime
  $now=[DateTimeOffset]::UtcNow;$expires=$now.AddMinutes(35)
  $req=[ordered]@{schemaVersion=3;kind='ordivon.d-drive-compact-request';maintenanceId=$maintenanceId;transactionDir=$tx;readyPath="$tx\ready.json";terminalPath="$tx\gate-terminal.json";authorizationPath="$tx\authorization.json";gatePath=$gate;controllerPath=$controller;gateSha256=(Sha $gate);controllerSha256=(Sha $controller);createdAtUtc=$now.ToString('o');expiresAtUtc=$expires.ToString('o');expiresAtUnixMs=$expires.ToUnixTimeMilliseconds()}
  $expectedRequestDigest=Json-Sha $req
  Atomic-Json $request $req -NoClobber
  $requestPublished=$true
  if((Sha $request) -ne $expectedRequestDigest){throw 'published request identity mismatch'}
  $recoveryTask=Get-ScheduledTask -TaskName $recoveryTaskName -ErrorAction SilentlyContinue
  if($recoveryTask){
    $recoveryTaskWasEnabled=($recoveryTask.State -ne 'Disabled')
    if($recoveryTaskWasEnabled){Disable-ScheduledTask -TaskName $recoveryTaskName -ErrorAction Stop|Out-Null;$recoveryTaskSuppressed=$true}
    if($recoveryTask.State -eq 'Running'){Stop-ScheduledTask -TaskName $recoveryTaskName -ErrorAction Stop}
  }
  Start-ScheduledTask -TaskName $authorizerTask
  $authStartDeadline=(Get-Date).AddSeconds(10)
  do {Start-Sleep -Milliseconds 250;$authInfo=Get-ScheduledTaskInfo -TaskName $authorizerTask} while($authInfo.LastRunTime -le $authBefore -and (Get-Date)-lt $authStartDeadline)
  if($authInfo.LastRunTime -le $authBefore){throw 'fresh authorizer instance did not start'}
  $controllerInvoked=$true
  & $controller -MaintenanceId $maintenanceId
  $status='completed'
} catch {$errorText=$_.Exception.ToString();throw} finally {
  if($recoveryTaskWasEnabled){
    try {Enable-ScheduledTask -TaskName $recoveryTaskName -ErrorAction Stop|Out-Null;$recoveryTaskRestored=$true} catch {if(-not $errorText){$errorText=$_.Exception.ToString()}}
  }
  try {
    # The process owns only the request bytes it published. An external or
    # changed request, an unknown controller effect, or failed restoration
    # must remain available to the independent recovery consumer.
    $cleanup='NOT_OWNED'
    if($requestPublished){
      if(-not(Test-Path -LiteralPath $request -PathType Leaf)){$cleanup='REQUEST_MISSING_UNKNOWN'}
      elseif((Sha $request) -ne $expectedRequestDigest){$cleanup='REQUEST_CONFLICT'}
      elseif(($controllerInvoked -and $status -ne 'completed') -or ($recoveryTaskWasEnabled -and -not $recoveryTaskRestored)){$cleanup='RECONCILIATION_REQUIRED'}
      else{$cleanup='QUALIFIED'}
    }
    $receipt=[ordered]@{schemaVersion=3;kind='ordivon.d-drive-compact-run';status=$status;maintenanceId=$maintenanceId;requestSha256=$expectedRequestDigest;requestPublished=$requestPublished;controllerInvoked=$controllerInvoked;requestCleanupStanding=$cleanup;recoveryTaskName=$recoveryTaskName;recoveryTaskWasEnabled=$recoveryTaskWasEnabled;recoveryTaskSuppressed=$recoveryTaskSuppressed;recoveryTaskRestored=$recoveryTaskRestored;finishedAt=[DateTimeOffset]::UtcNow.ToString('o');error=$errorText}
    if($status -eq 'completed' -and $cleanup -ne 'QUALIFIED'){$receipt.status='reconciliation_required'}
    # Persist the exact decision before the potentially irreversible cleanup.
    Atomic-Json $runReceipt $receipt
    if($cleanup -eq 'QUALIFIED'){
      if((Test-Path -LiteralPath $request -PathType Leaf) -and (Sha $request) -eq $expectedRequestDigest){
        Remove-Item -LiteralPath $request -Force -ErrorAction Stop
        $receipt.requestCleanupStanding='REMOVED'
      }else{
        $receipt.requestCleanupStanding='REQUEST_CONFLICT'
        if($status -eq 'completed'){$receipt.status='reconciliation_required'}
      }
      Atomic-Json $runReceipt $receipt
    }
    if($status -eq 'completed' -and $receipt.requestCleanupStanding -ne 'REMOVED'){
      throw "maintenance request cleanup requires reconciliation: $($receipt.requestCleanupStanding)"
    }
  } finally {if($lock){$lock.Dispose()}}
}
