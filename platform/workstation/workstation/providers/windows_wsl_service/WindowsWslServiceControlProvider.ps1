param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('probe','ensure')]
  [string]$Command,

  [Parameter(Mandatory=$false)]
  [ValidateSet('control-plane','acceptance')]
  [string]$Profile = 'control-plane',

  [Parameter(Mandatory=$false)]
  [ValidatePattern('^[A-Za-z0-9._-]+$')]
  [string]$Distro = 'archlinux'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Profiles = @{
  'control-plane' = @('ordivon-runtime.service','ordivon-host-v2.service')
  'acceptance' = @('ordivon-ef6e-ensure-test.service')
}

function Normalize-Output {
  param([AllowNull()][object]$Value)
  if ($null -eq $Value) { return '' }
  return (([string]$Value) -replace [char]0, '').Trim()
}

function Invoke-WslCommand {
  param([string[]]$Arguments)
  $wsl = Join-Path $env:SystemRoot 'System32\wsl.exe'
  $raw = @(& $wsl -d $Distro -u root -- @Arguments 2>&1)
  $rc = $LASTEXITCODE
  return [ordered]@{
    exitCode = [int]$rc
    output = @($raw | ForEach-Object { Normalize-Output $_ } | Where-Object { $_ })
  }
}

function Get-UnitState {
  param([string]$Unit)
  $result = Invoke-WslCommand @('/usr/bin/systemctl','is-active',$Unit)
  $state = if ($result.output.Count -gt 0) { [string]$result.output[0] } else { 'unknown' }
  return [ordered]@{
    unit = $Unit
    state = $state
    exitCode = $result.exitCode
  }
}

$units = @($Profiles[$Profile])
$before = @($units | ForEach-Object { Get-UnitState $_ })
$inactive = @($before | Where-Object { $_.state -ne 'active' } | ForEach-Object { $_.unit })
$started = @()
$mutationAttempted = $false

if ($Command -eq 'ensure' -and $inactive.Count -gt 0) {
  $mutationAttempted = $true
  $startResult = Invoke-WslCommand (@('/usr/bin/systemctl','start') + $inactive)
  if ($startResult.exitCode -ne 0) {
    throw "systemctl start failed rc=$($startResult.exitCode): $($startResult.output -join ' | ')"
  }
  $started = @($inactive)
}

$after = @($units | ForEach-Object { Get-UnitState $_ })
$healthy = -not ($after | Where-Object { $_.state -ne 'active' })

$capability = if ($Command -eq 'ensure') { 'capability/service/ensure' } else { 'capability/service/probe' }

[ordered]@{
  schemaVersion = 1
  kind = 'ordivon.workstation.windows-wsl-service-control-provider'
  providerId = 'provider/windows-local/wsl-service-control-v1'
  capabilityId = $capability
  command = $Command
  profile = $Profile
  distro = $Distro
  units = $units
  before = $before
  after = $after
  healthy = [bool]$healthy
  mutationAttempted = [bool]$mutationAttempted
  startedUnits = $started
  targetNodeId = 'linux-local'
  windowsProcess = [ordered]@{
    pid = $PID
    user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
  }
} | ConvertTo-Json -Depth 8 -Compress

if (-not $healthy) {
  exit 4
}
