#requires -version 5.1
<#
Mechanical SCM transition for the existing staged PG Runtime. This does not
certify PG admission, drain, recipient acceptance, or all-issued finality.
Run from an independent, serialized operator session, never from a Job of
either service being switched. The operator must already hold ingress closed
and have consumed the original normal-product and drain evidence.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('Activate','RestoreLegacy')][string]$Direction,
    [Parameter(Mandatory=$true)][string]$LegacyService,
    [Parameter(Mandatory=$true)][string]$PgService,
    [Parameter(Mandatory=$true)][string]$LegacyImagePath,
    [Parameter(Mandatory=$true)][string]$PgImagePath,
    [Parameter(Mandatory=$true)][string]$LegacyAccount,
    [Parameter(Mandatory=$true)][string]$PgAccount,
    [Parameter(Mandatory=$true)][ValidateSet('Automatic','Manual','DelayedAutomatic')][string]$LegacyStartMode,
    [ValidateSet('Automatic','Manual')][string]$PgStartMode='Automatic',
    [Parameter(Mandatory=$true)][uint32]$ExpectedWriterPid,
    [Parameter(Mandatory=$true)][string]$LegacyBinary,
    [Parameter(Mandatory=$true)][string]$ExpectedLegacySha256,
    [Parameter(Mandatory=$true)][string]$PgBinary,
    [Parameter(Mandatory=$true)][string]$ExpectedPgSha256,
    [Parameter(Mandatory=$true)][string]$PgLauncher,
    [Parameter(Mandatory=$true)][string]$ExpectedLauncherSha256,
    [Parameter(Mandatory=$true)][string]$PgEnvironment,
    [Parameter(Mandatory=$true)][string]$ExpectedEnvironmentSha256,
    [ValidateRange(5,120)][int]$TimeoutSeconds=30,
    [string]$PgEndpoint='',
    [string]$ExpectedNodeId='',
    [string]$TokenFile='',
    [string]$PreparedSourceRepo='',
    [string]$PreparedSourceRevision='',
    [string]$AcceptanceRoot='',
    [string]$ExpectedAcceptanceSha256='',
    [ValidateRange(1,65535)][int]$ExpectedActiveUserSessionId=1,
    [switch]$IngressQuiesced,
    [switch]$OriginalConsumerQualified,
    [switch]$OriginalWriterDrained,
    [switch]$Apply
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if ($LegacyService -notmatch '^[A-Za-z0-9_.-]+$' -or
    $PgService -notmatch '^[A-Za-z0-9_.-]+$' -or
    $LegacyService -ieq $PgService) {
    throw 'Two distinct exact SCM service identities are required.'
}
function Get-ExactService([string]$Name) {
    $cim=Get-CimInstance Win32_Service -Filter "Name='$Name'"
    if ($null -eq $cim -or $cim.Name -ine $Name) { throw "Missing exact SCM service: $Name" }
    $sc=Get-Service -Name $Name -ErrorAction Stop
    $mode=[string]$sc.StartType
    if ($mode -eq 'Automatic') {
        $key="HKLM:\SYSTEM\CurrentControlSet\Services\$Name"
        $delayed=Get-ItemProperty -LiteralPath $key -Name DelayedAutoStart -ErrorAction SilentlyContinue
        if ($null -ne $delayed -and $delayed.DelayedAutoStart -eq 1) { $mode='DelayedAutomatic' }
    }
    if ([string]$sc.Status -ne [string]$cim.State) { throw "SCM state changed while reading $Name" }
    [pscustomobject]@{name=$Name;state=[string]$sc.Status;mode=$mode;
        pid=[uint32]$cim.ProcessId;image=[string]$cim.PathName;account=[string]$cim.StartName}
}
function Assert-Identity($Observed,[string]$Image,[string]$Account) {
    if ($Observed.image -cne $Image -or $Observed.account -ine $Account) {
        throw "SCM identity changed: $($Observed.name)"
    }
}
function Assert-Commitment([string]$Path,[string]$Expected) {
    if ($Expected -notmatch '^[0-9A-Fa-f]{64}$' -or -not [IO.Path]::IsPathRooted($Path)) {
        throw 'Invalid absolute file commitment.'
    }
    $item=Get-Item -LiteralPath $Path
    if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
        (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ine $Expected) {
        throw 'SCM candidate file commitment differs.'
    }
}
# Verify the exact hashed configuration bytes bind the carrier that SCM will
# start. Individually valid file hashes do not establish a matching product.
# RestoreLegacy must remain possible after a failed candidate configuration.
function Assert-PgEnvironmentBindings {
    if ($Direction -ne 'Activate') { return }
    $item=Get-Item -LiteralPath $PgEnvironment
    if ($item.Length -gt 65536) { throw 'PG environment exceeds the native parser bound.' }
    $bytes=[IO.File]::ReadAllBytes($PgEnvironment)
    if ($bytes.Length -gt 65536) { throw 'PG environment exceeds the native parser bound.' }
    $sha=[Security.Cryptography.SHA256]::Create()
    try { $digest=([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','') }
    finally { $sha.Dispose() }
    if ($digest -ine $ExpectedEnvironmentSha256) { throw 'PG environment bytes changed during binding.' }
    $utf8=[Text.UTF8Encoding]::new($false,$true)
    $values=@{}
    foreach ($rawLine in ($utf8.GetString($bytes) -split "\r?\n")) {
        $line=$rawLine.Trim()
        if ($line.Length -eq 0 -or $line.StartsWith('#')) { continue }
        $separator=$line.IndexOf('=')
        if ($separator -lt 1) { throw 'Invalid PG environment line.' }
        $key=$line.Substring(0,$separator).Trim()
        $value=$line.Substring($separator+1).Trim()
        if ($key -cnotmatch '^(ORDIVON_[A-Z0-9_]+|RUST_LOG)$' -or $values.ContainsKey($key) -or
            $value.IndexOf([char]0) -ge 0) { throw 'Unsupported or duplicate PG environment key.' }
        $values[$key]=$value
    }
    $expected=@{ORDIVON_PG_RUNNER=$PgLauncher}
    if ($selectedQualification) {
        $expected['ORDIVON_PG_BIND']=([Uri]$PgEndpoint).Authority
        $expected['ORDIVON_NODE_ID']=$ExpectedNodeId
        $expected['ORDIVON_BEARER_TOKEN_FILE']=$TokenFile
    }
    foreach ($key in $expected.Keys) {
        if (-not $values.ContainsKey($key) -or $values[$key] -cne $expected[$key]) {
            throw ('PG environment does not bind the committed activation input: '+$key)
        }
    }
}
function Assert-Commitments {
    Assert-Commitment $LegacyBinary $ExpectedLegacySha256
    Assert-Commitment $PgBinary $ExpectedPgSha256
    Assert-Commitment $PgLauncher $ExpectedLauncherSha256
    Assert-Commitment $PgEnvironment $ExpectedEnvironmentSha256
    Assert-PgEnvironmentBindings
    # Bind the operator's file commitments to the exact installed image paths.
    # Native SCM can omit quotes on whitespace-free paths.
    $exeArgs=@(('"{0}"' -f $PgBinary))
    $envArgs=@(('"{0}"' -f $PgEnvironment))
    if ($PgBinary -notmatch '[\s"]') { $exeArgs += $PgBinary }
    if ($PgEnvironment -notmatch '[\s"]') { $envArgs += $PgEnvironment }
    $images=@(foreach ($exeArg in $exeArgs) {
        foreach ($envArg in $envArgs) { "$exeArg --windows-service --env-file $envArg" }
    })
    if ($PgImagePath -cnotin $images) { throw 'PG SCM image does not bind committed binary and environment.' }
    $legacyArgs=@(('"{0}"' -f $LegacyBinary))
    if ($LegacyBinary -notmatch '[\s"]') { $legacyArgs += $LegacyBinary }
    $legacyMatches=@($legacyArgs | Where-Object {
        $LegacyImagePath -ieq $_ -or $LegacyImagePath.StartsWith(($_+' '),[StringComparison]::OrdinalIgnoreCase)
    })
    if ($legacyMatches.Count -eq 0) { throw 'Legacy SCM image does not bind committed binary.' }
}
function Set-Mode([string]$Name,[string]$Mode) {
    $native=@{Automatic='auto';Manual='demand';DelayedAutomatic='delayed-auto';Disabled='disabled'}[$Mode]
    if (-not $native) { throw 'Unsupported SCM start mode.' }
    & "$env:SystemRoot\System32\sc.exe" config $Name start= $native | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "SCM config failed: $Name" }
    if ((Get-ExactService $Name).mode -ne $Mode) { throw "SCM start-mode readback mismatch: $Name" }
}
function Stop-Disabled([string]$Name,[uint32]$OldPid) {
    # Disable first so ordinary SCM recovery cannot restart the old writer.
    Set-Mode $Name 'Disabled'
    $controller=Get-Service -Name $Name
    if ($controller.Status -ne 'Stopped') {
        # No -Force: dependent services must be handled by the existing operator.
        Stop-Service -Name $Name -ErrorAction Stop
        $controller.WaitForStatus('Stopped',[TimeSpan]::FromSeconds($TimeoutSeconds))
    }
    $state=Get-ExactService $Name
    if ($state.state -ne 'Stopped' -or $state.mode -ne 'Disabled' -or $state.pid -ne 0) {
        throw "Writer stop/disable not established: $Name"
    }
    if ($OldPid -gt 0 -and (Get-Process -Id $OldPid -ErrorAction SilentlyContinue)) {
        throw "Prior SCM process identity remains present: $Name"
    }
    return $state
}
function Assert-StoppedDisabled($State) {
    if ($State.state -ne 'Stopped' -or $State.mode -ne 'Disabled' -or $State.pid -ne 0) {
        throw "Destination is not stopped and disabled: $($State.name)"
    }
}
# Explicit Manual without inputs is only a staged start under fenced ingress.
# Automatic startup requires the existing actual PG consumer gate.
$qualificationInputs=@($PgEndpoint,$ExpectedNodeId,$TokenFile,$PreparedSourceRepo,
    $PreparedSourceRevision,$AcceptanceRoot,$ExpectedAcceptanceSha256)
$selectedQualification=@($qualificationInputs | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count -gt 0
$acceptance=Join-Path $PSScriptRoot '..\..\scripts\windows-native-runtime-r6c-acceptance.ps1'
function Assert-QualificationInputs {
    if ($Direction -ne 'Activate') { return }
    if (-not $selectedQualification) {
        if ($PgStartMode -ne 'Manual') { throw 'Automatic PG startup requires exact fresh-PG consumer qualification inputs.' }
        return
    }
    if (@($qualificationInputs | Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count -ne 0) {
        throw 'Fresh-PG consumer qualification inputs must be supplied together.'
    }
    if ($PgService -notmatch 'Candidate' -or $PgService -ieq 'OrdivonRuntime' -or
        $PgAccount -ine ("NT SERVICE\" + $PgService) -or
        $PgEndpoint -notmatch '^http://127\.0\.0\.1:[0-9]{1,5}/mcp$' -or
        $PgEndpoint -match ':8897/mcp$' -or $ExpectedNodeId -ieq 'windows-main') {
        throw 'Fresh-PG qualification must use the original candidate boundary and virtual service identity.'
    }
    $null=[Uri]$PgEndpoint
    Assert-Commitment (Resolve-Path -LiteralPath $acceptance).Path $ExpectedAcceptanceSha256
    if (-not [IO.Path]::IsPathRooted($TokenFile) -or -not [IO.File]::Exists($TokenFile) -or
        -not [IO.Path]::IsPathRooted($PreparedSourceRepo) -or -not [IO.Directory]::Exists($PreparedSourceRepo) -or
        -not [IO.Path]::IsPathRooted($AcceptanceRoot) -or $PreparedSourceRevision -notmatch '^[0-9a-f]{40}$') {
        throw 'Fresh-PG qualification fixture or token path is invalid.'
    }
    $root=[IO.Path]::GetFullPath($AcceptanceRoot).TrimEnd('\')
    $repo=[IO.Path]::GetFullPath($PreparedSourceRepo).TrimEnd('\')
    if (-not ($repo+'\').StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)) {
        throw 'Prepared fixture must remain under AcceptanceRoot.'
    }
    $owner=(Get-Acl -LiteralPath $repo).Owner
    $sid=[Security.Principal.NTAccount]::new($owner).Translate([Security.Principal.SecurityIdentifier]).Value
    $expected=[Security.Principal.NTAccount]::new($PgAccount).Translate([Security.Principal.SecurityIdentifier]).Value
    if ($sid -ne $expected) { throw 'Prepared fixture owner differs from the candidate service.' }
}
function Assert-ListenerOwner([uint32]$ExpectedPid,[bool]$Wait) {
    $port=([Uri]$PgEndpoint).Port
    $deadline=[DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        $listeners=@(Get-NetTCPConnection -State Listen -LocalAddress '127.0.0.1' -LocalPort $port -ErrorAction SilentlyContinue)
        $state=Get-ExactService $PgService
        if ($state.state -ne 'Running' -or $state.pid -ne $ExpectedPid) {
            throw 'Candidate SCM process changed during consumer qualification.'
        }
        if ($listeners.Count -eq 1 -and $listeners[0].OwningProcess -eq $ExpectedPid) { return }
        if (-not $Wait -or [DateTime]::UtcNow -ge $deadline) {
            throw 'Candidate SCM process does not own the exact MCP listener.'
        }
        Start-Sleep -Milliseconds 250
    } while ($true)
}
$mutex=[Threading.Mutex]::new($false,'Global\Ordivon.Runtime.WindowsPgCutover')
$held=$false
try {
    # Abandonment means the prior operation may have been interrupted. The
    # exact current SCM preimage, not this mutex, decides whether replay is safe.
    try { $held=$mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] {
        $held=$true
        throw 'Prior SCM transition was interrupted; reconcile exact service state before another operation.'
    }
    if (-not $held) { throw 'Another operator SCM transition holds the mutex.' }
    Assert-Commitments
    Assert-QualificationInputs
    $legacy=Get-ExactService $LegacyService
    $pg=Get-ExactService $PgService
    Assert-Identity $legacy $LegacyImagePath $LegacyAccount
    Assert-Identity $pg $PgImagePath $PgAccount
    if ($Direction -eq 'Activate') {
        $from=$legacy; $to=$pg; $targetMode=$PgStartMode
        if ($from.state -ne 'Running' -or $from.mode -ne $LegacyStartMode -or
            $ExpectedWriterPid -eq 0 -or $from.pid -ne $ExpectedWriterPid) {
            throw 'Legacy running preimage changed.'
        }
    } else {
        $from=$pg; $to=$legacy; $targetMode=$LegacyStartMode
        $running=($from.state -eq 'Running' -and $from.mode -in @($PgStartMode,'Manual') -and
            $ExpectedWriterPid -gt 0 -and $from.pid -eq $ExpectedWriterPid)
        $alreadyStopped=($from.state -eq 'Stopped' -and $from.mode -eq 'Disabled' -and
            $ExpectedWriterPid -eq 0 -and $from.pid -eq 0)
        if (-not ($running -or $alreadyStopped)) { throw 'PG restore preimage changed.' }
    }
    Assert-StoppedDisabled $to
    if (-not $Apply) {
        [ordered]@{schemaVersion=1;kind='ordivon.windows-pg-scm-cutover-preview';
            direction=$Direction;from=$from.name;to=$to.name;fromPid=$from.pid;
            sourceMode=$from.mode;destinationMode=$targetMode;effect=$false} | ConvertTo-Json
        return
    }
    $identity=[Security.Principal.WindowsIdentity]::GetCurrent()
    $principal=[Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'SCM transition requires the existing elevated operator.'
    }
    if (-not ($IngressQuiesced -and $OriginalConsumerQualified -and $OriginalWriterDrained)) {
        throw 'Operator must establish original consumer qualification, closed ingress, and writer drain before SCM transition.'
    }
    # The old writer must be stopped before the new service is enabled.
    $stopped=Stop-Disabled $from.name $ExpectedWriterPid
    Assert-Commitments
    $current=Get-ExactService $to.name
    Assert-StoppedDisabled $current
    Assert-Identity $current $to.image $to.account
    Assert-StoppedDisabled (Get-ExactService $from.name)
    $consumerReceipt=$null
    $initialMode=if ($Direction -eq 'Activate') {'Manual'} else {$targetMode}
    try {
        Set-Mode $to.name $initialMode
        Assert-StoppedDisabled (Get-ExactService $from.name)
        Start-Service -Name $to.name -ErrorAction Stop
        (Get-Service -Name $to.name).WaitForStatus('Running',[TimeSpan]::FromSeconds($TimeoutSeconds))
        $current=Get-ExactService $to.name
        Assert-Identity $current $to.image $to.account
        Assert-StoppedDisabled (Get-ExactService $from.name)
        if ($current.state -ne 'Running' -or $current.mode -ne $initialMode -or $current.pid -eq 0) {
            throw 'Destination start readback differs.'
        }
        if ($Direction -eq 'Activate' -and $selectedQualification) {
            $candidatePid=$current.pid
            Assert-ListenerOwner $candidatePid $true
            Assert-Commitments
            Assert-QualificationInputs
            $acceptanceArgs=@{
                Mode='WorkspaceCwdAdmission';RequireFreshPg=$true;ServiceName=$PgService
                Endpoint=$PgEndpoint;ExpectedNodeId=$ExpectedNodeId;TokenFile=$TokenFile
                PreparedSourceRepo=$PreparedSourceRepo;PreparedSourceRevision=$PreparedSourceRevision
                AcceptanceRoot=$AcceptanceRoot;ExpectedActiveUserSessionId=$ExpectedActiveUserSessionId
            }
            $consumerReceipt=(& $acceptance @acceptanceArgs) | ConvertFrom-Json
            if ($consumerReceipt.passed -ne $true -or $consumerReceipt.freshPgProjectionQualified -ne $true -or
                $consumerReceipt.exactReplayVerified -ne $true -or
                $consumerReceipt.activeUserSessionId -ne $ExpectedActiveUserSessionId) {
                throw 'Original fresh-PG Session1 consumer qualification failed.'
            }
            Assert-Commitments
            Assert-QualificationInputs
            Assert-StoppedDisabled (Get-ExactService $from.name)
            Assert-ListenerOwner $candidatePid $false
            Set-Mode $to.name $targetMode
            $current=Get-ExactService $to.name
            Assert-Identity $current $to.image $to.account
            Assert-ListenerOwner $candidatePid $false
            Assert-StoppedDisabled (Get-ExactService $from.name)
        }
    } catch {
        # A start error may have admitted effects; never restart the old
        # writer automatically. Attempt to leave BOTH services disabled and
        # require independent reconciliation before RestoreLegacy.
        try {
            $failed=Get-ExactService $to.name
            $null=Stop-Disabled $to.name $failed.pid
        } catch {
            throw 'Destination start and stop outcome unresolved. Source remains disabled; operator reconciliation required.'
        }
        throw 'Destination activation failed; both service starts fenced. Reconcile durable effects before explicit restore.'
    }
    [ordered]@{schemaVersion=1;kind='ordivon.windows-pg-scm-transition';
        direction=$Direction;from=$stopped.name;fromState=$stopped.state;fromMode=$stopped.mode;
        to=$current.name;toState=$current.state;toMode=$current.mode;toPid=$current.pid;
        scmTransitionObserved=$true;consumerQualificationEvaluated=($null -ne $consumerReceipt);
        freshPgSessionQualified=($null -ne $consumerReceipt);consumerReceipt=$consumerReceipt;
        pgWriterUniquenessEvaluated=$false;ingressReopened=$false;fullCutoverAccepted=$false} | ConvertTo-Json -Depth 12
} finally {
    if ($held) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
