$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$root='D:\OrdivonStudio';$maintenanceRoot="$root\maintenance";New-Item -ItemType Directory -Force -Path $maintenanceRoot|Out-Null
$lockPath="$root\d-drive-offline-compact-r3.request.lock";$lock=$null
try {$lock=[IO.File]::Open($lockPath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)} catch {throw 'Another R3 D-drive maintenance request is already active'}
function Sha([string]$p){'sha256:'+(Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLowerInvariant()}
function Atomic-Json([string]$Path,[object]$Value){$tmp=$Path+'.tmp-'+$PID;$Value|ConvertTo-Json -Depth 10|Set-Content -LiteralPath $tmp -Encoding UTF8;Move-Item -Force $tmp $Path}
$maintenanceId=('cap-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8))
$tx="$maintenanceRoot\$maintenanceId";New-Item -ItemType Directory -Force -Path $tx|Out-Null
$gate="$root\d-drive-compact-gate-r3.py";$controller="$root\d-drive-offline-compact-r3.ps1";$request="$maintenanceRoot\active-request.json";$runReceipt="$tx\run.json"
$status='failed';$errorText=$null
try {
  $req=[ordered]@{schemaVersion=3;kind='ordivon.d-drive-compact-request';maintenanceId=$maintenanceId;transactionDir=$tx;readyPath="$tx\ready.json";terminalPath="$tx\gate-terminal.json";authorizationPath="$tx\authorization.json";gatePath=$gate;controllerPath=$controller;gateSha256=(Sha $gate);controllerSha256=(Sha $controller);createdAtUtc=[DateTimeOffset]::UtcNow.ToString('o');expiresAtUtc=[DateTimeOffset]::UtcNow.AddMinutes(35).ToString('o')}
  Atomic-Json $request $req
  Start-ScheduledTask -TaskName 'Ordivon-DDrive-Compact-Authorize'
  & $controller -MaintenanceId $maintenanceId
  $status='completed'
} catch {$errorText=$_.Exception.ToString();throw} finally {
  Atomic-Json $runReceipt ([ordered]@{schemaVersion=3;kind='ordivon.d-drive-compact-run';status=$status;maintenanceId=$maintenanceId;requestSha256=if(Test-Path $request){Sha $request}else{$null};finishedAt=[DateTimeOffset]::Now.ToString('o');error=$errorText})
  Remove-Item -LiteralPath $request -Force -ErrorAction SilentlyContinue
  if($lock){$lock.Dispose()}
}
