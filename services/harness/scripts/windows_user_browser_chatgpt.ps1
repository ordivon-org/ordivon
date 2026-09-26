[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('classify','materialize','reconcile')][string]$Mode,
    [string]$EffectId,
    [string]$RequestDigest,
    [string]$PromptPath,
    [string]$PromptDigest,
    [string]$AttachmentManifestPath,
    [string]$AttachmentManifestDigest,
    [string]$StageRoot,
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

function Get-Root([System.Diagnostics.Process]$Process) {
    return [System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$Process.MainWindowHandle)
}

function Get-EditById($Root,[string]$AutomationId) {
    $cond=[System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::AutomationIdProperty,$AutomationId)
    return $Root.FindFirst([System.Windows.Automation.TreeScope]::Descendants,$cond)
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
    return $best
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
        Start-Sleep -Seconds 8
        $root=Get-Root $browser
        $names=Read-AllNames $root
        if($names -match '(?i)cloudflare|just a moment|security check|verify you are human'){ Emit-Classification 'CHALLENGE_GATED' 'provider challenge observed before effect'; exit 0 }
        $composer=Get-EditById $root 'prompt-textarea'
        if($null -ne $composer){ Emit-Classification 'READY' 'authenticated ChatGPT composer available'; exit 0 }
        if($names -match '(?i)log in|sign up'){ Emit-Classification 'AUTH_REQUIRED' 'ChatGPT authentication required'; exit 0 }
        Emit-Classification 'UNKNOWN' 'ChatGPT page reached without composer or explicit authentication/challenge signal'
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
    if($manifest.schemaVersion -ne 1 -or $manifest.kind -ne 'ordivon.user-browser-attachment-manifest' -or @($manifest.attachments).Count -ne 1){
        Emit-Receipt 'pre-effect-failed' $null 'user-browser:attachment-manifest-unsupported' $false 'attachment-manifest-unsupported'
        exit 0
    }
    $attachment=@($manifest.attachments)[0]
    $relative=[string]$attachment.stagingRelativePath
    if([string]::IsNullOrWhiteSpace($relative) -or [IO.Path]::IsPathRooted($relative) -or $relative -match '(^|/)\.\.(/|$)' -or $relative.Contains('\')){
        Emit-Receipt 'pre-effect-failed' $null 'user-browser:attachment-relative-path-invalid' $false 'attachment-relative-path-invalid'
        exit 0
    }
    $rootFull=[IO.Path]::GetFullPath($StageRoot).TrimEnd('\')
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
    Start-Sleep -Seconds 8
    $root=Get-Root $browser
    $names=Read-AllNames $root
    if($names -match '(?i)cloudflare|just a moment|security check|verify you are human'){
        Emit-Receipt 'pre-effect-failed' $null 'provider-boundary:CHALLENGE_GATED' $false 'challenge-gated'
        exit 0
    }
    $composer=Get-EditById $root 'prompt-textarea'
    if($null -eq $composer){
        if($names -match '(?i)log in|sign up'){
            Emit-Receipt 'human-required' $null 'provider-boundary:AUTH_REQUIRED' $false 'auth-required'
        } else {
            Emit-Receipt 'pre-effect-failed' $null 'user-browser:composer-unavailable' $false 'composer-unavailable'
        }
        exit 0
    }
    if($null -ne $attachment){
        Upload-ExactAttachment $browser $root ([string]$attachment.resolvedPath) ([string]$attachment.presentationName)
        $root=Get-Root $browser
        $composer=Get-EditById $root 'prompt-textarea'
        if($null -eq $composer){throw 'composer unavailable after attachment upload'}
    }
    $prompt=[IO.File]::ReadAllText($PromptPath,[Text.Encoding]::UTF8)
    $composer.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue($prompt)
    Start-Sleep -Milliseconds 700
    $root=Get-Root $browser
    $buttonCond=[System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Button)
    $buttons=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$buttonCond)
    $send=$null
    for($i=0;$i -lt $buttons.Count;$i++){
        $b=$buttons.Item($i)
        $id=[string]$b.Current.AutomationId
        $name=[string]$b.Current.Name
        if($id -eq 'composer-submit-button' -or $name -match '(?i)^send|send prompt|submit'){$send=$b;break}
    }
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
        $current=Get-EditById $root 'prompt-textarea'
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
