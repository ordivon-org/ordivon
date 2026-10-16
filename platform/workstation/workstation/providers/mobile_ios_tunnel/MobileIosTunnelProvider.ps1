param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('status','install','start','stop','remove')]
  [string]$Command,

  [Parameter(Mandatory=$true)]
  [ValidatePattern('^[A-Fa-f0-9-]{20,64}$')]
  [string]$Udid,

  [Parameter(Mandatory=$false)]
  [ValidatePattern('^[A-Za-z0-9._-]+$')]
  [string]$ServiceName = 'OrdivonRuntimeR6Candidate',

  [Parameter(Mandatory=$false)]
  [ValidatePattern('^[A-Za-z0-9._ -]+$')]
  [string]$TaskName = 'Ordivon-GoIos-Tunnel',

  [Parameter(Mandatory=$false)]
  [ValidateRange(1024,65535)]
  [int]$TunnelInfoPort = 60105,

  [Parameter(Mandatory=$false)]
  [string]$IosPath = 'C:\ProgramData\Ordivon\RuntimeCandidateR6\native-tools\go-ios\v1.3.2\ios.exe',

  [Parameter(Mandatory=$false)]
  [string]$PairRecordRoot = '',

  [Parameter(Mandatory=$false)]
  [ValidateRange(1,30)]
  [int]$StartTimeoutSeconds = 12
)

$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

if([string]::IsNullOrWhiteSpace($PairRecordRoot)) {
  $PairRecordRoot = "C:\Windows\ServiceProfiles\$ServiceName\AppData\Local\Ordivon\Mobile\go-ios-pairing"
}

function Get-TaskState([string]$Name) {
  $task=Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
  if($null -eq $task){return $null}
  return [string]$task.State
}

function Get-TunnelRows {
  $previousErrorActionPreference=$ErrorActionPreference
  try {
    $ErrorActionPreference='Continue'
    $raw=& $IosPath tunnel ls --tunnel-info-port $TunnelInfoPort --pretty 2>$null
    $nativeExitCode=$LASTEXITCODE
  } finally {
    $ErrorActionPreference=$previousErrorActionPreference
  }
  if($nativeExitCode -ne 0 -or [string]::IsNullOrWhiteSpace(($raw -join [Environment]::NewLine))){
    return @()
  }
  try {
    $parsed=($raw -join [Environment]::NewLine) | ConvertFrom-Json
  } catch {
    return @()
  }
  return @($parsed)
}

function Get-MatchingTunnel {
  return @(Get-TunnelRows | Where-Object {
    [string]$_.udid -eq $Udid -and [bool]$_.userspaceTun
  })
}

function Emit([string]$Standing,[bool]$MutationAttempted,[hashtable]$Extra) {
  $payload=[ordered]@{
    schemaVersion=1
    kind='ordivon.workstation.mobile-ios-tunnel-provider'
    command=$Command
    standing=$Standing
    taskName=$TaskName
    udid=$Udid
    tunnelInfoPort=$TunnelInfoPort
    controlPlaneAuthority='elevated'
    tunnelExecutionIdentity="NT SERVICE\$ServiceName"
    tunnelExecutionPrivilege='limited'
    mutationAttempted=$MutationAttempted
    deviceControlAuthorized=$false
    runnerReady=$false
    providerEffectAuthorized=$false
  }
  foreach($k in $Extra.Keys){$payload[$k]=$Extra[$k]}
  $payload | ConvertTo-Json -Compress -Depth 6
}

if(-not (Test-Path -LiteralPath $IosPath -PathType Leaf)){throw 'go-ios carrier is unavailable'}
$ExpectedIosSha256='c99b04f1d615fa716637efae457d5c554f32259f9d249375de0086e3cc1a1df5'
$ObservedIosSha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $IosPath).Hash.ToLowerInvariant()
if($ObservedIosSha256 -ne $ExpectedIosSha256){throw 'go-ios carrier digest mismatch'}

switch($Command) {
  'status' {
    $rows=@(Get-MatchingTunnel)
    Emit $(if($rows.Count -eq 1){'TUNNEL_READY'}elseif($rows.Count -gt 1){'AMBIGUOUS'}else{'NOT_READY'}) $false @{
      taskState=Get-TaskState $TaskName
      tunnelCount=$rows.Count
      pairRecordRoot=$PairRecordRoot
    }
    exit $(if($rows.Count -le 1){0}else{3})
  }

  'install' {
    $old=Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if($null -ne $old -and [string]$old.State -eq 'Running'){throw 'refusing to replace a running go-ios tunnel task'}
    if($null -ne $old){Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop}

    New-Item -ItemType Directory -Path $PairRecordRoot -Force | Out-Null
    $working=Split-Path -Parent $PairRecordRoot
    $args='tunnel start --userspace --udid '+$Udid+' --tunnel-info-port '+$TunnelInfoPort+' --pair-record-path "'+$PairRecordRoot+'"'
    $action=New-ScheduledTaskAction -Execute $IosPath -Argument $args -WorkingDirectory $working
    $principal=New-ScheduledTaskPrincipal -UserId ("NT SERVICE\$ServiceName") -LogonType ServiceAccount -RunLevel Limited
    $settings=New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $TaskName -Action $action -Principal $principal -Settings $settings -Force | Out-Null

    Emit 'INSTALLED' $true @{
      taskState=Get-TaskState $TaskName
      pairRecordRoot=$PairRecordRoot
      credentialStored=$false
    }
    exit 0
  }

  'start' {
    $task=Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    if([string]$task.State -eq 'Running'){
      $rows=@(Get-MatchingTunnel)
      Emit $(if($rows.Count -eq 1){'TUNNEL_READY'}else{'TASK_RUNNING_TUNNEL_NOT_READY'}) $false @{
        taskState=[string]$task.State
        tunnelCount=$rows.Count
        pairRecordRoot=$PairRecordRoot
      }
      exit $(if($rows.Count -eq 1){0}else{2})
    }

    Start-ScheduledTask -TaskName $TaskName
    $deadline=(Get-Date).AddSeconds($StartTimeoutSeconds)
    $rows=@()
    do {
      Start-Sleep -Milliseconds 250
      $rows=@(Get-MatchingTunnel)
    } while($rows.Count -eq 0 -and (Get-Date) -lt $deadline)

    $standing=if($rows.Count -eq 1){'TUNNEL_READY'}elseif($rows.Count -gt 1){'AMBIGUOUS'}else{'START_TIMEOUT'}
    Emit $standing $true @{
      taskState=Get-TaskState $TaskName
      tunnelCount=$rows.Count
      pairRecordRoot=$PairRecordRoot
    }
    if($standing -ne 'TUNNEL_READY'){exit 2}
    exit 0
  }

  'stop' {
    $task=Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if($null -eq $task){
      Emit 'TASK_ABSENT' $false @{tunnelCount=@(Get-MatchingTunnel).Count;pairRecordRoot=$PairRecordRoot}
      exit 0
    }
    if([string]$task.State -eq 'Running'){Stop-ScheduledTask -TaskName $TaskName -ErrorAction Stop}
    $deadline=(Get-Date).AddSeconds(10)
    do {
      Start-Sleep -Milliseconds 250
      $rows=@(Get-MatchingTunnel)
    } while($rows.Count -gt 0 -and (Get-Date) -lt $deadline)
    $standing=if($rows.Count -eq 0){'STOPPED'}else{'STOP_INCOMPLETE'}
    Emit $standing $true @{taskState=Get-TaskState $TaskName;tunnelCount=$rows.Count;pairRecordRoot=$PairRecordRoot}
    if($standing -ne 'STOPPED'){exit 4}
    exit 0
  }

  'remove' {
    $task=Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if($null -eq $task){
      Emit 'TASK_ABSENT' $false @{pairRecordRoot=$PairRecordRoot}
      exit 0
    }
    if([string]$task.State -eq 'Running'){throw 'refusing to remove a running go-ios tunnel task; stop first'}
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
    Emit 'REMOVED' $true @{pairRecordRoot=$PairRecordRoot}
    exit 0
  }
}
