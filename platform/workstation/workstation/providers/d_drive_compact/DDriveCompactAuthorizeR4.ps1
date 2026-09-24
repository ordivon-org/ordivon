param([Parameter(Mandatory=$true)][string]$RequestPath,[int]$WaitSeconds=1500)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
function Sha([string]$p){'sha256:'+(Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLowerInvariant()}
function Atomic-Json([string]$Path,[object]$Value){$tmp=$Path+'.tmp-'+$PID;$Value|ConvertTo-Json -Depth 10|Set-Content -LiteralPath $tmp -Encoding UTF8;Move-Item -Force $tmp $Path}
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
$state=(((& "$env:WINDIR\System32\wsl.exe" -d 'archlinux' -u root -- /usr/bin/systemctl is-active ($unit+'.service') 2>$null)|Out-String).Trim())
if($state -ne 'active'){throw "R3 gate unit is not active: $state"}
$obj=[ordered]@{schemaVersion=3;kind='ordivon.d-drive-compact-authorization';maintenanceId=[string]$req.maintenanceId;restartAuthorized=$true;compactAuthorized=$true;readySha256=(Sha $ready);gateSha256=[string]$req.gateSha256;controllerSha256=[string]$req.controllerSha256;runtimeActiveJobs=0;runtimeActiveReservations=0;runtimeHeldReservations=0;runtimeHealth='healthy';recoveryRequiredAttempts=0;distro='archlinux';vhdPath='D:\WSL\archlinux\ext4.vhdx';gateUnit=$unit;issuedAtUtc=[DateTimeOffset]::UtcNow.ToString('o');expiresAtUtc=[DateTimeOffset]::UtcNow.AddMinutes(3).ToString('o');authorizationBasis='explicit current capacity-incident maintenance instruction bound to exact R3 READY receipt and live gate unit'}
Atomic-Json $auth $obj
