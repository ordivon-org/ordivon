param([Parameter(Mandatory=$true)][string]$AuthorizerPath)
$ErrorActionPreference='Stop'
function Sha([string]$p){'sha256:'+(Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLowerInvariant()}
function Put([string]$p,[object]$v){[IO.File]::WriteAllText($p,($v|ConvertTo-Json -Depth 10),(New-Object Text.UTF8Encoding($false)))}
$failed=0
foreach($case in @('valid','wrong-ready-digest','wrong-state-code','coerced-count','missing-count','future-ready','expired-request','old-authorization')){
  $root=Join-Path ([IO.Path]::GetTempPath()) ('ordivon-r4-auth-test-'+[guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Path $root|Out-Null
  try {
    $gate=Join-Path $root 'gate.py';$controller=Join-Path $root 'controller.ps1'
    [IO.File]::WriteAllText($gate,'synthetic gate never executed')
    [IO.File]::WriteAllText($controller,'synthetic controller never executed')
    $request=Join-Path $root 'request.json';$ready=Join-Path $root 'ready.json'
    $state=Join-Path $root 'gate-state.json';$auth=Join-Path $root 'authorization.json'
    $now=[DateTimeOffset]::UtcNow
    $req=[ordered]@{schemaVersion=3;kind='ordivon.d-drive-compact-request';maintenanceId='fixture-1';transactionDir=$root;readyPath=$ready;terminalPath=(Join-Path $root 'terminal.json');authorizationPath=$auth;gatePath=$gate;controllerPath=$controller;gateSha256=(Sha $gate);controllerSha256=(Sha $controller);createdAtUtc=$now.AddSeconds(-2).ToString('o');expiresAtUtc=$now.AddMinutes(2).ToString('o')}
    $r=[ordered]@{schemaVersion=3;kind='ordivon.d-drive-compact-gate-ready';maintenanceId='fixture-1';status='ready';admissionLockHeld=$true;gateSha256=$req.gateSha256;runtimeHealth='healthy';runtimeActiveJobs=0;runtimeActiveReservations=0;runtimeHeldReservations=0;runtimeRecoveryRequired=0;integrityCheck='ok';violationCount=0;recoveryRequiredAttempts=0;capacityHolders=@();unitName='fixture-unit';readyAtUtc=$now.ToString('o');readyHoldSeconds=120}
    switch($case){
      'coerced-count' {$r.runtimeActiveJobs=$false}
      'missing-count' {$r.Remove('runtimeActiveJobs')}
      'future-ready' {$r.readyAtUtc=$now.AddMinutes(20).ToString('o')}
      'expired-request' {$req.expiresAtUtc=$now.AddSeconds(-1).ToString('o')}
    }
    Put $request $req;Put $ready $r
    $gs=[ordered]@{schemaVersion=3;kind='ordivon.d-drive-compact-gate-state';maintenanceId='fixture-1';unitName='fixture-unit';phase='READY_HELD';gateSha256=$req.gateSha256;readySha256=(Sha $ready);observedAtUtc=$now.ToString('o')}
    if($case -eq 'wrong-ready-digest'){$gs.readySha256='sha256:'+'0'*64}
    if($case -eq 'wrong-state-code'){$gs.gateSha256='sha256:'+'0'*64}
    Put $state $gs
    if($case -eq 'old-authorization'){[IO.File]::WriteAllText($auth,'existing authorization bytes')}
    $threw=$false
    try {& $AuthorizerPath -RequestPath $request -WaitSeconds 1|Out-Null} catch {$threw=$true}
    if($case -eq 'valid'){
      if($threw -or -not(Test-Path $auth)){throw 'valid exact evidence rejected'}
      $a=Get-Content -Raw $auth|ConvertFrom-Json
      if($a.readySha256 -ne (Sha $ready) -or $a.gateStateSha256 -ne (Sha $state)){throw 'wrong evidence binding'}
    }elseif($case -eq 'old-authorization'){
      if(-not $threw -or [IO.File]::ReadAllText($auth) -ne 'existing authorization bytes'){throw 'old authorization overwritten'}
    }else{
      if(-not $threw -or (Test-Path $auth)){throw 'invalid evidence authorized'}
    }
    Write-Output "PASS $case"
  } catch {$failed++;Write-Output "FAIL $case : $($_.Exception.Message)"} finally {Remove-Item -LiteralPath $root -Recurse -Force}
}
if($failed){exit 1}
