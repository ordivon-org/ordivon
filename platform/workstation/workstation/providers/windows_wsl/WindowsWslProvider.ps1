param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('probe','verify-offline','storage-reclaim')]
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


function Convert-HexUInt64 {
  param([Parameter(Mandatory=$true)][string]$Value)
  if ($Value -notmatch '^0x[0-9A-Fa-f]+$') { throw "invalid hex value: $Value" }
  return [Convert]::ToUInt64($Value.Substring(2), 16)
}

function Get-DistroVhdPath {
  param([Parameter(Mandatory=$true)][string]$Name)
  $root = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss'
  $entry = Get-ChildItem -LiteralPath $root -ErrorAction Stop |
    ForEach-Object { Get-ItemProperty -LiteralPath $_.PSPath -ErrorAction Stop } |
    Where-Object { [string]$_.DistributionName -eq $Name } |
    Select-Object -First 1
  if ($null -eq $entry) { throw "WSL distro registry entry not found: $Name" }
  $base = [string]$entry.BasePath
  if ([string]::IsNullOrWhiteSpace($base)) { throw "WSL distro BasePath is empty: $Name" }
  $vhd = Join-Path $base 'ext4.vhdx'
  if (-not (Test-Path -LiteralPath $vhd -PathType Leaf)) { throw "WSL distro VHD is missing: $vhd" }
  return $vhd
}

function Get-SparseAllocation {
  param([Parameter(Mandatory=$true)][string]$Path)
  $driveRoot = [IO.Path]::GetPathRoot($Path)
  $driveLetter = $driveRoot.TrimEnd('\\')
  $escapedDrive = $driveLetter.Replace("'", "''")
  $volume = Get-CimInstance Win32_Volume -Filter "DriveLetter='$escapedDrive'" | Select-Object -First 1
  if ($null -eq $volume -or [uint64]$volume.BlockSize -eq 0) { throw "cannot resolve NTFS cluster size for $driveLetter" }
  $clusterBytes = [uint64]$volume.BlockSize
  $fsutil = Join-Path $env:SystemRoot 'System32\\fsutil.exe'
  $lines = @(& $fsutil file queryextents $Path 2>&1)
  if ($LASTEXITCODE -ne 0) { throw "fsutil file queryextents failed rc=$LASTEXITCODE" }
  [uint64]$allocatedClusters = 0
  [uint64]$holeClusters = 0
  [uint64]$extentCount = 0
  foreach ($line in $lines) {
    $matches = [regex]::Matches([string]$line, '0x[0-9A-Fa-f]+')
    if ($matches.Count -ne 3) { continue }
    $clusters = Convert-HexUInt64 $matches[1].Value
    $lcn = Convert-HexUInt64 $matches[2].Value
    if ($lcn -eq [uint64]::MaxValue) { $holeClusters += $clusters } else { $allocatedClusters += $clusters }
    $extentCount += 1
  }
  if ($extentCount -eq 0) { throw 'fsutil queryextents returned no parseable extents' }
  return [ordered]@{
    method = 'fsutil-file-queryextents-v1'
    clusterBytes = $clusterBytes
    extentCount = $extentCount
    allocatedBytes = $allocatedClusters * $clusterBytes
    holeBytes = $holeClusters * $clusterBytes
  }
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
  'storage-reclaim' {
    if (-not $exists) { throw "WSL distro does not exist: $Distro" }
    $vhd = Get-DistroVhdPath $Distro
    $item = Get-Item -LiteralPath $vhd -ErrorAction Stop
    $allocation = Get-SparseAllocation $vhd
    $length = [uint64]$item.Length
    $accounted = [uint64]$allocation.allocatedBytes + [uint64]$allocation.holeBytes
    $root = [IO.Path]::GetPathRoot($vhd)
    $payload['capabilityId'] = 'capability/wsl/storage-reclaim-observe'
    $payload['verified'] = [bool]($accounted -eq $length)
    $payload['storageReclaim'] = [ordered]@{
      vhdPath = $vhd
      sparse = [bool](($item.Attributes -band [IO.FileAttributes]::SparseFile) -ne 0)
      logicalBytes = $length
      allocatedBytes = [uint64]$allocation.allocatedBytes
      holeBytes = [uint64]$allocation.holeBytes
      accountedBytes = $accounted
      accountingMatchesLogicalLength = [bool]($accounted -eq $length)
      extentCount = [uint64]$allocation.extentCount
      clusterBytes = [uint64]$allocation.clusterBytes
      hostVolume = $root
      hostFreeBytes = [uint64]([IO.DriveInfo]::new($root)).AvailableFreeSpace
      allocationMethod = [string]$allocation.method
      batStanding = 'UNKNOWN_NOT_OBSERVED'
    }
  }
}

$payload | ConvertTo-Json -Depth 6 -Compress
