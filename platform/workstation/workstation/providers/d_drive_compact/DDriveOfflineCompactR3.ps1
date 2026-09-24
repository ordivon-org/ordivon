param(
  [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$')][string]$MaintenanceId,
  [Parameter(Mandatory=$false)][int]$GateWaitSeconds = 1500,
  [Parameter(Mandatory=$false)][int]$AuthorizationWaitSeconds = 240
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = 'D:\OrdivonStudio'
$distro = 'archlinux'
$vhdPath = 'D:\WSL\archlinux\ext4.vhdx'
$gateWindows = "$root\d-drive-compact-gate-r3.py"
$gateLinux = '/mnt/d/OrdivonStudio/d-drive-compact-gate-r3.py'
$controllerWindows = "$root\d-drive-offline-compact-r3.ps1"
$txRoot = "$root\maintenance\$MaintenanceId"
$ready = "$txRoot\ready.json"
$terminal = "$txRoot\gate-terminal.json"
$handoff = "$txRoot\handoff.json"
$authorization = "$txRoot\authorization.json"
$result = "$txRoot\result.json"
$optimizeOut = "$txRoot\optimize-vhd.txt"
$unitName = "ordivon-d-drive-compact-gate-$MaintenanceId"
$pressureTimer = 'ordivon-runtime-storage-pressure.timer'
$pressureService = 'ordivon-runtime-storage-pressure.service'

function Sha([string]$Path) { return ('sha256:' + (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()) }
function Atomic-Json([string]$Path,[object]$Value) { $tmp=$Path+'.tmp-'+$PID; $Value|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $tmp -Encoding UTF8; Move-Item -Force $tmp $Path }
function Get-WslRunning { @(& "$env:WINDIR\System32\wsl.exe" --list --running --quiet 2>$null | ForEach-Object { (($_ -replace [char]0,'').Trim()) } | Where-Object { $_ }) }
function Test-Admin { return ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) }
function Test-VhdExclusiveOpen { try { $s=[IO.File]::Open($vhdPath,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None);$s.Dispose();$true } catch {$false} }
function Volume-State { $vol=Get-Volume -DriveLetter D; $v=Get-VHD -Path $vhdPath; [ordered]@{freeBytes=[int64]$vol.SizeRemaining;vhdFileSize=[int64]$v.FileSize;vhdAttached=[bool]$v.Attached} }
function Wsl-Systemctl-State([string]$Unit) { (((& "$env:WINDIR\System32\wsl.exe" -d $distro -u root -- /usr/bin/systemctl is-active $Unit 2>$null)|Out-String).Trim()) }
function Start-ControlPlane {
  & "$env:WINDIR\System32\wsl.exe" -d $distro -u root -- /bin/true | Out-Null
  & "$env:WINDIR\System32\wsl.exe" -d $distro -u root -- /usr/bin/systemctl start ordivon-runtime.service ordivon-host-v2.service ordivon-gateway.service | Out-Null
  & "$env:WINDIR\System32\wsl.exe" -d $distro -u root -- /usr/bin/systemctl enable --now $pressureTimer | Out-Null
  & "$env:WINDIR\System32\wsl.exe" -d $distro -u root -- /usr/bin/systemctl start --no-block $pressureService | Out-Null
  $deadline=(Get-Date).AddMinutes(3)
  do {
    $runtime=Wsl-Systemctl-State 'ordivon-runtime.service';$host=Wsl-Systemctl-State 'ordivon-host-v2.service';$gateway=Wsl-Systemctl-State 'ordivon-gateway.service';$timer=Wsl-Systemctl-State $pressureTimer
    if($runtime -eq 'active' -and $host -eq 'active' -and $gateway -eq 'active' -and $timer -eq 'active'){break}
    Start-Sleep -Milliseconds 500
  } while((Get-Date)-lt $deadline)
  [ordered]@{runtime=$runtime;host=$host;gateway=$gateway;pressureTimer=$timer}
}
function Runtime-Health {
  $raw=(((& "$env:WINDIR\System32\wsl.exe" -d $distro -u root -- /usr/local/libexec/ordivon/ordivon-runtime-status --health --json 2>$null)|Out-String)); if([string]::IsNullOrWhiteSpace($raw)){throw 'Runtime health returned no JSON'}; $raw|ConvertFrom-Json
}
function Runtime-Doctor {
  $raw=(((& "$env:WINDIR\System32\wsl.exe" -d $distro -u root -- /usr/local/libexec/ordivon/ordivon-runtime-doctor inspect --database /var/lib/ordivon/registry/registry.sqlite3 --store-root /var/lib/ordivon/runtime --pretty --fail-on-violation 2>$null)|Out-String)); if([string]::IsNullOrWhiteSpace($raw)){throw 'Runtime Doctor returned no JSON'}; $raw|ConvertFrom-Json
}

if(-not(Test-Admin)){throw 'Administrator token required'}
if(-not(Test-Path -LiteralPath $gateWindows -PathType Leaf)){throw "Gate missing: $gateWindows"}
if(-not(Test-Path -LiteralPath $controllerWindows -PathType Leaf)){throw "Controller missing: $controllerWindows"}
if(-not(Test-Path -LiteralPath $vhdPath -PathType Leaf)){throw "VHD missing: $vhdPath"}
New-Item -ItemType Directory -Force -Path $txRoot | Out-Null
$before=Volume-State
$status='failed';$errorText=$null;$recovery=$null
try {
  Remove-Item $ready,$terminal,$handoff,$authorization,$result,$optimizeOut -Force -ErrorAction SilentlyContinue
  $unitArg = ('--unit={0}' -f $unitName)
  $txLinux = ('/mnt/d/OrdivonStudio/maintenance/{0}' -f $MaintenanceId)
  $gateArgs=@('-d',$distro,'-u','root','--','/usr/bin/systemd-run',$unitArg,'--collect','--property=Type=exec','--','/usr/bin/python3',$gateLinux,'--maintenance-id',$MaintenanceId,'--unit-name',$unitName,'--transaction-root',$txLinux)
  $savedErrorActionPreference=$ErrorActionPreference
  $ErrorActionPreference='Continue'
  $submitOutput=((& "$env:WINDIR\System32\wsl.exe" @gateArgs 2>&1)|Out-String)
  $submitRc=$LASTEXITCODE
  $ErrorActionPreference=$savedErrorActionPreference
  Atomic-Json "$txRoot\gate-submit.json" ([ordered]@{schemaVersion=3;kind='ordivon.d-drive-compact-gate-submit';maintenanceId=$MaintenanceId;unitName=$unitName;rc=$submitRc;output=$submitOutput;observedAt=[DateTimeOffset]::Now.ToString('o')})
  if($submitRc -ne 0){throw "systemd-run gate submission failed rc=$submitRc output=$($submitOutput.Trim())"}

  $gateDeadline=(Get-Date).AddSeconds($GateWaitSeconds)
  do {
    if(Test-Path -LiteralPath $terminal){$t=Get-Content -Raw -LiteralPath $terminal|ConvertFrom-Json;throw "Gate rejected phase=$($t.phase) reasonCode=$($t.reasonCode): $($t.detail)"}
    if(Test-Path -LiteralPath $ready){break}
    $state=Wsl-Systemctl-State "$unitName.service"
    if($state -notin @('active','activating')){throw "Gate unit left active state before READY: $state"}
    Start-Sleep -Milliseconds 250
  } while((Get-Date)-lt $gateDeadline)
  if(-not(Test-Path -LiteralPath $ready)){throw 'Gate wait deadline exceeded without READY/terminal receipt'}
  $r=Get-Content -Raw -LiteralPath $ready|ConvertFrom-Json
  if($r.schemaVersion -ne 3 -or $r.kind -ne 'ordivon.d-drive-compact-gate-ready' -or $r.maintenanceId -ne $MaintenanceId -or $r.status -ne 'ready' -or $r.admissionLockHeld -ne $true){throw 'READY receipt identity/state mismatch'}
  if($r.gateSha256 -ne (Sha $gateWindows)){throw 'READY gate digest mismatch'}
  if($r.runtimeHealth -ne 'healthy' -or $r.runtimeActiveJobs -ne 0 -or $r.runtimeActiveReservations -ne 0 -or $r.runtimeHeldReservations -ne 0 -or $r.runtimeRecoveryRequired -ne 0){throw 'READY does not bind a zero-holder healthy Runtime'}
  foreach($u in @('ordivon-runtime.service','ordivon-host-v2.service','ordivon-gateway.service')){
    $property = $r.services.PSObject.Properties[$u]
    $observed = if($null -ne $property){[string]$property.Value}else{'missing'}
    if($observed -ne 'active'){throw "READY control-plane state rejected: $u=$observed"}
  }
  if((Wsl-Systemctl-State "$unitName.service") -ne 'active'){throw 'Gate unit is not active while READY is consumed'}

  $authDeadline=(Get-Date).AddSeconds($AuthorizationWaitSeconds)
  do {
    if(Test-Path -LiteralPath $authorization){break}
    if(Test-Path -LiteralPath $terminal){$t=Get-Content -Raw -LiteralPath $terminal|ConvertFrom-Json;throw "Gate terminated while waiting for authorization: $($t.reasonCode)"}
    Start-Sleep -Milliseconds 250
  } while((Get-Date)-lt $authDeadline)
  if(-not(Test-Path -LiteralPath $authorization)){throw 'Fresh authorization did not arrive while READY gate was held'}
  $a=Get-Content -Raw -LiteralPath $authorization|ConvertFrom-Json
  if($a.schemaVersion -ne 3 -or $a.kind -ne 'ordivon.d-drive-compact-authorization' -or $a.maintenanceId -ne $MaintenanceId -or $a.compactAuthorized -ne $true){throw 'Authorization identity/grant mismatch'}
  if($a.readySha256 -ne (Sha $ready)){throw 'Authorization is not bound to exact READY receipt'}
  if($a.gateSha256 -ne (Sha $gateWindows) -or $a.controllerSha256 -ne (Sha $controllerWindows)){throw 'Authorization code binding mismatch'}
  if([DateTimeOffset]::UtcNow -ge [DateTimeOffset]::Parse([string]$a.expiresAtUtc)){throw 'Authorization expired'}
  if((Wsl-Systemctl-State "$unitName.service") -ne 'active'){throw 'Gate unit lost before offline handoff'}

  $handoffObj=[ordered]@{schemaVersion=3;kind='ordivon.d-drive-compact-handoff';maintenanceId=$MaintenanceId;status='offline_authorized';readySha256=(Sha $ready);authorizationSha256=(Sha $authorization);observedAtUtc=[DateTimeOffset]::UtcNow.ToString('o')}
  Atomic-Json $handoff $handoffObj
  $handoffObserved="$txRoot\handoff-observed.json";$handoffDeadline=(Get-Date).AddSeconds(15)
  do { if(Test-Path -LiteralPath $handoffObserved){break}; Start-Sleep -Milliseconds 100 } while((Get-Date)-lt $handoffDeadline)
  if(-not(Test-Path -LiteralPath $handoffObserved)){throw 'Linux gate did not acknowledge exact offline handoff'}

  # The physical effect is host-level VHD maintenance. Shut down the complete WSL VM
  # rather than assuming a distro-only terminate releases every VHD handle.
  & "$env:WINDIR\System32\wsl.exe" --shutdown | Out-Null
  if($LASTEXITCODE -ne 0){throw "wsl --shutdown failed rc=$LASTEXITCODE"}
  $stopDeadline=(Get-Date).AddSeconds(90)
  do { $running=Get-WslRunning; if(-not($running -contains $distro)){break}; Start-Sleep -Milliseconds 250 } while((Get-Date)-lt $stopDeadline)
  if($running -contains $distro){throw 'archlinux still running after terminate'}
  $exclusiveDeadline=(Get-Date).AddSeconds(90);$exclusive=$false
  do {$exclusive=Test-VhdExclusiveOpen;if($exclusive){break};Start-Sleep -Milliseconds 250}while((Get-Date)-lt $exclusiveDeadline)
  if(-not $exclusive){throw 'VHD never became exclusively openable'}
  $vhd=Get-VHD -Path $vhdPath
  if($vhd.Attached){throw 'Get-VHD still reports Attached=True after WSL termination'}

  try { Optimize-VHD -Path $vhdPath -Mode Full -ErrorAction Stop | Out-String | Set-Content -LiteralPath $optimizeOut -Encoding UTF8 } catch { $_|Out-String|Set-Content -LiteralPath $optimizeOut -Encoding UTF8; throw }
  $afterCompact=Volume-State
  if($afterCompact.vhdFileSize -gt $before.vhdFileSize){throw 'VHD grew during compact'}

  $recovery=Start-ControlPlane
  if($recovery.runtime -ne 'active' -or $recovery.host -ne 'active' -or $recovery.gateway -ne 'active' -or $recovery.pressureTimer -ne 'active'){throw 'Control plane did not recover'}
  $health=Runtime-Health
  if($health.status -ne 'healthy' -or $health.registry.recoveryRequired -ne 0 -or $health.registry.heldReservations -ne 0){throw 'Runtime health did not close cleanly after recovery'}
  $doctor=Runtime-Doctor
  if($doctor.integrityCheck -ne 'ok' -or $doctor.violationCount -ne 0 -or $doctor.summary.recoveryRequiredAttempts -ne 0){throw 'Runtime Doctor did not close cleanly after recovery'}
  $afterRestart=Volume-State
  $status='completed'
  $receipt=[ordered]@{schemaVersion=3;kind='ordivon.d-drive-offline-compact-result';status=$status;maintenanceId=$MaintenanceId;distro=$distro;vhdPath=$vhdPath;before=$before;afterCompact=$afterCompact;afterRestart=$afterRestart;reclaimedVhdBytes=[int64]($before.vhdFileSize-$afterCompact.vhdFileSize);reclaimedVolumeBytes=[int64]($afterCompact.freeBytes-$before.freeBytes);readySha256=(Sha $ready);authorizationSha256=(Sha $authorization);handoffSha256=(Sha $handoff);compactMethod='Optimize-VHD Full';recovery=$recovery;runtimeHealth=[ordered]@{status=$health.status;recoveryRequired=$health.registry.recoveryRequired;heldReservations=$health.registry.heldReservations};runtimeDoctor=[ordered]@{integrityCheck=$doctor.integrityCheck;violationCount=$doctor.violationCount;recoveryRequiredAttempts=$doctor.summary.recoveryRequiredAttempts};completedAt=[DateTimeOffset]::Now.ToString('o')}
  Atomic-Json $result $receipt
  $latest="$root\d-drive-compact-result-r3-latest.json";Atomic-Json $latest $receipt
} catch {
  $errorText=$_.Exception.Message
  try {$recovery=Start-ControlPlane} catch {}
  $receipt=[ordered]@{schemaVersion=3;kind='ordivon.d-drive-offline-compact-result';status='failed';maintenanceId=$MaintenanceId;phase='windows-controller';error=$errorText;before=$before;recovery=$recovery;failedAt=[DateTimeOffset]::Now.ToString('o')}
  Atomic-Json $result $receipt
  throw
}
