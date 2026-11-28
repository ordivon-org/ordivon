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
function Atomic-Json([string]$Path,[object]$Value) { $tmp=$Path+'.tmp-'+$PID; $json=$Value|ConvertTo-Json -Depth 12; $utf8=New-Object System.Text.UTF8Encoding($false); $bytes=$utf8.GetBytes($json); $stream=[System.IO.File]::Open($tmp,[System.IO.FileMode]::Create,[System.IO.FileAccess]::Write,[System.IO.FileShare]::None); try {$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)} finally {$stream.Dispose()}; Move-Item -Force $tmp $Path }
function Get-WslRunning {
  $rows=@(& "$env:WINDIR\System32\wsl.exe" --list --running --quiet 2>$null)
  if($LASTEXITCODE -ne 0){throw 'WSL running-distribution census unavailable'}
  @($rows | ForEach-Object { (($_ -replace [char]0,'').Trim()) } | Where-Object { $_ })
}
function Test-Admin { return ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) }
function Test-VhdExclusiveOpen { try { $s=[IO.File]::Open($vhdPath,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None);$s.Dispose();$true } catch {$false} }
# A sparse VHDX has THREE different quantities: virtual/logical file
# length, actually allocated NTFS bytes, and free bytes on the D volume.
# Windows GetCompressedFileSizeW reports the allocated number (Win32 API).
# Keep the existing Get-VHD FileSize evidence without changing its meaning.
function Get-SparseAllocatedBytes([string]$Path) {
  if(-not ('OrdivonR3SparseAllocation' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
public static class OrdivonR3SparseAllocation {
  [DllImport("kernel32.dll", EntryPoint="GetCompressedFileSizeW", CharSet=CharSet.Unicode, SetLastError=true)]
  private static extern uint NativeAllocatedSize(string path, out uint high);
  public static long Read(string path) {
    uint high;
    uint low = NativeAllocatedSize(path, out high);
    int error = Marshal.GetLastWin32Error();
    if(low == uint.MaxValue && error != 0) throw new Win32Exception(error);
    return checked((long)(((ulong)high << 32) | low));
  }
}
'@ -ErrorAction Stop
  }
  return [int64][OrdivonR3SparseAllocation]::Read($Path)
}
function Volume-State { $vol=Get-Volume -DriveLetter D; $v=Get-VHD -Path $vhdPath; [ordered]@{freeBytes=[int64]$vol.SizeRemaining;vhdFileSize=[int64]$v.FileSize;vhdAllocatedBytes=[int64](Get-SparseAllocatedBytes $vhdPath);vhdAttached=[bool]$v.Attached} }
function Wsl-Systemctl-State([string]$Unit) { (((& "$env:WINDIR\System32\wsl.exe" -d $distro -u root -- /usr/bin/systemctl is-active $Unit 2>$null)|Out-String).Trim()) }
function Wsl-Systemctl-Enabled([string]$Unit) { (((& "$env:WINDIR\System32\wsl.exe" -d $distro -u root -- /usr/bin/systemctl is-enabled $Unit 2>$null)|Out-String).Trim()) }
function Start-ControlPlane([object]$PressureBefore) {
  & "$env:WINDIR\System32\wsl.exe" -d $distro -u root -- /bin/true | Out-Null
  & "$env:WINDIR\System32\wsl.exe" -d $distro -u root -- /usr/bin/systemctl start ordivon-runtime.service ordivon-host-v2.service ordivon-gateway.service | Out-Null
  $expectedTimerState=if($null -ne $PressureBefore -and [string]$PressureBefore.timerState -eq 'active'){'active'}else{'inactive'}
  $expectedTimerEnablement=if($null -ne $PressureBefore){[string]$PressureBefore.timerEnablement}else{'unknown'}
  if($expectedTimerState -eq 'active'){
    & "$env:WINDIR\System32\wsl.exe" -d $distro -u root -- /usr/bin/systemctl start $pressureTimer | Out-Null
  }
  $deadline=(Get-Date).AddMinutes(3)
  do {
    $runtimeState=Wsl-Systemctl-State 'ordivon-runtime.service';$hostState=Wsl-Systemctl-State 'ordivon-host-v2.service';$gatewayState=Wsl-Systemctl-State 'ordivon-gateway.service';$timerState=Wsl-Systemctl-State $pressureTimer;$timerEnablement=Wsl-Systemctl-Enabled $pressureTimer
    if($runtimeState -eq 'active' -and $hostState -eq 'active' -and $gatewayState -eq 'active' -and $timerState -eq $expectedTimerState -and $timerEnablement -eq $expectedTimerEnablement){break}
    Start-Sleep -Milliseconds 500
  } while((Get-Date)-lt $deadline)
  [ordered]@{runtime=$runtimeState;host=$hostState;gateway=$gatewayState;pressureTimer=$timerState;pressureTimerExpected=$expectedTimerState;pressureTimerEnablement=$timerEnablement;pressureTimerEnablementExpected=$expectedTimerEnablement}
}
# An acknowledgement is a typed observation of this exact handoff and gate
# state, not a filename. The legacy global shutdown requires no other distro.
function Assert-HandoffEvidence($Ack,$State,[string]$Id,[string]$Unit,[string]$ReadyDigest,[string]$HandoffDigest,[string]$GateDigest,[DateTimeOffset]$Expiry,[string[]]$Running,[string]$Target){
  if($Ack.schemaVersion -ne 3 -or $Ack.kind -cne 'ordivon.d-drive-compact-gate-handoff-observed' -or $Ack.maintenanceId -cne $Id -or $Ack.status -cne 'accepted' -or $Ack.readySha256 -cne $ReadyDigest -or $Ack.handoffSha256 -cne $HandoffDigest){throw 'Exact handoff acknowledgement rejected'}
  if($State.schemaVersion -ne 3 -or $State.kind -cne 'ordivon.d-drive-compact-gate-state' -or $State.maintenanceId -cne $Id -or $State.unitName -cne $Unit -or $State.phase -cne 'HANDOFF_HELD' -or $State.gateSha256 -cne $GateDigest -or $State.readySha256 -cne $ReadyDigest -or $State.handoffSha256 -cne $HandoffDigest){throw 'Exact HANDOFF_HELD state rejected'}
  if([DateTimeOffset]::UtcNow -ge $Expiry){throw 'Authorization expired before physical handoff'}
  if(@($Running).Count -ne 1 -or $Running[0] -cne $Target){throw 'Legacy global shutdown would affect an unqualified distro'}
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
# Never reset evidence for a reused transaction ID; recovery must reconcile
# the existing transaction rather than starting a second physical effect.
foreach($prior in @($ready,$terminal,$handoff,$authorization,$result,$optimizeOut,"$txRoot\gate-state.json","$txRoot\handoff-observed.json","$txRoot\gate-submit.json")){
  if(Test-Path -LiteralPath $prior){throw 'Existing maintenance evidence requires reconciliation'}
}
$before=Volume-State
$status='failed';$errorText=$null;$recovery=$null;$offlineEffectStarted=$false
try {
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

  $authDeadline=(Get-Date).AddSeconds($AuthorizationWaitSeconds)
  do {
    if(Test-Path -LiteralPath $authorization){break}
    if(Test-Path -LiteralPath $terminal){$t=Get-Content -Raw -LiteralPath $terminal|ConvertFrom-Json;throw "Gate terminated while waiting for authorization: $($t.reasonCode)"}
    Start-Sleep -Milliseconds 250
  } while((Get-Date)-lt $authDeadline)
  if(-not(Test-Path -LiteralPath $authorization)){throw 'Fresh authorization did not arrive while READY gate was held'}
  $a=Get-Content -Raw -LiteralPath $authorization|ConvertFrom-Json
  $authorizationDigest=Sha $authorization
  $requestPath="$root\maintenance\active-request.json"
  $gateStatePath="$txRoot\gate-state.json"
  if(-not(Test-Path -LiteralPath $requestPath -PathType Leaf) -or $a.requestSha256 -cne (Sha $requestPath)){throw 'Authorization request identity mismatch'}
  if(-not(Test-Path -LiteralPath $gateStatePath -PathType Leaf) -or $a.gateStateSha256 -cne (Sha $gateStatePath) -or $a.gateUnit -cne $unitName -or $a.distro -cne $distro -or $a.vhdPath -cne $vhdPath){throw 'Authorization state/target identity mismatch'}
  if($a.schemaVersion -ne 3 -or $a.kind -ne 'ordivon.d-drive-compact-authorization' -or $a.maintenanceId -ne $MaintenanceId -or $a.compactAuthorized -isnot [bool] -or $a.compactAuthorized -ne $true){throw 'Authorization identity/grant mismatch'}
  if($a.readySha256 -ne (Sha $ready)){throw 'Authorization is not bound to exact READY receipt'}
  if($a.gateSha256 -ne (Sha $gateWindows) -or $a.controllerSha256 -ne (Sha $controllerWindows)){throw 'Authorization code binding mismatch'}
  if([DateTimeOffset]::UtcNow -ge [DateTimeOffset]::Parse([string]$a.expiresAtUtc)){throw 'Authorization expired'}
  $handoffObj=[ordered]@{schemaVersion=3;kind='ordivon.d-drive-compact-handoff';maintenanceId=$MaintenanceId;status='offline_authorized';readySha256=(Sha $ready);authorizationSha256=(Sha $authorization);observedAtUtc=[DateTimeOffset]::UtcNow.ToString('o')}
  Atomic-Json $handoff $handoffObj
  $handoffObserved="$txRoot\handoff-observed.json";$handoffDeadline=(Get-Date).AddSeconds(15)
  do { if(Test-Path -LiteralPath $handoffObserved){break}; Start-Sleep -Milliseconds 100 } while((Get-Date)-lt $handoffDeadline)
  if(-not(Test-Path -LiteralPath $handoffObserved)){throw 'Linux gate did not acknowledge exact offline handoff'}
  $ack=Get-Content -Raw -LiteralPath $handoffObserved|ConvertFrom-Json
  $state=Get-Content -Raw -LiteralPath $gateStatePath|ConvertFrom-Json
  if((Sha $authorization) -cne $authorizationDigest -or (Sha $ready) -cne $a.readySha256 -or (Sha $requestPath) -cne $a.requestSha256 -or (Test-Path -LiteralPath $terminal)){throw 'Handoff evidence changed or terminated'}
  Assert-HandoffEvidence $ack $state $MaintenanceId $unitName $a.readySha256 (Sha $handoff) $a.gateSha256 ([DateTimeOffset]::Parse([string]$a.expiresAtUtc)) @(Get-WslRunning) $distro

  # The physical effect is host-level VHD maintenance. Shut down the complete WSL VM
  # rather than assuming a distro-only terminate releases every VHD handle.
  $offlineEffectStarted=$true
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
  if($afterCompact.vhdAllocatedBytes -gt $before.vhdAllocatedBytes){throw 'Sparse VHD allocated bytes grew during compact'}

  $recovery=Start-ControlPlane $r.pressureBefore
  if($recovery.runtime -ne 'active' -or $recovery.host -ne 'active' -or $recovery.gateway -ne 'active' -or $recovery.pressureTimer -ne $recovery.pressureTimerExpected -or $recovery.pressureTimerEnablement -ne $recovery.pressureTimerEnablementExpected){throw 'Control plane did not recover with pressure policy preserved'}
  $health=Runtime-Health
  if($health.status -ne 'healthy' -or $health.registry.recoveryRequired -ne 0 -or $health.registry.heldReservations -ne 0){throw 'Runtime health did not close cleanly after recovery'}
  $doctor=Runtime-Doctor
  if($doctor.integrityCheck -ne 'ok' -or $doctor.violationCount -ne 0 -or $doctor.summary.recoveryRequiredAttempts -ne 0){throw 'Runtime Doctor did not close cleanly after recovery'}
  $afterRestart=Volume-State
  $status='completed'
  $receipt=[ordered]@{schemaVersion=3;kind='ordivon.d-drive-offline-compact-result';status=$status;maintenanceId=$MaintenanceId;distro=$distro;vhdPath=$vhdPath;before=$before;afterCompact=$afterCompact;afterRestart=$afterRestart;reclaimedVhdBytes=[int64]($before.vhdFileSize-$afterCompact.vhdFileSize);reclaimedAllocatedVhdBytes=[int64]($before.vhdAllocatedBytes-$afterCompact.vhdAllocatedBytes);reclaimedVolumeBytes=[int64]($afterCompact.freeBytes-$before.freeBytes);readySha256=(Sha $ready);authorizationSha256=(Sha $authorization);handoffSha256=(Sha $handoff);compactMethod='Optimize-VHD Full';recovery=$recovery;runtimeHealth=[ordered]@{status=$health.status;recoveryRequired=$health.registry.recoveryRequired;heldReservations=$health.registry.heldReservations};runtimeDoctor=[ordered]@{integrityCheck=$doctor.integrityCheck;violationCount=$doctor.violationCount;recoveryRequiredAttempts=$doctor.summary.recoveryRequiredAttempts};completedAt=[DateTimeOffset]::Now.ToString('o')}
  Atomic-Json $result $receipt
  $latest="$root\d-drive-compact-result-r3-latest.json";Atomic-Json $latest $receipt
} catch {
  $errorText=$_.Exception.Message
  $recoveryAttempted=$false
  if($offlineEffectStarted){
    $recoveryAttempted=$true
    try {$recovery=Start-ControlPlane $r.pressureBefore} catch {}
  }
  $receipt=[ordered]@{schemaVersion=3;kind='ordivon.d-drive-offline-compact-result';status='failed';maintenanceId=$MaintenanceId;phase='windows-controller';error=$errorText;before=$before;offlineEffectStarted=$offlineEffectStarted;recoveryAttempted=$recoveryAttempted;recovery=$recovery;failedAt=[DateTimeOffset]::Now.ToString('o')}
  Atomic-Json $result $receipt
  throw
}
