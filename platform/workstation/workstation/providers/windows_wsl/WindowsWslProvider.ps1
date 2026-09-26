param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('probe','verify-offline','admission-probe')]
  [string]$Command,

  [Parameter(Mandatory=$false)]
  [ValidatePattern('^[A-Za-z0-9._-]+$')]
  [string]$Distro = 'archlinux',

  [Parameter(Mandatory=$false)]
  [ValidateRange(1,30)]
  [int]$ProbeTimeoutSeconds = 8
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

function Invoke-WslAdmissionProbe {
  param(
    [string]$DistroName,
    [int]$TimeoutSeconds
  )

  $wsl = Join-Path $env:SystemRoot 'System32\wsl.exe'
  $marker = 'ORDIVON_WSL_ADMISSION_OK'
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $wsl
  $psi.WorkingDirectory = $env:SystemRoot
  $psi.Arguments = ('-d {0} -u root -- /usr/bin/printf {1}' -f $DistroName, $marker)
  $psi.UseShellExecute = $false
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.CreateNoWindow = $true

  $process = New-Object System.Diagnostics.Process
  $process.StartInfo = $psi
  $clock = [System.Diagnostics.Stopwatch]::StartNew()
  if (-not $process.Start()) {
    throw 'failed to start bounded wsl.exe admission probe'
  }

  $completed = $process.WaitForExit($TimeoutSeconds * 1000)
  if (-not $completed) {
    try { $process.Kill() } catch {}
    $clock.Stop()
    return [ordered]@{
      status = 'TIMEOUT'
      verified = $false
      attempted = $true
      timeoutSeconds = $TimeoutSeconds
      durationMs = [int64]$clock.ElapsedMilliseconds
      exitCode = $null
      stdout = ''
      stderr = ''
      marker = $marker
    }
  }

  $stdout = Normalize-WslName $process.StandardOutput.ReadToEnd()
  $stderr = Normalize-WslName $process.StandardError.ReadToEnd()
  $clock.Stop()
  $verified = ($process.ExitCode -eq 0 -and $stdout -eq $marker)
  $status = if ($verified) { 'READY' } else { 'ERROR' }
  return [ordered]@{
    status = $status
    verified = [bool]$verified
    attempted = $true
    timeoutSeconds = $TimeoutSeconds
    durationMs = [int64]$clock.ElapsedMilliseconds
    exitCode = [int]$process.ExitCode
    stdout = $stdout
    stderr = $stderr
    marker = $marker
  }
}

$all = @(Get-WslNames)
$running = @(Get-WslNames -RunningOnly)
$exists = $all -contains $Distro
$isRunning = $running -contains $Distro

$payload = [ordered]@{
  schemaVersion = 2
  kind = 'ordivon.workstation.windows-wsl-provider'
  providerId = 'provider/windows-local/windows-wsl-observer-v2'
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
  'admission-probe' {
    $payload['capabilityId'] = 'capability/wsl/fresh-session-admission'
    if (-not $exists) {
      $admission = [ordered]@{
        status = 'DISTRO_NOT_FOUND'
        verified = $false
        attempted = $false
        timeoutSeconds = $ProbeTimeoutSeconds
        durationMs = 0
        exitCode = $null
        stdout = ''
        stderr = ''
        marker = 'ORDIVON_WSL_ADMISSION_OK'
      }
    } else {
      $admission = Invoke-WslAdmissionProbe -DistroName $Distro -TimeoutSeconds $ProbeTimeoutSeconds
    }
    $payload['admissionProbe'] = $admission
    $payload['verified'] = [bool]$admission.verified
  }
}

$payload | ConvertTo-Json -Depth 8 -Compress
