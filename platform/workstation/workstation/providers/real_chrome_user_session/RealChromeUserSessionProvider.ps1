param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('status','install','start','stop','remove')]
  [string]$Command,

  [Parameter(Mandatory=$false)]
  [string]$ProxyUrl = 'http://127.0.0.1:19781',

  [Parameter(Mandatory=$false)]
  [string]$ChromePath = 'C:\Program Files\Google\Chrome\Application\chrome.exe',

  [Parameter(Mandatory=$false)]
  [ValidatePattern('^[A-Za-z0-9._ -]+$')]
  [string]$TaskName = 'Ordivon-RealChrome-UserSession',

  [Parameter(Mandatory=$false)]
  [ValidateRange(1,30)]
  [int]$StartTimeoutSeconds = 12
)

$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

function Get-InteractiveUser {
  $user=[string](Get-CimInstance Win32_ComputerSystem -ErrorAction Stop).UserName
  if([string]::IsNullOrWhiteSpace($user)){throw 'no interactive Windows user is logged on'}
  return $user.Trim()
}

function Test-LoopbackHttpProxy([string]$Value) {
  $uri=$null
  if(-not [Uri]::TryCreate($Value,[UriKind]::Absolute,[ref]$uri)){return $false}
  if($uri.Scheme -ne 'http'){return $false}
  if($uri.UserInfo){return $false}
  if($uri.AbsolutePath -ne '/' -or $uri.Query -or $uri.Fragment){return $false}
  return ($uri.Host -eq '127.0.0.1' -or $uri.Host -eq 'localhost' -or $uri.Host -eq '::1')
}

function Get-BrowserProcess {
  $rows=@(Get-CimInstance Win32_Process -Filter "name='chrome.exe'" -ErrorAction SilentlyContinue)
  foreach($row in $rows){
    $cmd=[string]$row.CommandLine
    if($cmd -notmatch ' --type='){return $row}
  }
  return $null
}

function Get-TaskState([string]$Name) {
  $task=Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
  if($null -eq $task){return $null}
  return [string]$task.State
}

function Emit([string]$Standing,[bool]$MutationAttempted,[hashtable]$Extra) {
  $payload=[ordered]@{
    schemaVersion=1
    kind='ordivon.workstation.real-chrome-user-session-provider'
    command=$Command
    standing=$Standing
    taskName=$TaskName
    proxyUrl=$ProxyUrl
    mutationAttempted=$MutationAttempted
    browserControlAuthorityGranted=$false
    providerEffectAuthorized=$false
  }
  foreach($k in $Extra.Keys){$payload[$k]=$Extra[$k]}
  $payload | ConvertTo-Json -Compress -Depth 6
}

if(-not (Test-LoopbackHttpProxy $ProxyUrl)){throw 'ProxyUrl must be loopback HTTP with no credentials/path/query/fragment'}
if(-not (Test-Path -LiteralPath $ChromePath -PathType Leaf)){throw 'ChromePath is unavailable'}

switch($Command){
  'status' {
    $browser=Get-BrowserProcess
    $cmdline=if($null -ne $browser){[string]$browser.CommandLine}else{''}
    Emit 'OBSERVED' $false @{
      interactiveUser=Get-InteractiveUser
      taskState=Get-TaskState $TaskName
      chromeRunning=($null -ne $browser)
      proxyBindingPresent=($cmdline -match ('--proxy-server='+[regex]::Escape($ProxyUrl)))
      disableQuicPresent=($cmdline -match '--disable-quic')
    }
    exit 0
  }

  'install' {
    $user=Get-InteractiveUser
    $old=Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if($null -ne $old -and [string]$old.State -eq 'Running'){throw 'refusing to replace a running real-Chrome carrier task'}
    if($null -ne $old){Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop}
    $args='--new-window --force-renderer-accessibility --disable-session-crashed-bubble --no-first-run --disable-quic --proxy-server='+$ProxyUrl+' chrome://inspect/#remote-debugging'
    $action=New-ScheduledTaskAction -Execute $ChromePath -Argument $args
    $principal=New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
    $settings=New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $TaskName -Action $action -Principal $principal -Settings $settings -Force | Out-Null
    Emit 'INSTALLED' $true @{
      interactiveUser=$user
      taskState=Get-TaskState $TaskName
      passwordStored=$false
    }
    exit 0
  }

  'start' {
    $task=Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    $before=Get-BrowserProcess
    if($null -ne $before){throw 'refusing start while Chrome is already running; exact launch binding would be ambiguous'}
    Start-ScheduledTask -TaskName $TaskName
    $deadline=(Get-Date).AddSeconds($StartTimeoutSeconds)
    $browser=$null
    do{
      Start-Sleep -Milliseconds 250
      $browser=Get-BrowserProcess
    }while($null -eq $browser -and (Get-Date)-lt $deadline)
    if($null -eq $browser){
      Emit 'START_TIMEOUT' $true @{taskState=Get-TaskState $TaskName;chromeRunning=$false}
      exit 2
    }
    $cmdline=[string]$browser.CommandLine
    $bound=($cmdline -match ('--proxy-server='+[regex]::Escape($ProxyUrl)))
    $quic=($cmdline -match '--disable-quic')
    $standing=if($bound -and $quic){'RUNNING'}else{'BINDING_MISMATCH'}
    Emit $standing $true @{
      taskState=Get-TaskState $TaskName
      chromeRunning=$true
      proxyBindingPresent=$bound
      disableQuicPresent=$quic
    }
    if($standing -ne 'RUNNING'){exit 3}
    exit 0
  }

  'stop' {
    $task=Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if($null -eq $task){
      Emit 'TASK_ABSENT' $false @{chromeRunning=($null -ne (Get-BrowserProcess))}
      exit 0
    }
    if([string]$task.State -eq 'Running'){
      Stop-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    }
    $deadline=(Get-Date).AddSeconds(10)
    do{
      Start-Sleep -Milliseconds 250
      $browser=Get-BrowserProcess
    }while($null -ne $browser -and (Get-Date)-lt $deadline)
    $remaining=($null -ne (Get-BrowserProcess))
    Emit $(if($remaining){'STOP_INCOMPLETE'}else{'STOPPED'}) $true @{
      taskState=Get-TaskState $TaskName
      chromeRunning=$remaining
    }
    if($remaining){exit 4}
    exit 0
  }

  'remove' {
    $task=Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if($null -eq $task){
      Emit 'TASK_ABSENT' $false @{}
      exit 0
    }
    if([string]$task.State -eq 'Running'){throw 'refusing to remove a running real-Chrome carrier task; stop first'}
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
    Emit 'REMOVED' $true @{}
    exit 0
  }
}
