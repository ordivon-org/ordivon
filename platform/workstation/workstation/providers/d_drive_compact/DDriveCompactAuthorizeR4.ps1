param([Parameter(Mandatory=$true)][string]$RequestPath,[int]$WaitSeconds=1500)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
function Sha([string]$p){'sha256:'+(Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLowerInvariant()}
# Parse and identify the same byte snapshot. Later rereads are currentness
# checks, not the source of the parsed evidence digest.
function Read-Evidence([string]$Path){
  $bytes=[IO.File]::ReadAllBytes($Path)
  $hash=[Security.Cryptography.SHA256]::Create()
  try {$digest='sha256:'+([BitConverter]::ToString($hash.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}finally{$hash.Dispose()}
  $utf8=New-Object Text.UTF8Encoding($false,$true)
  [pscustomobject]@{value=($utf8.GetString($bytes)|ConvertFrom-Json);digest=$digest}
}
function Is-ZeroCount($v){($v -is [int] -or $v -is [long]) -and $v -eq 0}
function Atomic-Json([string]$Path,[object]$Value){
  $tmp=$Path+'.tmp-'+$PID;$owned=$false
  $utf8=New-Object System.Text.UTF8Encoding($false)
  $bytes=$utf8.GetBytes(($Value|ConvertTo-Json -Depth 10))
  try {
    $stream=[System.IO.File]::Open($tmp,[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::Write,[System.IO.FileShare]::None)
    $owned=$true
    try {$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
    [System.IO.File]::Move($tmp,$Path)
  }finally{if($owned -and (Test-Path -LiteralPath $tmp)){Remove-Item -LiteralPath $tmp -Force}}
}
if(-not(Test-Path -LiteralPath $RequestPath -PathType Leaf)){throw "Request missing: $RequestPath"}
$requestEvidence=Read-Evidence $RequestPath;$req=$requestEvidence.value
if($req.schemaVersion -ne 3 -or $req.kind -ne 'ordivon.d-drive-compact-request'){throw 'Request schema/kind mismatch'}
if([DateTimeOffset]::UtcNow -ge [DateTimeOffset]::Parse([string]$req.expiresAtUtc)){throw 'Maintenance request expired'}
foreach($p in @([string]$req.gatePath,[string]$req.controllerPath)){if(-not(Test-Path -LiteralPath $p -PathType Leaf)){throw "Bound code missing: $p"}}
if((Sha ([string]$req.gatePath)) -ne [string]$req.gateSha256 -or (Sha ([string]$req.controllerPath)) -ne [string]$req.controllerSha256){throw 'Request code digest drift'}
$ready=[string]$req.readyPath;$terminal=[string]$req.terminalPath;$auth=[string]$req.authorizationPath
$deadline=(Get-Date).AddSeconds($WaitSeconds)
do {
  if(Test-Path -LiteralPath $terminal){$t=Get-Content -Raw -LiteralPath $terminal|ConvertFrom-Json;throw "Gate terminal before authorization: $($t.reasonCode)"}
  if(Test-Path -LiteralPath $ready){break}
  Start-Sleep -Milliseconds 250
} while((Get-Date)-lt $deadline)
if(-not(Test-Path -LiteralPath $ready)){throw 'Timed out waiting for R3 READY'}
$readyEvidence=Read-Evidence $ready;$r=$readyEvidence.value
if($r.schemaVersion -ne 3 -or $r.kind -ne 'ordivon.d-drive-compact-gate-ready' -or $r.status -ne 'ready' -or $r.maintenanceId -ne $req.maintenanceId -or ($r.admissionLockHeld -isnot [bool]) -or $r.admissionLockHeld -ne $true){throw 'R3 READY identity/state mismatch'}
if($r.gateSha256 -ne $req.gateSha256 -or $r.runtimeHealth -ne 'healthy' -or $r.integrityCheck -ne 'ok' -or $r.capacityHolders -isnot [array] -or $r.capacityHolders.Count -ne 0){throw 'R3 READY predicates do not authorize compact'}
foreach($name in @('runtimeActiveJobs','runtimeActiveReservations','runtimeHeldReservations','runtimeRecoveryRequired','violationCount','recoveryRequiredAttempts')){
  if(-not(Is-ZeroCount $r.$name)){throw "R3 READY invalid count: $name"}
}
$unit=[string]$r.unitName
$statePath=Join-Path ([string]$req.transactionDir) 'gate-state.json'
if(-not(Test-Path -LiteralPath $statePath -PathType Leaf)){throw 'R3 gate state receipt missing'}
$stateEvidence=Read-Evidence $statePath;$gs=$stateEvidence.value
if($gs.schemaVersion -ne 3 -or $gs.kind -ne 'ordivon.d-drive-compact-gate-state' -or $gs.maintenanceId -ne $req.maintenanceId -or $gs.unitName -ne $unit -or $gs.phase -ne 'READY_HELD' -or $gs.readySha256 -cne $readyEvidence.digest -or $gs.gateSha256 -cne $req.gateSha256){throw 'R3 gate state is not READY_HELD for this maintenance identity'}
$readyAt=[DateTimeOffset]::Parse([string]$r.readyAtUtc)
$readyHold=[double]$r.readyHoldSeconds
$now=[DateTimeOffset]::UtcNow
$requestExpiry=[DateTimeOffset]::Parse([string]$req.expiresAtUtc)
$readyExpiry=$readyAt.AddSeconds($readyHold)
if($readyAt -gt $now -or $readyHold -le 0 -or $now -ge $readyExpiry -or $now -ge $requestExpiry){throw 'R3 READY or request freshness rejected'}
# The grant cannot outlive either of its prerequisites.
$expires=$now.AddMinutes(3)
if($requestExpiry -lt $expires){$expires=$requestExpiry}
if($readyExpiry -lt $expires){$expires=$readyExpiry}
if(Test-Path -LiteralPath $terminal){throw 'R3 gate terminal receipt appeared before authorization commit'}
if((Sha $RequestPath) -cne $requestEvidence.digest -or (Sha $ready) -cne $readyEvidence.digest -or (Sha $statePath) -cne $stateEvidence.digest -or (Sha ([string]$req.gatePath)) -cne $req.gateSha256 -or (Sha ([string]$req.controllerPath)) -cne $req.controllerSha256){throw 'R3 authorization evidence changed before publication'}
if([DateTimeOffset]::UtcNow -ge $expires -or (Test-Path -LiteralPath $terminal)){throw 'R3 grant prerequisites expired or terminated'}
$obj=[ordered]@{schemaVersion=3;kind='ordivon.d-drive-compact-authorization';maintenanceId=[string]$req.maintenanceId;restartAuthorized=$true;compactAuthorized=$true;requestSha256=$requestEvidence.digest;readySha256=$readyEvidence.digest;gateSha256=[string]$req.gateSha256;controllerSha256=[string]$req.controllerSha256;runtimeActiveJobs=0;runtimeActiveReservations=0;runtimeHeldReservations=0;runtimeHealth='healthy';recoveryRequiredAttempts=0;distro='archlinux';vhdPath='D:\WSL\archlinux\ext4.vhdx';gateUnit=$unit;gateStateSha256=$stateEvidence.digest;issuedAtUtc=$now.ToString('o');expiresAtUtc=$expires.ToString('o');authorizationBasis='explicit current capacity-incident maintenance instruction bound to exact R3 READY receipt, READY_HELD gate-state receipt, and subsequent handoff-observed live acknowledgement'}
Atomic-Json $auth $obj
