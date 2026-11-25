param([Parameter(Mandatory=$true)][string]$ControllerPath)
$ErrorActionPreference='Stop'
# Extract only the pure receipt predicate; never execute the controller.
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile($ControllerPath,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'controller parser errors'}
$fn=$ast.Find({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Assert-HandoffEvidence'},$true)
if($null -eq $fn){Write-Output 'RED exact handoff predicate missing from controller';exit 1}
. ([scriptblock]::Create($fn.Extent.Text))
$failed=0
$ready='sha256:'+'1'*64;$handoff='sha256:'+'2'*64;$code='sha256:'+'3'*64
foreach($case in @('valid','wrong-maintenance','wrong-ready','wrong-handoff','wrong-state','wrong-code','wrong-ack-kind','expired','other-distro')){
  $ack=[pscustomobject]@{schemaVersion=3;kind='ordivon.d-drive-compact-gate-handoff-observed';maintenanceId='fixture';status='accepted';readySha256=$ready;handoffSha256=$handoff}
  $state=[pscustomobject]@{schemaVersion=3;kind='ordivon.d-drive-compact-gate-state';maintenanceId='fixture';unitName='unit';phase='HANDOFF_HELD';gateSha256=$code;readySha256=$ready;handoffSha256=$handoff}
  $expiry=[DateTimeOffset]::UtcNow.AddMinutes(1);$running=@('archlinux')
  switch($case){
    'wrong-maintenance' {$ack.maintenanceId='other'}
    'wrong-ready' {$ack.readySha256='wrong'}
    'wrong-handoff' {$ack.handoffSha256='wrong'}
    'wrong-state' {$state.phase='READY_HELD'}
    'wrong-code' {$state.gateSha256='wrong'}
    'wrong-ack-kind' {$ack.kind='unrelated'}
    'expired' {$expiry=[DateTimeOffset]::UtcNow.AddSeconds(-1)}
    'other-distro' {$running+= 'OrdivonSparseLabR1'}
  }
  $threw=$false
  try {Assert-HandoffEvidence $ack $state 'fixture' 'unit' $ready $handoff $code $expiry $running 'archlinux'}catch{$threw=$true}
  if(($case -eq 'valid' -and $threw) -or ($case -ne 'valid' -and -not $threw)){Write-Output "FAIL $case";$failed++}else{Write-Output "PASS $case"}
}
if($failed){exit 1}
