[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('classify','materialize','reconcile','observe','release')][string]$Mode,
    [string]$EffectId,
    [string]$RequestDigest,
    [string]$PromptPath,
    [string]$PromptDigest,
    [string]$AttachmentManifestPath,
    [string]$AttachmentManifestDigest,
    [string]$StageRoot,
    [string]$TargetResource,
    [string]$OutputBeginMarker='ORDIVON_AGENT_OUTPUT_BEGIN',
    [string]$OutputEndMarker='ORDIVON_AGENT_OUTPUT_END',
    [Parameter(Mandatory=$true)][string]$ProxyUrl,
    [string]$ChromePath='C:\Program Files\Google\Chrome\Application\chrome.exe'
)

$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

function Get-Sha256Text([string]$Text) {
    $sha=[System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes=[Text.Encoding]::UTF8.GetBytes($Text)
        $hash=$sha.ComputeHash($bytes)
        return 'sha256:' + (($hash | ForEach-Object {$_.ToString('x2')}) -join '')
    } finally { $sha.Dispose() }
}

function Emit-Receipt(
    [string]$Standing, [string]$ProviderResource, [string]$Detail,
    [bool]$ProviderEffectAttempted, [string]$EvidenceSeed
) {
    $resource=$null
    if($ProviderResource){$resource=$ProviderResource}
    $evidence=Get-Sha256Text ($EffectId+'|'+$RequestDigest+'|'+$PromptDigest+'|'+$AttachmentManifestDigest+'|'+$Standing+'|'+$EvidenceSeed)
    [ordered]@{
        schemaVersion=1
        kind='ordivon.windows-user-browser-attempt'
        effectId=$EffectId
        standing=$Standing
        providerResource=$resource
        evidenceDigest=$evidence
        detail=$Detail
        providerEffectAttempted=$ProviderEffectAttempted
    } | ConvertTo-Json -Compress
}


function Emit-Classification([string]$Standing,[string]$Detail) {
    [ordered]@{
        schemaVersion=1
        kind='ordivon.windows-user-browser-classification'
        standing=$Standing
        detail=$Detail
        providerEffectAttempted=$false
    } | ConvertTo-Json -Compress
}

function Emit-OutputObservation([string]$Standing,[string]$ProviderResource,[string]$Detail,[string]$AssistantOutput) {
    $output=$null
    $outputDigest=$null
    if(-not [string]::IsNullOrEmpty($AssistantOutput)){$output=$AssistantOutput;$outputDigest=Get-Sha256Text $AssistantOutput}
    $evidence=Get-Sha256Text ($EffectId+'|'+$RequestDigest+'|'+$PromptDigest+'|'+$TargetResource+'|'+$Standing+'|'+$outputDigest)
    [ordered]@{
        schemaVersion=1
        kind='ordivon.windows-user-browser-output-observation'
        effectId=$EffectId
        targetResource=$TargetResource
        observedResource=$ProviderResource
        standing=$Standing
        detail=$Detail
        expectedPromptDigest=$PromptDigest
        assistantOutput=$output
        assistantOutputDigest=$outputDigest
        evidenceDigest=$evidence
        providerEffectAttempted=$false
        composerFilled=$false
        sendAttempted=$false
    } | ConvertTo-Json -Compress -Depth 8
}

function Emit-ReleaseReceipt([string]$Standing,[string]$ProviderResource,[string]$Detail) {
    $evidence=Get-Sha256Text ($EffectId+'|'+$TargetResource+'|'+$Standing+'|'+$ProviderResource)
    [ordered]@{
        schemaVersion=1
        kind='ordivon.windows-user-browser-release'
        effectId=$EffectId
        targetResource=$TargetResource
        observedResource=$ProviderResource
        standing=$Standing
        detail=$Detail
        evidenceDigest=$evidence
        providerEffectAttempted=$false
        sendAttempted=$false
    } | ConvertTo-Json -Compress
}

function Get-Root([System.Diagnostics.Process]$Process) {
    return [System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$Process.MainWindowHandle)
}

function Get-EditById($Root,[string]$AutomationId) {
    $cond=[System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::AutomationIdProperty,$AutomationId)
    return $Root.FindFirst([System.Windows.Automation.TreeScope]::Descendants,$cond)
}

function Get-WebRoot($Root) {
    return Get-EditById $Root 'RootWebArea'
}

function Get-ElementKey($Element) {
    if($null -eq $Element){return $null}
    try{return (@($Element.GetRuntimeId()) -join '.')}catch{return $null}
}

function Get-Composer($Root) {
    $legacy=Get-EditById $Root 'prompt-textarea'
    if($null -ne $legacy -and $legacy.Current.IsEnabled -and $legacy.Current.IsKeyboardFocusable){return $legacy}
    $web=Get-WebRoot $Root
    if($null -eq $web){return $null}
    $cond=[System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Edit)
    $edits=$web.FindAll([System.Windows.Automation.TreeScope]::Descendants,$cond)
    $usable=New-Object System.Collections.Generic.List[object]
    for($i=0;$i -lt $edits.Count;$i++){
        $candidate=$edits.Item($i)
        if(-not $candidate.Current.IsEnabled -or -not $candidate.Current.IsKeyboardFocusable){continue}
        $pattern=$null
        if($candidate.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$pattern)){$usable.Add($candidate)}
    }
    if($usable.Count -eq 1){return $usable[0]}
    return $null
}

function Test-AccountChooser($Root) {
    $buttonCond=[System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Button)
    $buttons=$Root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$buttonCond)
    for($i=0;$i -lt [Math]::Min($buttons.Count,2000);$i++){
        $name=[string]$buttons.Item($i).Current.Name
        # Current ChatGPT account-choice surfaces expose the remembered account as a button whose
        # accessible name contains the account e-mail.  Treat this as an authentication boundary,
        # not as a composer-readiness condition, and never activate it automatically.
        if($name -match '(?i)[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}') { return $true }
    }
    return $false
}

function Get-ChatGptPageState($Root) {
    $names=Read-AllNames $Root
    if($names -match '(?i)ERR_PROXY_CONNECTION_FAILED|ERR_TUNNEL_CONNECTION_FAILED|ERR_CONNECTION_REFUSED'){
        return [pscustomobject]@{Standing='NETWORK_UNAVAILABLE';Composer=$null;Detail='provider proxy/network error page observed'}
    }
    if($names -match '(?i)cloudflare|just a moment|security check|verify you are human'){
        return [pscustomobject]@{Standing='CHALLENGE_GATED';Composer=$null;Detail='provider challenge observed before effect'}
    }
    $composer=Get-Composer $Root
    if($null -ne $composer){
        return [pscustomobject]@{Standing='READY';Composer=$composer;Detail='authenticated ChatGPT composer available'}
    }
    if((Test-AccountChooser $Root) -or $names -match '(?i)log in|sign up|choose an account|select an account|another account|create account|欢迎回来|选择一个账户|登录至另一个账户|创建账户'){
        return [pscustomobject]@{Standing='AUTH_REQUIRED';Composer=$null;Detail='ChatGPT authentication or account selection required'}
    }
    return [pscustomobject]@{Standing='WAIT';Composer=$null;Detail='ChatGPT page not yet ready'}
}

function Wait-ForChatGptPage($Browser,[int]$Seconds=75) {
    $deadline=(Get-Date).AddSeconds($Seconds)
    while((Get-Date) -lt $deadline){
        $root=Get-Root $Browser
        $state=Get-ChatGptPageState $root
        if($state.Standing -ne 'WAIT'){
            return [pscustomobject]@{Standing=$state.Standing;Composer=$state.Composer;Root=$root;Detail=$state.Detail}
        }
        Start-Sleep -Milliseconds 750
    }
    return [pscustomobject]@{Standing='TIMEOUT';Composer=$null;Root=(Get-Root $Browser);Detail='ChatGPT composer readiness deadline exceeded'}
}

function Read-AllNames($Root) {
    $all=$Root.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
    $values=New-Object System.Collections.Generic.List[string]
    for($i=0;$i -lt [Math]::Min($all.Count,6000);$i++){
        $name=[string]$all.Item($i).Current.Name
        if(-not [string]::IsNullOrWhiteSpace($name)){$values.Add($name)}
    }
    return ($values -join [Environment]::NewLine)
}

function Get-AddressValue($Root) {
    $address=Get-EditById $Root 'view_1012'
    if($null -eq $address){return $null}
    try {
        $vp=$address.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
        return [string]$vp.Current.Value
    } catch { return $null }
}


function Invoke-UiElement($Element,[string]$Purpose) {
    $pattern=$null
    if($Element.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$pattern)){
        ([System.Windows.Automation.InvokePattern]$pattern).Invoke()
        return 'InvokePattern'
    }
    $pattern=$null
    if($Element.TryGetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern,[ref]$pattern)){
        $expand=[System.Windows.Automation.ExpandCollapsePattern]$pattern
        if($expand.Current.ExpandCollapseState -ne [System.Windows.Automation.ExpandCollapseState]::Expanded){
            $expand.Expand()
        }
        return 'ExpandCollapsePattern'
    }
    $pattern=$null
    if($Element.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$pattern)){
        ([System.Windows.Automation.SelectionItemPattern]$pattern).Select()
        return 'SelectionItemPattern'
    }
    $pattern=$null
    if($Element.TryGetCurrentPattern([System.Windows.Automation.LegacyIAccessiblePattern]::Pattern,[ref]$pattern)){
        ([System.Windows.Automation.LegacyIAccessiblePattern]$pattern).DoDefaultAction()
        return 'LegacyIAccessiblePattern'
    }
    $supported=@($Element.GetSupportedPatterns() | ForEach-Object {[string]$_.ProgrammaticName}) -join ','
    throw ($Purpose+' control exposes no supported activation pattern; supported='+$supported)
}

function Get-UploadControl($Root) {
    $all=$Root.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
    $best=$null
    $bestScore=-1
    for($i=0;$i -lt [Math]::Min($all.Count,6000);$i++){
        $item=$all.Item($i)
        $name=[string]$item.Current.Name
        $id=[string]$item.Current.AutomationId
        $type=$item.Current.ControlType
        if($type -ne [System.Windows.Automation.ControlType]::Button -and $type -ne [System.Windows.Automation.ControlType]::MenuItem){continue}
        if($id -notmatch '(?i)attach|upload|composer-plus' -and $name -notmatch '(?i)attach|add photos.*files|upload.*file|add.*file'){continue}
        $score=0
        if($type -eq [System.Windows.Automation.ControlType]::MenuItem){$score+=50}
        if($name -match '(?i)add photos.*files|upload.*file|attach.*file|add.*file'){$score+=100}
        if($id -match '(?i)attach|upload'){$score+=40}
        if($id -match '(?i)composer-plus'){$score+=10}
        if($score -gt $bestScore){$best=$item;$bestScore=$score}
    }
    if($null -ne $best){return $best}
    $web=Get-WebRoot $Root
    $composer=Get-Composer $Root
    if($null -eq $web -or $null -eq $composer){return $null}
    $composerKey=Get-ElementKey $composer
    if([string]::IsNullOrWhiteSpace($composerKey)){return $null}
    $webAll=$web.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
    $index=-1
    for($i=0;$i -lt [Math]::Min($webAll.Count,6000);$i++){if((Get-ElementKey $webAll.Item($i)) -eq $composerKey){$index=$i;break}}
    if($index -lt 0){return $null}
    $cr=$composer.Current.BoundingRectangle
    for($i=$index-1;$i -ge [Math]::Max(0,$index-12);$i--){
        $candidate=$webAll.Item($i)
        if($candidate.Current.ControlType -ne [System.Windows.Automation.ControlType]::Button){continue}
        if(-not $candidate.Current.IsEnabled){continue}
        $br=$candidate.Current.BoundingRectangle
        if($br.Width -le 0 -or $br.Height -le 0){continue}
        $dy=[Math]::Abs(($br.Y+$br.Height/2)-($cr.Y+$cr.Height/2))
        if($dy -le [Math]::Max(90,$cr.Height*2) -and $br.X -le ($cr.X+40)){return $candidate}
    }
    return $null
}

function Get-SendControl($Root,$Composer) {
    $buttonCond=[System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Button)
    $buttons=$Root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$buttonCond)
    for($i=0;$i -lt $buttons.Count;$i++){
        $b=$buttons.Item($i)
        $id=[string]$b.Current.AutomationId
        $name=[string]$b.Current.Name
        if($id -eq 'composer-submit-button' -or $name -match '(?i)^send|send prompt|submit'){return $b}
    }
    if($null -eq $Composer){return $null}
    $cr=$Composer.Current.BoundingRectangle
    $candidate=$null
    $right=-1.0
    for($i=0;$i -lt $buttons.Count;$i++){
        $b=$buttons.Item($i)
        if(-not $b.Current.IsEnabled){continue}
        $br=$b.Current.BoundingRectangle
        if($br.Width -le 0 -or $br.Height -le 0){continue}
        $dy=[Math]::Abs(($br.Y+$br.Height/2)-($cr.Y+$cr.Height/2))
        if($dy -gt [Math]::Max(90,$cr.Height*2)){continue}
        if($br.X -lt ($cr.X+$cr.Width*0.55)){continue}
        if($br.X -gt $right){$candidate=$b;$right=$br.X}
    }
    return $candidate
}

function Get-FileDialog() {
    $desktop=[System.Windows.Automation.AutomationElement]::RootElement
    $cond=[System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Window)
    $windows=$desktop.FindAll([System.Windows.Automation.TreeScope]::Descendants,$cond)
    for($i=0;$i -lt [Math]::Min($windows.Count,300);$i++){
        $window=$windows.Item($i)
        $name=[string]$window.Current.Name
        if($name -match '(?i)^open$|choose.*file|select.*file|file upload'){ return $window }
        $fileEdit=Get-EditById $window '1148'
        $openButton=Get-EditById $window '1'
        if($null -ne $fileEdit -and $null -ne $openButton){return $window}
    }
    return $null
}

function Set-FileDialogPath($Dialog,[string]$Path) {
    $editCond=[System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Edit)
    $edits=$Dialog.FindAll([System.Windows.Automation.TreeScope]::Descendants,$editCond)
    $fileEdit=$null
    for($i=0;$i -lt $edits.Count;$i++){
        $candidate=$edits.Item($i)
        $id=[string]$candidate.Current.AutomationId
        $name=[string]$candidate.Current.Name
        if($id -eq '1148' -or $name -match '(?i)file name'){ $fileEdit=$candidate; break }
    }
    if($null -eq $fileEdit -and $edits.Count -gt 0){$fileEdit=$edits.Item($edits.Count-1)}
    if($null -eq $fileEdit){throw 'file dialog path editor unavailable'}
    $fileEdit.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue($Path)

    $buttonCond=[System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Button)
    $buttons=$Dialog.FindAll([System.Windows.Automation.TreeScope]::Descendants,$buttonCond)
    $open=$null
    for($i=0;$i -lt $buttons.Count;$i++){
        $candidate=$buttons.Item($i)
        $id=[string]$candidate.Current.AutomationId
        $name=[string]$candidate.Current.Name
        if($id -eq '1' -or $name -match '(?i)^open$|^choose$|^select$'){ $open=$candidate; break }
    }
    if($null -eq $open){throw 'file dialog Open control unavailable'}
    $script:providerEffectAttempted=$true
    Invoke-UiElement $open 'file dialog Open' | Out-Null
}

function Upload-ExactAttachment($Browser,$Root,[string]$Path,[string]$PresentationName) {
    $control=Get-UploadControl $Root
    if($null -eq $control){throw 'attachment control unavailable before provider effect'}
    Invoke-UiElement $control 'attachment entry' | Out-Null
    Start-Sleep -Milliseconds 700
    $dialog=Get-FileDialog
    if($null -eq $dialog){
        $root2=Get-Root $Browser
        $menu=Get-UploadControl $root2
        if($null -ne $menu){
            try{Invoke-UiElement $menu 'attachment upload menu' | Out-Null}catch{}
            Start-Sleep -Milliseconds 700
            $dialog=Get-FileDialog
        }
    }
    if($null -eq $dialog){throw 'attachment file dialog unavailable'}
    Set-FileDialogPath $dialog $Path
    $deadline=(Get-Date).AddSeconds(25)
    while((Get-Date) -lt $deadline){
        Start-Sleep -Milliseconds 500
        $root2=Get-Root $Browser
        $names=Read-AllNames $root2
        if($names -match [regex]::Escape($PresentationName)){return}
    }
    throw 'attachment upload was not visibly acknowledged by provider UI'
}

function Get-CanonicalChatResource([string]$Address) {
    if([string]::IsNullOrWhiteSpace($Address)){return $null}
    $value=$Address.Trim()
    if($value -match '^(?:https://)?chatgpt\.com/c/([^/?#\s]+)'){
        $conversationId=$Matches[1]
        if($conversationId.StartsWith('WEB:')){return $null}
        if($conversationId -notmatch '^[A-Za-z0-9_-]{8,256}$'){return $null}
        return 'https://chatgpt.com/c/' + $conversationId
    }
    return $null
}

if($Mode -eq 'observe' -or $Mode -eq 'release'){
    if([string]::IsNullOrWhiteSpace($EffectId) -or [string]::IsNullOrWhiteSpace($TargetResource)){
        throw 'EffectId and TargetResource are required for observe/release'
    }
    if(-not (Test-Path -LiteralPath $ChromePath -PathType Leaf)){
        if($Mode -eq 'observe'){Emit-OutputObservation 'CARRIER_UNAVAILABLE' $null 'normal Chrome executable unavailable' $null}
        else{Emit-ReleaseReceipt 'CARRIER_UNAVAILABLE' $null 'normal Chrome executable unavailable'}
        exit 0
    }
    $windows=@(Get-Process chrome -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowHandle -ne 0})
    if($windows.Count -eq 0){
        if($Mode -eq 'release'){Emit-ReleaseReceipt 'ALREADY_RELEASED' $null 'no normal Chrome main window remains'}
        else{Emit-OutputObservation 'CARRIER_UNAVAILABLE' $null 'no normal Chrome main window is available' $null}
        exit 0
    }
    if($windows.Count -ne 1){
        if($Mode -eq 'release'){Emit-ReleaseReceipt 'AMBIGUOUS_CARRIER' $null 'multiple normal Chrome main windows are present'}
        else{Emit-OutputObservation 'AMBIGUOUS_CARRIER' $null 'multiple normal Chrome main windows are present' $null}
        exit 0
    }
    $browser=$windows[0]
    $root=Get-Root $browser
    $observedResource=Get-CanonicalChatResource (Get-AddressValue $root)
    if($observedResource -ne $TargetResource){
        if($Mode -eq 'release'){Emit-ReleaseReceipt 'TARGET_RESOURCE_MISMATCH' $observedResource 'normal Chrome is not bound to the expected provider resource'}
        else{Emit-OutputObservation 'TARGET_RESOURCE_MISMATCH' $observedResource 'normal Chrome is not bound to the expected provider resource' $null}
        exit 0
    }
    if($Mode -eq 'observe'){
        if([string]::IsNullOrWhiteSpace($PromptDigest)){throw 'PromptDigest is required for observe'}
        $deadline=(Get-Date).AddSeconds(180)
        $names=''
        while((Get-Date) -lt $deadline){
            $root=Get-Root $browser
            $names=Read-AllNames $root
            if($names.Contains('EFFECT_ID='+$EffectId) -and $names.Contains($OutputBeginMarker) -and $names.Contains($OutputEndMarker)){break}
            Start-Sleep -Milliseconds 750
        }
        if(-not $names.Contains('EFFECT_ID='+$EffectId)){
            Emit-OutputObservation 'EXPECTED_USER_TURN_NOT_VISIBLE' $observedResource 'exact effect marker is not visible in the target conversation' $null
            exit 0
        }
        $begin=$names.LastIndexOf($OutputBeginMarker,[StringComparison]::Ordinal)
        $end=$names.IndexOf($OutputEndMarker,$begin+[Math]::Max(1,$OutputBeginMarker.Length),[StringComparison]::Ordinal)
        if($begin -lt 0 -or $end -lt 0){
            Emit-OutputObservation 'ASSISTANT_OUTPUT_NOT_COMPLETE' $observedResource 'output markers are not both visible before observation deadline' $null
            exit 0
        }
        $start=$begin+$OutputBeginMarker.Length
        $assistant=$names.Substring($start,$end-$start).Trim()
        if([string]::IsNullOrWhiteSpace($assistant)){
            Emit-OutputObservation 'ASSISTANT_OUTPUT_EMPTY' $observedResource 'output markers are visible but payload is empty' $null
            exit 0
        }
        Emit-OutputObservation 'CAPTURED' $observedResource 'exact marked assistant output captured read-only' $assistant
        exit 0
    }
    $names=Read-AllNames $root
    if(-not $names.Contains($OutputEndMarker)){
        Emit-ReleaseReceipt 'OUTPUT_NOT_COMPLETE' $observedResource 'refusing carrier release before marked assistant output is complete'
        exit 0
    }
    $ownedStart=$browser.StartTime.AddSeconds(-3)
    $owned=@(Get-Process chrome -ErrorAction SilentlyContinue | Where-Object {$_.StartTime -ge $ownedStart})
    foreach($proc in $owned){try{Stop-Process -Id $proc.Id -Force -ErrorAction Stop}catch{}}
    $deadline=(Get-Date).AddSeconds(8)
    while((Get-Date) -lt $deadline){
        $remaining=@(Get-Process chrome -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowHandle -ne 0})
        if($remaining.Count -eq 0){break}
        Start-Sleep -Milliseconds 250
    }
    $remaining=@(Get-Process chrome -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowHandle -ne 0})
    if($remaining.Count -eq 0){Emit-ReleaseReceipt 'RELEASED' $observedResource 'exact target conversation carrier released after completed output capture'}
    else{Emit-ReleaseReceipt 'RELEASE_INCOMPLETE' $observedResource 'normal Chrome main window remains after targeted carrier release'}
    exit 0
}

if(-not (Test-Path -LiteralPath $ChromePath -PathType Leaf)){
    if($Mode -eq 'classify'){
        Emit-Classification 'UNKNOWN' 'normal Chrome executable unavailable'
    } else {
        Emit-Receipt 'pre-effect-failed' $null 'user-browser:chrome-unavailable' $false 'chrome-unavailable'
    }
    exit 0
}
if($Mode -ne 'classify' -and ([string]::IsNullOrWhiteSpace($EffectId) -or [string]::IsNullOrWhiteSpace($RequestDigest))){
    throw 'EffectId and RequestDigest are required outside classify mode'
}
if($Mode -eq 'classify'){
    $existing=@(Get-Process chrome -ErrorAction SilentlyContinue)
    if($existing.Count -gt 0){
        Emit-Classification 'BUSY' 'normal Chrome already running; qualification will not take over existing browser'
        exit 0
    }
    try {
        $args=@('--new-window','--force-renderer-accessibility','--disable-session-crashed-bubble','--no-first-run','--disable-quic',('--proxy-server='+$ProxyUrl),'about:blank')
        Start-Process -FilePath $ChromePath -ArgumentList $args | Out-Null
        $deadline=(Get-Date).AddSeconds(12)
        $browser=$null
        while((Get-Date) -lt $deadline){
            $browser=@(Get-Process chrome -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowHandle -ne 0} | Sort-Object StartTime -Descending | Select-Object -First 1)
            if($browser.Count -eq 1){break}
            Start-Sleep -Milliseconds 250
        }
        if($null -eq $browser -or $browser.Count -ne 1){ Emit-Classification 'UNKNOWN' 'normal Chrome window unavailable'; exit 0 }
        $browser=$browser[0]
        $root=Get-Root $browser
        $address=Get-EditById $root 'view_1012'
        if($null -eq $address){ Emit-Classification 'UNKNOWN' 'normal Chrome address bar unavailable'; exit 0 }
        $address.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue('https://chatgpt.com/')
        $address.SetFocus()
        Start-Sleep -Milliseconds 700
        $listCond=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::ListItem)
        $items=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$listCond)
        $choice=$null
        for($i=0;$i -lt $items.Count;$i++){ if(([string]$items.Item($i).Current.Name) -like 'https://chatgpt.com*'){$choice=$items.Item($i);break} }
        if($null -eq $choice){ Emit-Classification 'UNKNOWN' 'ChatGPT navigation choice unavailable'; exit 0 }
        $choice.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
        $page=Wait-ForChatGptPage $browser 75
        if($page.Standing -eq 'READY'){Emit-Classification 'READY' $page.Detail;exit 0}
        if($page.Standing -eq 'CHALLENGE_GATED'){Emit-Classification 'CHALLENGE_GATED' $page.Detail;exit 0}
        if($page.Standing -eq 'AUTH_REQUIRED'){Emit-Classification 'AUTH_REQUIRED' $page.Detail;exit 0}
        if($page.Standing -eq 'NETWORK_UNAVAILABLE'){Emit-Classification 'UNKNOWN' $page.Detail;exit 0}
        Emit-Classification 'UNKNOWN' $page.Detail
    } catch {
        $detail=('classification '+$_.Exception.GetType().Name+': '+$_.Exception.Message)
        if($detail.Length -gt 800){$detail=$detail.Substring(0,800)}
        Emit-Classification 'UNKNOWN' $detail
    }
    exit 0
}

if(-not $PromptPath -or -not (Test-Path -LiteralPath $PromptPath -PathType Leaf)){
    Emit-Receipt 'pre-effect-failed' $null 'user-browser:prompt-unavailable' $false 'prompt-unavailable'
    exit 0
}
$observedPrompt='sha256:' + (Get-FileHash -LiteralPath $PromptPath -Algorithm SHA256).Hash.ToLowerInvariant()
if(-not $PromptDigest -or $observedPrompt -ne $PromptDigest){
    Emit-Receipt 'pre-effect-failed' $null 'user-browser:prompt-digest-mismatch' $false 'prompt-digest-mismatch'
    exit 0
}
$attachment=$null
if($AttachmentManifestPath -or $AttachmentManifestDigest -or $StageRoot){
    if(-not $AttachmentManifestPath -or -not $AttachmentManifestDigest -or -not $StageRoot -or -not (Test-Path -LiteralPath $AttachmentManifestPath -PathType Leaf)){
        Emit-Receipt 'pre-effect-failed' $null 'user-browser:attachment-manifest-unavailable' $false 'attachment-manifest-unavailable'
        exit 0
    }
    $observedManifest='sha256:' + (Get-FileHash -LiteralPath $AttachmentManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if($observedManifest -ne $AttachmentManifestDigest){
        Emit-Receipt 'pre-effect-failed' $null 'user-browser:attachment-manifest-digest-mismatch' $false 'attachment-manifest-digest-mismatch'
        exit 0
    }
    try{$manifest=Get-Content -LiteralPath $AttachmentManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json}catch{
        Emit-Receipt 'pre-effect-failed' $null 'user-browser:attachment-manifest-invalid' $false 'attachment-manifest-invalid'; exit 0
    }
    $manifestAttachments=@($manifest.attachments)
    if($manifest.schemaVersion -ne 1 -or $manifest.kind -ne 'ordivon.user-browser-attachment-manifest' -or $manifestAttachments.Count -lt 1 -or $manifestAttachments.Count -gt 4){
        Emit-Receipt 'pre-effect-failed' $null 'user-browser:attachment-manifest-unsupported' $false 'attachment-manifest-unsupported'
        exit 0
    }
    $attachments=New-Object System.Collections.Generic.List[object]
    $rootFull=[IO.Path]::GetFullPath($StageRoot).TrimEnd('\')
    foreach($attachment in $manifestAttachments){
        $relative=[string]$attachment.stagingRelativePath
        if([string]::IsNullOrWhiteSpace($relative) -or [IO.Path]::IsPathRooted($relative) -or $relative -match '(^|/)\.\.(/|$)' -or $relative.Contains('\')){
            Emit-Receipt 'pre-effect-failed' $null 'user-browser:attachment-relative-path-invalid' $false 'attachment-relative-path-invalid'
            exit 0
        }
        $attachmentPath=[IO.Path]::GetFullPath((Join-Path $rootFull ($relative -replace '/','\')))
        if(-not $attachmentPath.StartsWith($rootFull+'\',[StringComparison]::OrdinalIgnoreCase) -or -not (Test-Path -LiteralPath $attachmentPath -PathType Leaf)){
            Emit-Receipt 'pre-effect-failed' $null 'user-browser:attachment-path-unavailable' $false 'attachment-path-unavailable'
            exit 0
        }
        $observedAttachment='sha256:' + (Get-FileHash -LiteralPath $attachmentPath -Algorithm SHA256).Hash.ToLowerInvariant()
        if($observedAttachment -ne [string]$attachment.digest){
            Emit-Receipt 'pre-effect-failed' $null 'user-browser:attachment-digest-mismatch' $false 'attachment-digest-mismatch'
            exit 0
        }
        $attachment | Add-Member -NotePropertyName resolvedPath -NotePropertyValue $attachmentPath -Force
        $attachments.Add($attachment)
    }
}
if($Mode -eq 'reconcile'){
    Emit-Receipt 'unknown' $null 'user-browser:reconcile-has-no-exact-provider-binding-evidence; resend-forbidden' $true 'reconcile-no-binding'
    exit 0
}

$existing=@(Get-Process chrome -ErrorAction SilentlyContinue)
if($existing.Count -gt 0){
    Emit-Receipt 'pre-effect-failed' $null 'user-browser:chrome-already-running; carrier-will-not-take-over-existing-browser' $false 'chrome-busy'
    exit 0
}

$providerEffectAttempted=$false
try {
    $args=@(
        '--new-window',
        '--force-renderer-accessibility',
        '--disable-session-crashed-bubble',
        '--no-first-run',
        '--disable-quic',
        ('--proxy-server='+$ProxyUrl),
        'about:blank'
    )
    Start-Process -FilePath $ChromePath -ArgumentList $args | Out-Null
    $deadline=(Get-Date).AddSeconds(12)
    $browser=$null
    while((Get-Date) -lt $deadline){
        $browser=@(Get-Process chrome -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowHandle -ne 0} | Sort-Object StartTime -Descending | Select-Object -First 1)
        if($browser.Count -eq 1){break}
        Start-Sleep -Milliseconds 250
    }
    if($null -eq $browser -or $browser.Count -ne 1){
        Emit-Receipt 'pre-effect-failed' $null 'user-browser:chrome-window-unavailable' $false 'window-unavailable'
        exit 0
    }
    $browser=$browser[0]
    $root=Get-Root $browser
    $address=Get-EditById $root 'view_1012'
    if($null -eq $address){
        Emit-Receipt 'pre-effect-failed' $null 'user-browser:address-bar-unavailable' $false 'address-unavailable'
        exit 0
    }
    $address.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue('https://chatgpt.com/')
    $address.SetFocus()
    Start-Sleep -Milliseconds 700
    $listCond=[System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::ListItem)
    $items=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$listCond)
    $choice=$null
    for($i=0;$i -lt $items.Count;$i++){
        if(([string]$items.Item($i).Current.Name) -like 'https://chatgpt.com*'){$choice=$items.Item($i);break}
    }
    if($null -eq $choice){
        Emit-Receipt 'pre-effect-failed' $null 'user-browser:chatgpt-navigation-choice-unavailable' $false 'nav-choice-unavailable'
        exit 0
    }
    $choice.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
    $page=Wait-ForChatGptPage $browser 75
    $root=$page.Root
    $composer=$page.Composer
    if($page.Standing -eq 'CHALLENGE_GATED'){
        Emit-Receipt 'pre-effect-failed' $null 'provider-boundary:CHALLENGE_GATED' $false 'challenge-gated';exit 0
    }
    if($page.Standing -eq 'AUTH_REQUIRED'){
        Emit-Receipt 'human-required' $null 'provider-boundary:AUTH_REQUIRED' $false 'auth-required';exit 0
    }
    if($page.Standing -eq 'NETWORK_UNAVAILABLE'){
        Emit-Receipt 'pre-effect-failed' $null 'user-browser:provider-network-unavailable' $false 'provider-network-unavailable';exit 0
    }
    if($page.Standing -ne 'READY' -or $null -eq $composer){
        Emit-Receipt 'pre-effect-failed' $null 'user-browser:composer-readiness-timeout' $false 'composer-readiness-timeout';exit 0
    }
    if($null -ne $attachments){
        foreach($attachment in $attachments){
            Upload-ExactAttachment $browser $root ([string]$attachment.resolvedPath) ([string]$attachment.presentationName)
            $root=Get-Root $browser
            $composer=Get-Composer $root
            if($null -eq $composer){throw 'composer unavailable after attachment upload'}
        }
    }
    $prompt=[IO.File]::ReadAllText($PromptPath,[Text.Encoding]::UTF8)
    $composer.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue($prompt)
    Start-Sleep -Milliseconds 700
    $root=Get-Root $browser
    $send=Get-SendControl $root $composer
    if($null -eq $send){
        $composer.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue('')
        Emit-Receipt 'pre-effect-failed' $null 'user-browser:send-control-unavailable' $false 'send-unavailable'
        exit 0
    }
    $providerEffectAttempted=$true
    $send.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
    $resource=$null
    $composerCleared=$false
    $deadline=(Get-Date).AddSeconds(90)
    while((Get-Date) -lt $deadline){
        Start-Sleep -Milliseconds 500
        $root=Get-Root $browser
        $url=Get-AddressValue $root
        $resource=Get-CanonicalChatResource $url
        $current=Get-Composer $root
        if($null -ne $current){
            try {
                $v=$current.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
                if([string]::IsNullOrEmpty([string]$v.Current.Value)){$composerCleared=$true}
            } catch {}
        }
        if($resource){break}
    }
    if($resource){
        Emit-Receipt 'bound' $resource 'normal Chrome submit observed and provider-bound' $true $resource
    } elseif($composerCleared){
        Emit-Receipt 'submit-observed' $null 'normal Chrome submit observed without stable provider coordinate' $true 'composer-cleared'
    } else {
        Emit-Receipt 'unknown' $null 'normal Chrome effect outcome ambiguous after SEND boundary' $true 'post-send-ambiguous'
    }
} catch {
    $detail=('user-browser:'+($_.Exception.GetType().Name)+': '+$_.Exception.Message)
    if($detail.Length -gt 800){$detail=$detail.Substring(0,800)}
    if($providerEffectAttempted){
        Emit-Receipt 'unknown' $null $detail $true 'exception-after-send'
    } else {
        Emit-Receipt 'pre-effect-failed' $null $detail $false 'exception-before-send'
    }
}
exit 0
