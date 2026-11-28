param([Parameter(Mandatory=$true)][string]$RunnerPath)
$ErrorActionPreference='Stop'
$source=Get-Content -Raw -LiteralPath $RunnerPath
$marker='$root=''D:\OrdivonStudio'''
if(-not $source.Contains($marker)){throw 'expected exact original root binding'}
$source=$source.Replace($marker,'$root=$env:ORDIVON_R3_TEST_ROOT')
$runner=[scriptblock]::Create($source)
$script:scenario=''
$script:tick=0
$script:scheduledCalls=0

# Stub all ScheduledTask effects. No real WSL, VHD or scheduled task calls.
function Get-ScheduledTask {param([string]$TaskName)
  if($TaskName -eq 'Ordivon WSL Control Plane Recovery'){
    $state=if($script:scenario -eq 'restore-fails'){'Ready'}else{'Disabled'}
    return [pscustomobject]@{State=$state}
  }
  [pscustomobject]@{State='Ready'}
}
function Get-ScheduledTaskInfo {param([string]$TaskName)
  $script:tick++
  if($script:scenario -eq 'publish-race' -and $script:tick -eq 1){
    [IO.File]::WriteAllText($env:ORDIVON_R3_TEST_REQUEST,'racing active request bytes')
  }
  [pscustomobject]@{LastRunTime=[datetime]::UtcNow.AddSeconds($script:tick)}
}
function Start-ScheduledTask {param([string]$TaskName)
  $script:scheduledCalls++
  if($script:scenario -eq 'precontroller-fails'){throw 'synthetic authorizer start failure'}
}
function Stop-ScheduledTask {param([string]$TaskName) $script:scheduledCalls++}
function Disable-ScheduledTask {param([string]$TaskName) $script:scheduledCalls++}
function Enable-ScheduledTask {param([string]$TaskName)
  $script:scheduledCalls++
  if($script:scenario -eq 'restore-fails'){throw 'synthetic recovery restore failure'}
}
function Assert-True([bool]$Condition,[string]$Message) {if(-not $Condition){throw $Message}}

$failed=0
foreach($case in @('foreign','controller-fails','replacement','publish-race','restore-fails','precontroller-fails','success')){
  $script:scenario=$case;$script:tick=0;$script:scheduledCalls=0
  $root=Join-Path ([IO.Path]::GetTempPath()) ('ordivon-r3-runner-test-'+[guid]::NewGuid().ToString('N'))
  $env:ORDIVON_R3_TEST_ROOT=$root
  $env:ORDIVON_R3_TEST_CASE=$case
  $maintenance=Join-Path $root 'maintenance'
  New-Item -ItemType Directory -Force -Path $maintenance|Out-Null
  $request=Join-Path $maintenance 'active-request.json'
  $env:ORDIVON_R3_TEST_REQUEST=$request
  $gate=Join-Path $root 'd-drive-compact-gate-r3.py'
  $controller=Join-Path $root 'd-drive-offline-compact-r3.ps1'
  [IO.File]::WriteAllText($gate,'synthetic gate fixture, never executed')
  [IO.File]::WriteAllText($controller,@'
param([string]$MaintenanceId)
if($env:ORDIVON_R3_TEST_CASE -eq 'controller-fails'){throw 'synthetic unknown controller result'}
if($env:ORDIVON_R3_TEST_CASE -eq 'replacement'){
  [IO.File]::WriteAllText($env:ORDIVON_R3_TEST_REQUEST,'replacement request bytes')
}
'@)
  if($case -eq 'foreign'){[IO.File]::WriteAllText($request,'previous active request bytes')}
  try {
    $threw=$false
    try {& $runner|Out-Null} catch {$threw=$true}
    switch($case){
      'foreign' {
        Assert-True $threw 'existing request must block the runner'
        Assert-True (Test-Path -LiteralPath $request -PathType Leaf) 'existing request was deleted'
        Assert-True (([IO.File]::ReadAllText($request)) -eq 'previous active request bytes') 'existing request changed'
        Assert-True ($script:scheduledCalls -eq 0) 'foreign request must not trigger scheduler effects'
      }
      'controller-fails' {
        Assert-True $threw 'controller failure must not report success'
        Assert-True (Test-Path -LiteralPath $request -PathType Leaf) 'unknown controller effect lost its request'
      }
      'replacement' {
        Assert-True (Test-Path -LiteralPath $request -PathType Leaf) 'replacement request was deleted'
        Assert-True (([IO.File]::ReadAllText($request)) -eq 'replacement request bytes') 'replacement request changed'
      }
      'publish-race' {
        Assert-True $threw 'a foreign request arriving during publication must block'
        Assert-True (Test-Path -LiteralPath $request -PathType Leaf) 'racing request was removed'
        Assert-True (([IO.File]::ReadAllText($request)) -eq 'racing active request bytes') 'racing request changed'
      }
      'restore-fails' {
        Assert-True (Test-Path -LiteralPath $request -PathType Leaf) 'request lost despite failed recovery policy restoration'
      }
      'precontroller-fails' {
        Assert-True $threw 'authorizer failure must not report success'
        Assert-True (-not(Test-Path -LiteralPath $request)) 'owned request leaked after safe pre-controller failure'
      }
      'success' {
        Assert-True (-not $threw) 'normal synthetic controller should succeed'
        Assert-True (-not(Test-Path -LiteralPath $request)) 'owned request leaked after success'
      }
    }
    $receipts=@(Get-ChildItem -LiteralPath $maintenance -Filter run.json -Recurse -File)
    Assert-True ($receipts.Count -eq 1) 'expected exactly one durable run receipt'
    $receipt=Get-Content -Raw -LiteralPath $receipts[0].FullName|ConvertFrom-Json
    $expected=switch($case){
      'foreign' {'NOT_OWNED'}
      'publish-race' {'NOT_OWNED'}
      'controller-fails' {'RECONCILIATION_REQUIRED'}
      'restore-fails' {'RECONCILIATION_REQUIRED'}
      'replacement' {'REQUEST_CONFLICT'}
      default {'REMOVED'}
    }
    Assert-True ($receipt.requestCleanupStanding -eq $expected) "receipt standing mismatch for $case"
    if($case -in @('replacement','restore-fails')){
      Assert-True $threw 'unsafe success must not return normally'
      Assert-True ($receipt.status -eq 'reconciliation_required') 'uncertain effect must be explicit'
    }
    if($case -eq 'controller-fails' -or $case -eq 'restore-fails'){
      $current='sha256:'+(Get-FileHash -LiteralPath $request -Algorithm SHA256).Hash.ToLowerInvariant()
      Assert-True ($receipt.requestSha256 -eq $current) 'retained request identity must match receipt'
    }
    if($case -eq 'success'){Assert-True ($receipt.status -eq 'completed') 'success receipt must be completed'}
    Write-Output "PASS $case"
  } catch {
    $failed++
    Write-Output "FAIL $case : $($_.Exception.Message)"
  } finally {
    Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction Stop
  }
}
Remove-Item Env:ORDIVON_R3_TEST_ROOT,Env:ORDIVON_R3_TEST_CASE,Env:ORDIVON_R3_TEST_REQUEST -ErrorAction SilentlyContinue
if($failed){exit 1}
Write-Output '7 native Windows isolated request lifecycle cases passed'
