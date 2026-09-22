[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('classify','materialize','reconcile')][string]$Mode,
    [string]$EffectId,
    [string]$RequestDigest,
    [string]$PromptPath,
    [string]$PromptDigest,
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
    $evidence=Get-Sha256Text ($EffectId+'|'+$RequestDigest+'|'+$PromptDigest+'|'+$Standing+'|'+$EvidenceSeed)
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
    $deadline=(Get-Date).AddSeconds(20)
    while((Get-Date) -lt $deadline){
        Start-Sleep -Milliseconds 500
        $root=Get-Root $browser
        $url=Get-AddressValue $root
        if($url -match '^https://chatgpt\.com/c/[^/?#]+'){$resource=$Matches[0]}
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
