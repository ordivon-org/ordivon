param(
  [Parameter(Mandatory=$true)][string]$ProgramDirectory,
  [Parameter(Mandatory=$true)][string]$SessionDirectory,
  [Parameter(Mandatory=$true)][string]$SessionJson
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

function Sha256-Hex([byte[]]$Bytes) {
  $sha = [Security.Cryptography.SHA256]::Create()
  try { return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant() }
  finally { $sha.Dispose() }
}
function Sha256-B64([string]$Text) {
  $bytes=[Text.Encoding]::UTF8.GetBytes($Text)
  $sha=[Security.Cryptography.SHA256]::Create()
  try { return [Convert]::ToBase64String($sha.ComputeHash($bytes)) }
  finally { $sha.Dispose() }
}

$obsRoot = Join-Path $env:APPDATA 'obs-studio'
$wsConfig = Join-Path $obsRoot 'plugin_config\obs-websocket\config.json'
$globalIni = Join-Path $obsRoot 'global.ini'
$profileIni = Get-ChildItem (Join-Path $obsRoot 'basic\profiles') -Directory | Select-Object -First 1 | ForEach-Object { Join-Path $_.FullName 'basic.ini' }
$sceneJson = Get-ChildItem (Join-Path $obsRoot 'basic\scenes') -Filter '*.json' -File | Select-Object -First 1 -ExpandProperty FullName
$obsExe = 'C:\Program Files\obs-studio\bin\64bit\obs64.exe'
$obsDir = Split-Path $obsExe
$paths = @($wsConfig,$globalIni,$profileIni,$sceneJson)
foreach($p in $paths){ if(-not (Test-Path -LiteralPath $p -PathType Leaf)){ throw "required OBS state file missing: $p" } }
if(@(Get-Process -Name obs64 -ErrorAction SilentlyContinue).Count -ne 0){ throw 'OBS_ALREADY_RUNNING_PRECONDITION' }

New-Item -ItemType Directory -Path $SessionDirectory -Force | Out-Null
$backupDir = Join-Path $SessionDirectory 'state-backup'
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
$backup = @{}
foreach($p in $paths){
  $bytes=[IO.File]::ReadAllBytes($p)
  $backup[$p]=$bytes
  $name=([IO.Path]::GetFileName($p))+'-'+(Sha256-Hex $bytes)+'.bak'
  [IO.File]::WriteAllBytes((Join-Path $backupDir $name),$bytes)
}
$before = @{
  websocketConfigSha256 = Sha256-Hex $backup[$wsConfig]
  globalIniSha256 = Sha256-Hex $backup[$globalIni]
  profileIniSha256 = Sha256-Hex $backup[$profileIni]
  sceneCollectionSha256 = Sha256-Hex $backup[$sceneJson]
}

$cfg = Get-Content -LiteralPath $wsConfig -Raw -Encoding UTF8 | ConvertFrom-Json
if(-not $cfg.auth_required){ throw 'OBS_WEBSOCKET_AUTH_REQUIRED_PRECONDITION' }
$password = [string]$cfg.server_password
if([string]::IsNullOrEmpty($password)){ throw 'OBS_WEBSOCKET_PASSWORD_MISSING_PRECONDITION' }
$utf8NoBom = New-Object Text.UTF8Encoding($false)

$obs=$null; $ws=$null; $originalScene=$null; $createdScenes=New-Object System.Collections.Generic.List[string]
$muteState=New-Object System.Collections.Generic.List[object]
$events=New-Object System.Collections.Generic.List[object]
$timeline=New-Object System.Collections.Generic.List[object]
$timer=[Diagnostics.Stopwatch]::StartNew()
$recordOutput=$null; $version=$null; $episodeSucceeded=$false; $cleanup=@{}

function Timeline([string]$Kind,[string]$Detail){ $timeline.Add([pscustomobject]@{elapsedMs=$timer.ElapsedMilliseconds;kind=$Kind;detail=$Detail}) }
function Send-ObsJson($Object){
  $json=$Object | ConvertTo-Json -Compress -Depth 30
  $bytes=[Text.Encoding]::UTF8.GetBytes($json)
  $segment=New-Object 'System.ArraySegment[byte]' -ArgumentList (,$bytes)
  [void]$script:ws.SendAsync($segment,[Net.WebSockets.WebSocketMessageType]::Text,$true,[Threading.CancellationToken]::None).GetAwaiter().GetResult()
}
function Receive-ObsJson(){
  $buf=New-Object byte[] 65536; $mem=New-Object IO.MemoryStream
  try {
    do {
      $segment=New-Object 'System.ArraySegment[byte]' -ArgumentList (,$buf)
      $res=$script:ws.ReceiveAsync($segment,[Threading.CancellationToken]::None).GetAwaiter().GetResult()
      if($res.MessageType -eq [Net.WebSockets.WebSocketMessageType]::Close){ throw 'OBS_WEBSOCKET_CLOSED' }
      $mem.Write($buf,0,$res.Count)
    } while(-not $res.EndOfMessage)
    return ([Text.Encoding]::UTF8.GetString($mem.ToArray()) | ConvertFrom-Json)
  } finally { $mem.Dispose() }
}
function Invoke-ObsRequest([string]$Type,$Data=$null,[switch]$AllowFailure){
  $id=[guid]::NewGuid().ToString('N')
  $d=@{requestType=$Type;requestId=$id}; if($null -ne $Data){$d.requestData=$Data}
  Send-ObsJson @{op=6;d=$d}
  while($true){
    $m=Receive-ObsJson
    if($m.op -eq 5){
      $events.Add([pscustomobject]@{elapsedMs=$timer.ElapsedMilliseconds;eventType=[string]$m.d.eventType})
      continue
    }
    if($m.op -eq 7 -and [string]$m.d.requestId -eq $id){
      if(-not $m.d.requestStatus.result){
        if($AllowFailure){ return [pscustomobject]@{ok=$false;status=$m.d.requestStatus;data=$null} }
        throw ("OBS_REQUEST_FAILED {0} code={1} comment={2}" -f $Type,$m.d.requestStatus.code,$m.d.requestStatus.comment)
      }
      if($AllowFailure){ return [pscustomobject]@{ok=$true;status=$m.d.requestStatus;data=$m.d.responseData} }
      return $m.d.responseData
    }
  }
}
function Connect-Obs([string]$Password){
  for($attempt=1;$attempt -le 80;$attempt++){
    try {
      $script:ws=[Net.WebSockets.ClientWebSocket]::new()
      [void]$script:ws.ConnectAsync([Uri]'ws://127.0.0.1:4455',[Threading.CancellationToken]::None).GetAwaiter().GetResult()
      break
    } catch {
      if($script:ws){$script:ws.Dispose();$script:ws=$null}
      if($attempt -eq 80){throw}
      Start-Sleep -Milliseconds 250
    }
  }
  $hello=Receive-ObsJson
  if($hello.op -ne 0){throw 'OBS_EXPECTED_HELLO'}
  $identify=@{rpcVersion=1;eventSubscriptions=196}
  if($hello.d.authentication){
    $secret=Sha256-B64 ($Password+[string]$hello.d.authentication.salt)
    $auth=Sha256-B64 ($secret+[string]$hello.d.authentication.challenge)
    $identify.authentication=$auth
  }
  Send-ObsJson @{op=1;d=$identify}
  $identified=Receive-ObsJson
  if($identified.op -ne 2){throw 'OBS_IDENTIFY_FAILED'}
}
function Remove-TempScenes {
  foreach($name in @($createdScenes.ToArray()) | Sort-Object -Descending){
    try { [void](Invoke-ObsRequest 'RemoveScene' @{sceneName=$name} -AllowFailure) } catch {}
  }
}
function Restore-Mutes {
  foreach($m in $muteState){
    try { [void](Invoke-ObsRequest 'SetInputMute' @{inputName=$m.inputName;inputMuted=[bool]$m.original} -AllowFailure) } catch {}
  }
}
function Post-WmClose([uint32]$TargetPid){
  if(-not ('ObsWinClose' -as [type])){
    Add-Type @"
using System; using System.Runtime.InteropServices;
public static class ObsWinClose {
 public delegate bool EWP(IntPtr h, IntPtr l);
 [DllImport("user32.dll")] public static extern bool EnumWindows(EWP f, IntPtr l);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint p);
 [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);
}
"@
  }
  [ObsWinClose]::EnumWindows({param($h,$l) [uint32]$procId=0; [void][ObsWinClose]::GetWindowThreadProcessId($h,[ref]$procId); if($procId -eq $TargetPid){[void][ObsWinClose]::PostMessage($h,0x0010,[IntPtr]::Zero,[IntPtr]::Zero)}; return $true},[IntPtr]::Zero)|Out-Null
}

try {
  # Every persistent-state mutation is inside this recovery domain.
  $cfg.server_enabled = $true
  [IO.File]::WriteAllText($wsConfig,($cfg | ConvertTo-Json -Depth 20),$utf8NoBom)
  $profileText=[IO.File]::ReadAllText($profileIni)
  $recordEscaped=$SessionDirectory.Replace('\','\\')
  $profileText=[regex]::Replace($profileText,'(?m)^FilePath=.*$',('FilePath='+$recordEscaped))
  $profileText=[regex]::Replace($profileText,'(?m)^RecFilePath=.*$',('RecFilePath='+$recordEscaped))
  [IO.File]::WriteAllText($profileIni,$profileText,$utf8NoBom)
  Timeline 'state' 'temporary-config-applied'
  $obs=Start-Process -FilePath $obsExe -WorkingDirectory $obsDir -PassThru
  Timeline 'lifecycle' 'obs-started'
  Connect-Obs $password
  Timeline 'lifecycle' 'websocket-authenticated'
  $version=Invoke-ObsRequest 'GetVersion'
  $needed=@('GetSceneList','CreateScene','CreateInput','SetCurrentProgramScene','RemoveScene','GetInputList','GetInputMute','SetInputMute','GetRecordStatus','StartRecord','StopRecord')
  foreach($r in $needed){ if($version.availableRequests -notcontains $r){throw "OBS_REQUEST_NOT_AVAILABLE $r"} }
  $scenes=Invoke-ObsRequest 'GetSceneList'; $originalScene=[string]$scenes.currentProgramSceneName
  if([string]::IsNullOrEmpty($originalScene)){throw 'ORIGINAL_PROGRAM_SCENE_EMPTY'}
  $rec=Invoke-ObsRequest 'GetRecordStatus'; if($rec.outputActive){throw 'RECORDING_ALREADY_ACTIVE'}

  # Privacy guard: temporarily mute every input that exposes mute state; restore exact state after episode.
  $inputs=Invoke-ObsRequest 'GetInputList'
  foreach($i in @($inputs.inputs)){
    $m=Invoke-ObsRequest 'GetInputMute' @{inputName=[string]$i.inputName} -AllowFailure
    if($m.ok){
      $orig=[bool]$m.data.inputMuted
      $muteState.Add([pscustomobject]@{inputName=[string]$i.inputName;original=$orig})
      if(-not $orig){ [void](Invoke-ObsRequest 'SetInputMute' @{inputName=[string]$i.inputName;inputMuted=$true}) }
    }
  }
  Timeline 'privacy' ('audio-inputs-fenced:'+ $muteState.Count)

  $programme=@(
    @{token='signal';scene='ORDIVON Relay 001 - 00 Signal';file='00-signal.png'},
    @{token='archive';scene='ORDIVON Relay 001 - 01 Archive';file='01-archive.png'},
    @{token='object';scene='ORDIVON Relay 001 - 02 Object';file='02-object.png'},
    @{token='constellation';scene='ORDIVON Relay 001 - 03 Constellation';file='03-constellation.png'}
  )
  $existing=@($scenes.scenes | ForEach-Object {[string]$_.sceneName})
  foreach($slot in $programme){ if($existing -contains $slot.scene){throw ('TEMP_SCENE_COLLISION '+$slot.scene)} }
  foreach($slot in $programme){
    [void](Invoke-ObsRequest 'CreateScene' @{sceneName=$slot.scene}); $createdScenes.Add($slot.scene)
    $path=Join-Path $ProgramDirectory $slot.file
    if(-not (Test-Path -LiteralPath $path -PathType Leaf)){throw "PROGRAM_CARD_MISSING $path"}
    [void](Invoke-ObsRequest 'CreateInput' @{sceneName=$slot.scene;inputName=($slot.scene+' / Card');inputKind='image_source';inputSettings=@{file=$path};sceneItemEnabled=$true})
  }
  Timeline 'programme' 'temporary-scenes-created'

  $signal=$programme[0].scene; $archive=$programme[1].scene; $object=$programme[2].scene; $constellation=$programme[3].scene
  [void](Invoke-ObsRequest 'SetCurrentProgramScene' @{sceneName=$signal}); Timeline 'switch' 'signal-open'; Start-Sleep -Milliseconds 500
  [void](Invoke-ObsRequest 'StartRecord'); Timeline 'record' 'start'; Start-Sleep -Seconds 3
  [void](Invoke-ObsRequest 'SetCurrentProgramScene' @{sceneName=$archive}); Timeline 'switch' 'archive'; Start-Sleep -Seconds 6
  [void](Invoke-ObsRequest 'SetCurrentProgramScene' @{sceneName=$object}); Timeline 'switch' 'object'; Start-Sleep -Seconds 4
  [void](Invoke-ObsRequest 'SetCurrentProgramScene' @{sceneName=$constellation}); Timeline 'switch' 'constellation'; Start-Sleep -Seconds 6
  [void](Invoke-ObsRequest 'SetCurrentProgramScene' @{sceneName=$signal}); Timeline 'switch' 'signal-close'; Start-Sleep -Seconds 3
  $stop=Invoke-ObsRequest 'StopRecord'; $recordOutput=[string]$stop.outputPath; Timeline 'record' 'stop-requested'
  $post=$null
  for($settle=1;$settle -le 40;$settle++){
    Start-Sleep -Milliseconds 250
    $post=Invoke-ObsRequest 'GetRecordStatus'
    if(-not $post.outputActive){ Timeline 'record' ('stopped-after-polls:'+$settle); break }
  }
  if($post.outputActive){throw 'RECORDING_STILL_ACTIVE_AFTER_SETTLE_WINDOW'}
  if([string]::IsNullOrEmpty($recordOutput)){throw 'RECORD_OUTPUT_PATH_EMPTY'}
  if(-not (Test-Path -LiteralPath $recordOutput -PathType Leaf)){throw "RECORD_OUTPUT_MISSING $recordOutput"}

  [void](Invoke-ObsRequest 'SetCurrentProgramScene' @{sceneName=$originalScene}); Timeline 'restore' 'program-scene'
  Remove-TempScenes; Timeline 'restore' 'temporary-scenes-removed'
  Restore-Mutes
  foreach($m in $muteState){
    $check=Invoke-ObsRequest 'GetInputMute' @{inputName=$m.inputName} -AllowFailure
    if(-not $check.ok -or [bool]$check.data.inputMuted -ne [bool]$m.original){throw 'INPUT_MUTE_RESTORE_FAILED'}
  }
  Timeline 'restore' 'audio-input-mutes-verified'
  $afterScenes=Invoke-ObsRequest 'GetSceneList'
  if([string]$afterScenes.currentProgramSceneName -ne $originalScene){throw 'PROGRAM_SCENE_RESTORE_FAILED'}
  foreach($slot in $programme){if(@($afterScenes.scenes | ForEach-Object {[string]$_.sceneName}) -contains $slot.scene){throw 'TEMP_SCENE_REMAINS'}}
  $episodeSucceeded=$true
}
finally {
  if($ws -and $ws.State -eq [Net.WebSockets.WebSocketState]::Open){
    if($originalScene){try{[void](Invoke-ObsRequest 'SetCurrentProgramScene' @{sceneName=$originalScene} -AllowFailure)}catch{}}
    try{Remove-TempScenes}catch{}
    try{Restore-Mutes}catch{}
    try{[void]$ws.CloseAsync([Net.WebSockets.WebSocketCloseStatus]::NormalClosure,'done',[Threading.CancellationToken]::None).GetAwaiter().GetResult()}catch{}
    $ws.Dispose()
  }
  if($obs){
    try{$obs.Refresh()}catch{}
    if(-not $obs.HasExited){ Post-WmClose ([uint32]$obs.Id); try{Wait-Process -Id $obs.Id -Timeout 15 -ErrorAction SilentlyContinue}catch{} }
  }
  $remaining=@(Get-Process -Name obs64 -ErrorAction SilentlyContinue).Count
  $cleanup['obsProcessCountAfter']=$remaining
  $listener=$false
  try { $tcp=New-Object Net.Sockets.TcpClient; $iar=$tcp.BeginConnect('127.0.0.1',4455,$null,$null); if($iar.AsyncWaitHandle.WaitOne(300)){try{$tcp.EndConnect($iar);$listener=$tcp.Connected}catch{}}; $tcp.Close() } catch {}
  $cleanup['listener4455After']=$listener
  # Exact state restoration happens only after the GUI has had its chance to persist shutdown state.
  foreach($p in $paths){ [IO.File]::WriteAllBytes($p,[byte[]]$backup[$p]) }
  $cleanup['websocketConfigRestored']=(Sha256-Hex ([IO.File]::ReadAllBytes($wsConfig)))-eq $before.websocketConfigSha256
  $cleanup['globalIniRestored']=(Sha256-Hex ([IO.File]::ReadAllBytes($globalIni)))-eq $before.globalIniSha256
  $cleanup['profileIniRestored']=(Sha256-Hex ([IO.File]::ReadAllBytes($profileIni)))-eq $before.profileIniSha256
  $cleanup['sceneCollectionRestored']=(Sha256-Hex ([IO.File]::ReadAllBytes($sceneJson)))-eq $before.sceneCollectionSha256
}

$result=[ordered]@{
  schemaVersion=1; kind='ordivon.media.obs-live-relay-session'; episodeSucceeded=$episodeSucceeded
  obsVersion=[string]$version.obsVersion; obsWebSocketVersion=[string]$version.obsWebSocketVersion; rpcVersion=$version.rpcVersion
  authenticationRequired=$true; publicStreaming=$false; sourceProgramme='live-relay-001'
  originalProgramSceneRestored=$true; temporarySceneCount=$createdScenes.Count; audioInputMuteStatesRestored=$true
  recordingOutputPath=$recordOutput; timeline=$timeline; observedEvents=$events; beforeState=$before; cleanup=$cleanup
}
$json=$result | ConvertTo-Json -Depth 20
[IO.File]::WriteAllText($SessionJson,$json+$([Environment]::NewLine),$utf8NoBom)
if(-not $episodeSucceeded -or $cleanup.obsProcessCountAfter -ne 0 -or $cleanup.listener4455After -or -not $cleanup.globalIniRestored -or -not $cleanup.profileIniRestored -or -not $cleanup.sceneCollectionRestored -or -not $cleanup.websocketConfigRestored){exit 4}
