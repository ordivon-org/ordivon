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
function Assert-Commitments {
    Assert-Commitment $LegacyBinary $ExpectedLegacySha256
    Assert-Commitment $PgBinary $ExpectedPgSha256
    Assert-Commitment $PgLauncher $ExpectedLauncherSha256
    Assert-Commitment $PgEnvironment $ExpectedEnvironmentSha256
    # Bind the operator's file commitments to the exact installed image paths.
    $expectedPg='"{0}" --windows-service --env-file "{1}"' -f $PgBinary,$PgEnvironment
    if ($PgImagePath -cne $expectedPg) { throw 'PG SCM image does not bind committed binary and environment.' }
    if (-not ($LegacyImagePath.StartsWith(('"{0}"' -f $LegacyBinary),[StringComparison]::OrdinalIgnoreCase))) {
        throw 'Legacy SCM image does not bind committed binary.'
    }
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
        $running=($from.state -eq 'Running' -and $from.mode -eq $PgStartMode -and
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
    try {
        Set-Mode $to.name $targetMode
        Assert-StoppedDisabled (Get-ExactService $from.name)
        Start-Service -Name $to.name -ErrorAction Stop
        (Get-Service -Name $to.name).WaitForStatus('Running',[TimeSpan]::FromSeconds($TimeoutSeconds))
        $current=Get-ExactService $to.name
        Assert-Identity $current $to.image $to.account
        Assert-StoppedDisabled (Get-ExactService $from.name)
        if ($current.state -ne 'Running' -or $current.mode -ne $targetMode -or $current.pid -eq 0) {
            throw 'Destination start readback differs.'
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
        scmTransitionObserved=$true;consumerQualificationEvaluated=$false;
        pgWriterUniquenessEvaluated=$false;ingressReopened=$false} | ConvertTo-Json
} finally {
    if ($held) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
