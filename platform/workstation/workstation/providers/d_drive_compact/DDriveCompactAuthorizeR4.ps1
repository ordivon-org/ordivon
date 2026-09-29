param([Parameter(Mandatory=$true)][string]$RequestPath,[int]$WaitSeconds=1500)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
function Sha([string]$p){'sha256:'+(Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLowerInvariant()}
function Atomic-Json([string]$Path,[object]$Value) {$tmp=$Path+'.tmp-'+$PID; $json=$Value|ConvertTo-Json -Depth 10; $utf8=New-Object System.Text.UTF8Encoding($false); $bytes=$utf8.GetBytes($json); $stream=[System.IO.File]::Open($tmp,[System.IO.FileMode]::Create,[System.IO.FileAccess]::Write,[System.IO.FileShare]::None); try {$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)} finally {$stream.Dispose()}; Move-Item -Force $tmp $Path }
if(-not(Test-Path -LiteralPath $RequestPath -PathType Leaf)){throw "Request missing: $RequestPath"}
$req=Get-Content -Raw -LiteralPath $RequestPath|ConvertFrom-Json
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
$r=Get-Content -Raw -LiteralPath $ready|ConvertFrom-Json
if($r.schemaVersion -ne 3 -or $r.kind -ne 'ordivon.d-drive-compact-gate-ready' -or $r.status -ne 'ready' -or $r.maintenanceId -ne $req.maintenanceId -or $r.admissionLockHeld -ne $true){throw 'R3 READY identity/state mismatch'}
if($r.gateSha256 -ne $req.gateSha256 -or $r.runtimeHealth -ne 'healthy' -or $r.runtimeActiveJobs -ne 0 -or $r.runtimeActiveReservations -ne 0 -or $r.runtimeHeldReservations -ne 0 -or $r.runtimeRecoveryRequired -ne 0 -or $r.integrityCheck -ne 'ok' -or $r.violationCount -ne 0 -or $r.recoveryRequiredAttempts -ne 0 -or @($r.capacityHolders).Count -ne 0){throw 'R3 READY predicates do not authorize compact'}
$unit=[string]$r.unitName
$statePath=Join-Path ([string]$req.transactionDir) 'gate-state.json'
if(-not(Test-Path -LiteralPath $statePath -PathType Leaf)){throw 'R3 gate state receipt missing'}
$gs=Get-Content -Raw -LiteralPath $statePath|ConvertFrom-Json
if($gs.schemaVersion -ne 3 -or $gs.kind -ne 'ordivon.d-drive-compact-gate-state' -or $gs.maintenanceId -ne $req.maintenanceId -or $gs.unitName -ne $unit -or $gs.phase -ne 'READY_HELD'){throw 'R3 gate state is not READY_HELD for this maintenance identity'}
$readyAt=[DateTimeOffset]::Parse([string]$r.readyAtUtc)
$readyHold=[double]$r.readyHoldSeconds
if([DateTimeOffset]::UtcNow -ge $readyAt.AddSeconds($readyHold)){throw 'R3 READY hold window expired'}
if(Test-Path -LiteralPath $terminal){throw 'R3 gate terminal receipt appeared before authorization commit'}
$obj=[ordered]@{schemaVersion=3;kind='ordivon.d-drive-compact-authorization';maintenanceId=[string]$req.maintenanceId;restartAuthorized=$true;compactAuthorized=$true;readySha256=(Sha $ready);gateSha256=[string]$req.gateSha256;controllerSha256=[string]$req.controllerSha256;runtimeActiveJobs=0;runtimeActiveReservations=0;runtimeHeldReservations=0;runtimeHealth='healthy';recoveryRequiredAttempts=0;distro='archlinux';vhdPath='D:\WSL\archlinux\ext4.vhdx';gateUnit=$unit;gateStateSha256=(Sha $statePath);issuedAtUtc=[DateTimeOffset]::UtcNow.ToString('o');expiresAtUtc=[DateTimeOffset]::UtcNow.AddMinutes(3).ToString('o');authorizationBasis='explicit current capacity-incident maintenance instruction bound to exact R3 READY receipt, READY_HELD gate-state receipt, and subsequent handoff-observed live acknowledgement'}
Atomic-Json $auth $obj
