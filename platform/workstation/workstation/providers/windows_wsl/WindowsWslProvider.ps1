param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('probe','verify-offline')]
  [string]$Command,

  [Parameter(Mandatory=$false)]
  [ValidatePattern('^[A-Za-z0-9._-]+$')]
  [string]$Distro = 'archlinux'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Normalize-WslName {
  param([AllowNull()][object]$Value)
  if ($null -eq $Value) { return $null }
  return (([string]$Value) -replace [char]0, '').Trim()
}

function Get-WslNames {
  param([switch]$RunningOnly)
  $wsl = Join-Path $env:SystemRoot 'System32\wsl.exe'
  if (-not (Test-Path -LiteralPath $wsl -PathType Leaf)) {
    throw "wsl.exe is not present at expected path: $wsl"
  }

  $raw = if ($RunningOnly) {
    @(& $wsl --list --running --quiet)
  } else {
    @(& $wsl --list --quiet)
  }

  if ($LASTEXITCODE -ne 0) {
    throw "wsl.exe list command failed rc=$LASTEXITCODE"
  }

  return @(
    $raw |
      ForEach-Object { Normalize-WslName $_ } |
      Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
  )
}

$all = @(Get-WslNames)
$running = @(Get-WslNames -RunningOnly)
$exists = $all -contains $Distro
$isRunning = $running -contains $Distro

$payload = [ordered]@{
  schemaVersion = 1
  kind = 'ordivon.workstation.windows-wsl-provider'
  providerId = 'provider/windows-local/windows-wsl-observer-v1'
  command = $Command
  distro = $Distro
  exists = [bool]$exists
  running = [bool]$isRunning
  allDistros = $all
  runningDistros = $running
  mutationAttempted = $false
  windowsProcess = [ordered]@{
    pid = $PID
    user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    tokenElevated = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
      [Security.Principal.WindowsBuiltInRole]::Administrator
    )
  }
}

switch ($Command) {
  'probe' {
    $payload['capabilityId'] = 'capability/wsl/probe'
    $payload['verified'] = [bool]$exists
  }
  'verify-offline' {
    $payload['capabilityId'] = 'capability/wsl/verify-offline'
    $payload['verified'] = [bool]($exists -and -not $isRunning)
  }
}

$payload | ConvertTo-Json -Depth 6 -Compress
