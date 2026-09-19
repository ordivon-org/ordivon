param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('validate-d-drive-compact-r2')]
  [string]$Command,

  [Parameter(Mandatory=$true)]
  [string]$ReceiptPath,

  [Parameter(Mandatory=$true)]
  [string]$ExpectedDistro,

  [Parameter(Mandatory=$true)]
  [string]$ExpectedVhdPath,

  [Parameter(Mandatory=$true)]
  [ValidatePattern('^sha256:[0-9a-f]{64}$')]
  [string]$ExpectedGateSha256,

  [Parameter(Mandatory=$true)]
  [ValidatePattern('^sha256:[0-9a-f]{64}$')]
  [string]$ExpectedControllerSha256
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Add-Check {
  param(
    [System.Collections.Generic.List[object]]$Checks,
    [string]$Name,
    [bool]$Pass,
    [object]$Observed,
    [object]$Expected
  )
  $Checks.Add([ordered]@{
    name = $Name
    pass = $Pass
    observed = $Observed
    expected = $Expected
  })
}

if (-not (Test-Path -LiteralPath $ReceiptPath -PathType Leaf)) {
  throw "Authorization receipt missing: $ReceiptPath"
}

$raw = Get-Content -Raw -LiteralPath $ReceiptPath
$auth = $raw | ConvertFrom-Json
$checks = [System.Collections.Generic.List[object]]::new()

Add-Check $checks 'schemaVersion' ($auth.schemaVersion -eq 2) $auth.schemaVersion 2
Add-Check $checks 'kind' ($auth.kind -eq 'ordivon.d-drive-compact-authorization') $auth.kind 'ordivon.d-drive-compact-authorization'
Add-Check $checks 'restartAuthorized' ($auth.restartAuthorized -eq $true) $auth.restartAuthorized $true
Add-Check $checks 'compactAuthorized' ($auth.compactAuthorized -eq $true) $auth.compactAuthorized $true
Add-Check $checks 'runtimeActiveJobs' ($auth.runtimeActiveJobs -eq 0) $auth.runtimeActiveJobs 0
Add-Check $checks 'hostLeases' ($auth.hostLeases -eq 0) $auth.hostLeases 0
Add-Check $checks 'runtimeHealth' ($auth.runtimeHealth -eq 'healthy') $auth.runtimeHealth 'healthy'
Add-Check $checks 'recoveryRequiredAttempts' ($auth.recoveryRequiredAttempts -eq 0) $auth.recoveryRequiredAttempts 0
Add-Check $checks 'distro' ($auth.distro -eq $ExpectedDistro) $auth.distro $ExpectedDistro
Add-Check $checks 'vhdPath' ($auth.vhdPath -eq $ExpectedVhdPath) $auth.vhdPath $ExpectedVhdPath
Add-Check $checks 'gateSha256' ($auth.gateSha256 -eq $ExpectedGateSha256) $auth.gateSha256 $ExpectedGateSha256
Add-Check $checks 'controllerSha256' ($auth.controllerSha256 -eq $ExpectedControllerSha256) $auth.controllerSha256 $ExpectedControllerSha256

$expiry = $null
$expiryValid = $false
try {
  if (-not [string]::IsNullOrWhiteSpace([string]$auth.expiresAtUtc)) {
    $expiry = [DateTimeOffset]::Parse([string]$auth.expiresAtUtc)
    $expiryValid = [DateTimeOffset]::UtcNow -lt $expiry
  }
} catch {
  $expiryValid = $false
}
Add-Check $checks 'expiresAtUtc' $expiryValid $auth.expiresAtUtc 'future RFC3339 timestamp'

$authorized = -not ($checks | Where-Object { -not $_.pass })

$payload = [ordered]@{
  schemaVersion = 1
  kind = 'ordivon.workstation.authority-validation-provider'
  providerId = 'provider/windows-local/authority-validation-v1'
  capabilityId = 'capability/authority/validate'
  profile = 'd-drive-compact-r2'
  receiptPath = $ReceiptPath
  authorized = [bool]$authorized
  checks = $checks
  mutationAttempted = $false
  issuanceAttempted = $false
  renewalAttempted = $false
  windowsProcess = [ordered]@{
    pid = $PID
    user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
  }
}

$payload | ConvertTo-Json -Depth 8 -Compress
if (-not $authorized) {
  exit 3
}
