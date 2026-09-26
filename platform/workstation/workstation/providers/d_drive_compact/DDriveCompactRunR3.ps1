$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$root='D:\OrdivonStudio';$maintenanceRoot="$root\maintenance";New-Item -ItemType Directory -Force -Path $maintenanceRoot|Out-Null
$lockPath="$root\d-drive-offline-compact-r3.request.lock";$lock=$null
try {$lock=[IO.File]::Open($lockPath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)} catch {throw 'Another R3 D-drive maintenance request is already active'}
function Sha([string]$p){'sha256:'+(Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLowerInvariant()}
function Atomic-Json([string]$Path,[object]$Value) {$tmp=$Path+'.tmp-'+$PID; $json=$Value|ConvertTo-Json -Depth 10; $utf8=New-Object System.Text.UTF8Encoding($false); $bytes=$utf8.GetBytes($json); $stream=[System.IO.File]::Open($tmp,[System.IO.FileMode]::Create,[System.IO.FileAccess]::Write,[System.IO.FileShare]::None); try {$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)} finally {$stream.Dispose()}; Move-Item -Force $tmp $Path }
$maintenanceId=('cap-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8))
$tx="$maintenanceRoot\$maintenanceId";New-Item -ItemType Directory -Force -Path $tx|Out-Null
$gate="$root\d-drive-compact-gate-r3.py";$controller="$root\d-drive-offline-compact-r3.ps1";$request="$maintenanceRoot\active-request.json";$runReceipt="$tx\run.json"
$authorizerTask='Ordivon-DDrive-Compact-Authorize'
$status='failed';$errorText=$null
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
  $req=[ordered]@{schemaVersion=3;kind='ordivon.d-drive-compact-request';maintenanceId=$maintenanceId;transactionDir=$tx;readyPath="$tx\ready.json";terminalPath="$tx\gate-terminal.json";authorizationPath="$tx\authorization.json";gatePath=$gate;controllerPath=$controller;gateSha256=(Sha $gate);controllerSha256=(Sha $controller);createdAtUtc=[DateTimeOffset]::UtcNow.ToString('o');expiresAtUtc=[DateTimeOffset]::UtcNow.AddMinutes(35).ToString('o')}
  Atomic-Json $request $req
  Start-ScheduledTask -TaskName $authorizerTask
  $authStartDeadline=(Get-Date).AddSeconds(10)
  do {Start-Sleep -Milliseconds 250;$authInfo=Get-ScheduledTaskInfo -TaskName $authorizerTask} while($authInfo.LastRunTime -le $authBefore -and (Get-Date)-lt $authStartDeadline)
  if($authInfo.LastRunTime -le $authBefore){throw 'fresh authorizer instance did not start'}
  & $controller -MaintenanceId $maintenanceId
  $status='completed'
} catch {$errorText=$_.Exception.ToString();throw} finally {
  Atomic-Json $runReceipt ([ordered]@{schemaVersion=3;kind='ordivon.d-drive-compact-run';status=$status;maintenanceId=$maintenanceId;requestSha256=if(Test-Path $request){Sha $request}else{$null};finishedAt=[DateTimeOffset]::Now.ToString('o');error=$errorText})
  Remove-Item -LiteralPath $request -Force -ErrorAction SilentlyContinue
  if($lock){$lock.Dispose()}
}
