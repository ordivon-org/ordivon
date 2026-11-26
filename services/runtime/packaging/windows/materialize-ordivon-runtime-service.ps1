#requires -version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RuntimeBinary,
    [Parameter(Mandatory = $true)]
    [string]$WindowsJobLauncher,
    [Parameter(Mandatory = $true)]
    [string]$TokenSource,
    [string]$ServiceName = 'OrdivonRuntime',
    [string]$DisplayName = 'Ordivon Runtime',
    [string]$ProgramDataRoot = '',
    [string]$Bind = '127.0.0.1:8897',
    [string]$NodeId = 'windows-main',
    [ValidateSet('limited-only', 'limited-and-elevated')]
    [string]$WindowsAuthorityProfile = 'limited-only',
    [string]$ElevatedPrincipalsJson = '',
    [string]$ElevatedProfilesJson = '',
    [string]$MaintenanceLeasePath = '',
    # PG candidate uses an operator-provisioned private env file at its final
    # path. This script never generates a DSN or migrates the old Registry.
    [string]$PostgresEnvironmentFile = '',
    [string]$ExpectedRuntimeSha256 = '',
    [string]$ExpectedLauncherSha256 = '',
    [string]$ExpectedPostgresEnvironmentSha256 = '',
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ($ServiceName -notmatch '^[A-Za-z0-9_.-]+$') {
    throw 'ServiceName contains unsupported characters.'
}
if ($Bind -notmatch '^(127\.0\.0\.1|\[::1\]):[0-9]{1,5}$') {
    throw 'Bind must be an explicit loopback address and port.'
}
$bindPort = [int]($Bind -replace '^.*:', '')
if ($bindPort -lt 1 -or $bindPort -gt 65535) {
    throw 'Bind port must be in the range 1..65535.'
}
if ($NodeId -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$') {
    throw 'NodeId contains unsupported characters.'
}
if ([string]::IsNullOrWhiteSpace($ProgramDataRoot)) {
    $commonData = [Environment]::GetFolderPath(
        [Environment+SpecialFolder]::CommonApplicationData)
    $ProgramDataRoot = Join-Path $commonData 'Ordivon\Runtime'
}
if (-not [IO.Path]::IsPathRooted($ProgramDataRoot)) {
    throw 'ProgramDataRoot must be absolute.'
}

$privilegedPolicyValues = @(
    $ElevatedPrincipalsJson,
    $ElevatedProfilesJson,
    $MaintenanceLeasePath
)
$privilegedPolicyConfiguredCount = @(
    $privilegedPolicyValues | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
).Count
if ($privilegedPolicyConfiguredCount -ne 0 -and $privilegedPolicyConfiguredCount -ne 3) {
    throw 'Privileged admission policy must configure principals, profiles, and maintenance lease together.'
}
$privilegedPolicyConfigured = $privilegedPolicyConfiguredCount -eq 3
$elevatedPrincipalCount = 0
$elevatedProfileCount = 0
if ($privilegedPolicyConfigured) {
    foreach ($jsonValue in @($ElevatedPrincipalsJson, $ElevatedProfilesJson)) {
        if ($jsonValue.Contains("`r") -or $jsonValue.Contains("`n")) {
            throw 'Privileged admission JSON must be single-line.'
        }
    }
    if ($MaintenanceLeasePath.Contains("`r") -or $MaintenanceLeasePath.Contains("`n")) {
        throw 'MaintenanceLeasePath must be single-line.'
    }
    if (-not [IO.Path]::IsPathRooted($MaintenanceLeasePath)) {
        throw 'MaintenanceLeasePath must be absolute.'
    }
    try {
        $elevatedPrincipals = @($ElevatedPrincipalsJson | ConvertFrom-Json -ErrorAction Stop)
        $elevatedProfiles = @($ElevatedProfilesJson | ConvertFrom-Json -ErrorAction Stop)
    } catch {
        throw ('Privileged admission JSON is invalid: ' + $_.Exception.Message)
    }
    if ($elevatedPrincipals.Count -eq 0 -or $elevatedProfiles.Count -eq 0) {
        throw 'Privileged admission principal and profile arrays must be non-empty when configured.'
    }
    foreach ($principalId in $elevatedPrincipals) {
        if ($principalId -isnot [string] -or [string]::IsNullOrWhiteSpace($principalId)) {
            throw 'Privileged admission principal ids must be non-empty strings.'
        }
    }
    $elevatedPrincipalCount = $elevatedPrincipals.Count
    $elevatedProfileCount = $elevatedProfiles.Count
}

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Applying the Runtime Windows service requires an elevated Administrator shell.'
    }
}

function Resolve-ExistingFile([string]$Path, [string]$Label) {
    $resolved = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
    if (-not [IO.Path]::IsPathRooted($resolved) -or -not [IO.File]::Exists($resolved)) {
        throw "$Label must be an existing absolute file: $Path"
    }
    return $resolved
}

function Invoke-ScChecked([string[]]$Arguments) {
    & "$env:SystemRoot\System32\sc.exe" @Arguments | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "sc.exe failed ($LASTEXITCODE): $($Arguments -join ' ')"
    }
}

function Get-BuiltinAdministratorsGroup {
    $administratorsSid = [Security.Principal.SecurityIdentifier]::new('S-1-5-32-544')
    $group = Get-LocalGroup -SID $administratorsSid -ErrorAction Stop
    if ($null -eq $group) {
        throw 'Builtin Administrators local group could not be resolved by SID.'
    }
    return $group
}

function Test-LocalAdministratorsMembership([string]$Account) {
    $group = Get-BuiltinAdministratorsGroup
    return @(
        Get-LocalGroupMember -Group $group.Name -ErrorAction Stop |
            Where-Object { $_.Name -ieq $Account }
    ).Count -gt 0
}

function Set-LocalAdministratorsMembership([string]$Account, [bool]$Required) {
    $group = Get-BuiltinAdministratorsGroup
    $present = Test-LocalAdministratorsMembership $Account
    if ($Required -and -not $present) {
        Add-LocalGroupMember -Group $group.Name -Member $Account -ErrorAction Stop
    } elseif (-not $Required -and $present) {
        Remove-LocalGroupMember -Group $group.Name -Member $Account -ErrorAction Stop
    }
    $observed = Test-LocalAdministratorsMembership $Account
    if ($observed -ne $Required) {
        throw "Builtin Administrators membership did not converge for $Account."
    }
    return $observed
}

function New-PrivateFileSecurity(
    [Security.Principal.SecurityIdentifier]$ServiceSid,
    [Security.AccessControl.FileSystemRights]$ServiceRights
) {
    $system = [Security.Principal.SecurityIdentifier]::new('S-1-5-18')
    $administrators = [Security.Principal.SecurityIdentifier]::new('S-1-5-32-544')
    $security = [Security.AccessControl.FileSecurity]::new()
    $security.SetAccessRuleProtection($true, $false)
    $security.SetOwner($administrators)
    foreach ($sid in @($system, $administrators)) {
        $security.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new(
            $sid,
            [Security.AccessControl.FileSystemRights]::FullControl,
            [Security.AccessControl.AccessControlType]::Allow))
    }
    $security.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new(
        $ServiceSid,
        $ServiceRights,
        [Security.AccessControl.AccessControlType]::Allow))
    return $security
}

function New-PrivateDirectorySecurity(
    [Security.Principal.SecurityIdentifier]$ServiceSid,
    [Security.AccessControl.FileSystemRights]$ServiceRights
) {
    $system = [Security.Principal.SecurityIdentifier]::new('S-1-5-18')
    $administrators = [Security.Principal.SecurityIdentifier]::new('S-1-5-32-544')
    $security = [Security.AccessControl.DirectorySecurity]::new()
    $security.SetAccessRuleProtection($true, $false)
    $security.SetOwner($administrators)
    foreach ($sid in @($system, $administrators)) {
        $security.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new(
            $sid,
            [Security.AccessControl.FileSystemRights]::FullControl,
            [Security.AccessControl.InheritanceFlags]::ContainerInherit -bor
                [Security.AccessControl.InheritanceFlags]::ObjectInherit,
            [Security.AccessControl.PropagationFlags]::None,
            [Security.AccessControl.AccessControlType]::Allow))
    }
    $security.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new(
        $ServiceSid,
        $ServiceRights,
        [Security.AccessControl.InheritanceFlags]::ContainerInherit -bor
            [Security.AccessControl.InheritanceFlags]::ObjectInherit,
        [Security.AccessControl.PropagationFlags]::None,
        [Security.AccessControl.AccessControlType]::Allow))
    return $security
}

function Set-ExactPrivateAcl(
    [string]$Path,
    [Security.Principal.SecurityIdentifier]$ServiceSid,
    [Security.AccessControl.FileSystemRights]$ServiceRights
) {
    if ([IO.Directory]::Exists($Path)) {
        [IO.Directory]::SetAccessControl(
            $Path,
            (New-PrivateDirectorySecurity $ServiceSid $ServiceRights))
    } elseif ([IO.File]::Exists($Path)) {
        [IO.File]::SetAccessControl(
            $Path,
            (New-PrivateFileSecurity $ServiceSid $ServiceRights))
    } else {
        throw "ACL target does not exist: $Path"
    }
}

$runtimeSource = Resolve-ExistingFile $RuntimeBinary 'RuntimeBinary'
$launcherSource = Resolve-ExistingFile $WindowsJobLauncher 'WindowsJobLauncher'
$tokenSourceResolved = Resolve-ExistingFile $TokenSource 'TokenSource'

$binRoot = Join-Path $ProgramDataRoot 'bin'
$configRoot = Join-Path $ProgramDataRoot 'config'
$secretRoot = Join-Path $ProgramDataRoot 'secrets'
$storeRoot = Join-Path $ProgramDataRoot 'store'
$registryRoot = Join-Path $ProgramDataRoot 'registry'
$serviceHome = Join-Path $ProgramDataRoot 'service-home'
$postgres = -not [string]::IsNullOrWhiteSpace($PostgresEnvironmentFile)
$runtimeTarget = Join-Path $binRoot 'ordivon-runtime.exe'
if ($postgres) {
    $runtimeTarget = Join-Path $binRoot 'ordivon-runtime-pg.exe'
    $storeRoot = Join-Path $ProgramDataRoot 'pg-store'
}
$launcherTarget = Join-Path $binRoot 'ordivon-windows-job-launcher.exe'
$configTarget = Join-Path $configRoot 'ordivon-runtime.env'
$tokenTarget = Join-Path $secretRoot 'runtime-mcp.token'
if ($postgres) {
    # Never overwrite the legacy install's launcher, environment or token.
    # The PG launcher has a separate exact target, and the private config and
    # token are already provisioned in their final operator-owned locations.
    $launcherTarget = Join-Path $binRoot 'ordivon-windows-pg-job-launcher.exe'
    $configTarget = Join-Path $configRoot 'ordivon-runtime-pg.env'
    $tokenTarget = Join-Path $secretRoot 'runtime-pg-mcp.token'
    if (-not [string]::Equals([IO.Path]::GetFullPath($tokenSourceResolved),
            [IO.Path]::GetFullPath($tokenTarget), [StringComparison]::OrdinalIgnoreCase)) {
        throw 'PG TokenSource must be pre-provisioned at the final private PG token path.'
    }
    $pgConfig = Resolve-ExistingFile $PostgresEnvironmentFile 'PostgresEnvironmentFile'
    if (-not [string]::Equals([IO.Path]::GetFullPath($pgConfig), [IO.Path]::GetFullPath($configTarget),
            [StringComparison]::OrdinalIgnoreCase)) {
        throw 'PostgresEnvironmentFile must be pre-provisioned at the final private PG config path.'
    }
    if ($privilegedPolicyConfigured) {
        throw 'PG privileged admission policy must be bound inside the pre-provisioned PG environment.'
    }
    $commitments = @(
        @{ path = $runtimeSource; digest = $ExpectedRuntimeSha256; label = 'Runtime binary' },
        @{ path = $launcherSource; digest = $ExpectedLauncherSha256; label = 'Windows launcher' },
        @{ path = $pgConfig; digest = $ExpectedPostgresEnvironmentSha256; label = 'PG environment' }
    )
    function Assert-PgCandidateCommitments {
        foreach ($item in $commitments) {
            if ($item.digest -notmatch '^[0-9a-fA-F]{64}$') {
                throw ('Missing or invalid SHA-256 commitment for ' + $item.label)
            }
            if ((Get-FileHash -LiteralPath $item.path -Algorithm SHA256).Hash -ne $item.digest) {
                throw ('SHA-256 commitment mismatch for ' + $item.label)
            }
        }
    }
    Assert-PgCandidateCommitments
    $pgItem = Get-Item -LiteralPath $pgConfig
    if ($pgItem.Length -gt 65536 -or
        ($pgItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'PG environment must be a regular file of at most 64 KiB.'
    }
    # The Rust native env loader remains the authoritative parser. Here check
    # only the SCM/file identity and required PG profile, without echoing secrets.
    $pgValues = @{}
    foreach ($rawLine in [IO.File]::ReadAllLines($pgConfig)) {
        $line = $rawLine.Trim()
        if ($line.Length -eq 0 -or $line.StartsWith('#')) { continue }
        # Windows PowerShell 5.1 selects a different String.Split overload.
        # IndexOf/Substring matches the native loader's first '=' semantics.
        $separator = $line.IndexOf('=')
        if ($separator -lt 1) { throw 'Invalid PG environment line.' }
        $key = $line.Substring(0, $separator).Trim()
        if ($key -cnotmatch '^(ORDIVON_[A-Z0-9_]+|RUST_LOG)$' -or $pgValues.ContainsKey($key)) {
            throw 'Unsupported or duplicate PG environment key.'
        }
        $pgValues[$key] = $line.Substring($separator + 1).Trim()
    }
    foreach ($key in @('ORDIVON_PG_DSN','ORDIVON_PG_SCHEMA','ORDIVON_PG_SOURCE_SHA256',
            'ORDIVON_PG_PRINCIPAL','ORDIVON_PG_EXECUTABLE_ROOTS_JSON')) {
        if (-not $pgValues.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($pgValues[$key])) {
            throw ('Required PG environment key missing: ' + $key)
        }
    }
    foreach ($key in @('ORDIVON_REGISTRY_ROOT','ORDIVON_BIND','ORDIVON_BEARER_TOKEN',
            'ORDIVON_PG_TOKEN','ORDIVON_REMOTE_BEARER_TOKEN')) {
        if ($pgValues.ContainsKey($key)) { throw ('Legacy or inline secret key forbidden: ' + $key) }
    }
    if ($pgValues['ORDIVON_PG_SOURCE_SHA256'] -cnotmatch '^[0-9a-f]{64}$') {
        throw 'PG source identity must be lowercase SHA-256.'
    }
    $expectedBindings = @{
        ORDIVON_PG_BIND = $Bind
        ORDIVON_NODE_ID = $NodeId
        ORDIVON_PG_STORE_ROOT = $storeRoot
        ORDIVON_PG_RUNNER = $launcherTarget
        ORDIVON_BEARER_TOKEN_FILE = $tokenTarget
    }
    foreach ($key in $expectedBindings.Keys) {
        if (-not $pgValues.ContainsKey($key) -or $pgValues[$key] -cne $expectedBindings[$key]) {
            throw ('PG environment does not bind the planned service: ' + $key)
        }
    }
} elseif ($ExpectedRuntimeSha256 -or $ExpectedLauncherSha256 -or $ExpectedPostgresEnvironmentSha256) {
    throw 'PG candidate commitments require PostgresEnvironmentFile.'
}
# PG materialization must remain disabled through all SCM and ACL changes.
# Only the separately qualified cold activation may enable the service.
$startMode = $(if ($postgres) { 'disabled' } else { 'auto' })
$serviceAccount = "NT SERVICE\$ServiceName"
$requiresLocalAdministrators = $WindowsAuthorityProfile -eq 'limited-and-elevated'
$imagePath = ('"{0}" --windows-service --env-file "{1}"' -f $runtimeTarget, $configTarget)

$plan = [ordered]@{
    schemaVersion = 1
    applyRequested = [bool]$Apply
    programDataRoot = $ProgramDataRoot
    bind = $Bind
    nodeId = $NodeId
    registryBackend = $(if ($postgres) { 'postgresql' } else { 'sqlite' })
    executionReady = $false
    privilegedAdmission = [ordered]@{
        configured = $privilegedPolicyConfigured
        principalCount = $elevatedPrincipalCount
        profileCount = $elevatedProfileCount
        maintenanceLeasePath = $(if ($privilegedPolicyConfigured) { $MaintenanceLeasePath } else { $null })
    }
    service = [ordered]@{
        name = $ServiceName
        displayName = $DisplayName
        type = 'own'
        start = $startMode
        account = $serviceAccount
        windowsAuthorityProfile = $WindowsAuthorityProfile
        builtinAdministratorsMembershipRequired = $requiresLocalAdministrators
        imagePath = $imagePath
        sidType = 'unrestricted'
        failureResetSeconds = 86400
        failureActions = @('restart/5000', 'restart/15000', 'restart/60000')
        failureActionsOnNonCrashFailure = $true
        requiredPrivileges = 'deferred-to-native-acceptance'
    }
    acl = [ordered]@{
        state = 'service:FullControl; SYSTEM:FullControl; Administrators:FullControl'
        executable = 'service:ReadAndExecute; SYSTEM:FullControl; Administrators:FullControl'
        configSecret = 'service:Read; SYSTEM:FullControl; Administrators:FullControl'
    }
    files = [ordered]@{
        runtimeSource = $runtimeSource
        launcherSource = $launcherSource
        tokenSource = $tokenSourceResolved
        runtimeTarget = $runtimeTarget
        launcherTarget = $launcherTarget
        configTarget = $configTarget
        tokenTarget = $tokenTarget
    }
    invariants = @(
        'No bearer secret appears in SCM ImagePath or the env file.',
        'ProgramData state/config/token are ACL-bound to SYSTEM, Builtin Administrators and the service SID.',
        'The service is not started by this materializer; start/cold-restart acceptance is a separate gate.',
        'PG uses a separate store, a pre-provisioned exact private env file, and disabled startup until the qualified cold cutover.',
        'Required service privileges are not broadened before native acceptance proves the minimum set.',
        'limited-and-elevated uses the dedicated virtual service account as a Builtin Administrators member; launcher acceptance must prove both High/Admin-enabled elevated context and LUA-filtered Medium/Admin-disabled limited context.',
        'The dedicated virtual service identity is preserved so limited-token semantics do not inherit a shared machine identity.'
    )
}

if (-not $Apply) {
    $plan | ConvertTo-Json -Depth 10
    return
}

Assert-Administrator

function Assert-PgServiceStagingFence([string]$Name, [bool]$MustExist) {
    # Native SCM StartType and Status, not a textual sc.exe projection.
    $observed = Get-Service -Name $Name -ErrorAction SilentlyContinue
    if ($null -eq $observed) {
        if ($MustExist) { throw "PG staging service $Name disappeared." }
        return
    }
    if ($observed.Status -ne [ServiceProcess.ServiceControllerStatus]::Stopped -or
        $observed.StartType -ne [ServiceProcess.ServiceStartMode]::Disabled) {
        throw "PG staging service $Name must be stopped and disabled before materialization."
    }
}

if ($postgres) { Assert-PgServiceStagingFence $ServiceName $false }

# A running old Writer must be rejected before touching its binary, launcher,
# credentials or config. Recheck at the SCM change boundary as well.
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($null -ne $service -and $service.Status -ne [ServiceProcess.ServiceControllerStatus]::Stopped) {
    throw "Service $ServiceName already exists and must be stopped before materialization."
}

if ($postgres) {
    Assert-PgCandidateCommitments
}
$stateDirectories = @($storeRoot, $serviceHome)
if (-not $postgres) { $stateDirectories += $registryRoot }
foreach ($directory in (@($ProgramDataRoot, $binRoot, $configRoot, $secretRoot) + $stateDirectories)) {
    [IO.Directory]::CreateDirectory($directory) | Out-Null
}
function Copy-UnlessSameFile([string]$Source, [string]$Destination) {
    $sourceFull = [IO.Path]::GetFullPath($Source)
    $destinationFull = [IO.Path]::GetFullPath($Destination)
    if ([string]::Equals(
        $sourceFull,
        $destinationFull,
        [StringComparison]::OrdinalIgnoreCase)) {
        return
    }
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

Copy-UnlessSameFile $runtimeSource $runtimeTarget
Copy-UnlessSameFile $launcherSource $launcherTarget
if (-not $postgres) {
    Copy-UnlessSameFile $tokenSourceResolved $tokenTarget
}

if (-not $postgres) {
    $templatePath = Join-Path $PSScriptRoot 'ordivon-runtime.env.example'
    $template = [IO.File]::ReadAllText($templatePath)
    $templateRoot = 'C:\ProgramData\Ordivon\Runtime'
    $materialized = $template.Replace($templateRoot, $ProgramDataRoot)
    $materialized = $materialized.Replace(
        'ORDIVON_BIND=127.0.0.1:8897',
        ('ORDIVON_BIND=' + $Bind))
    $materialized = $materialized.Replace(
        'ORDIVON_NODE_ID=windows-main',
        ('ORDIVON_NODE_ID=' + $NodeId))
    if ($privilegedPolicyConfigured) {
        if (-not $materialized.EndsWith("`n")) {
            $materialized += "`r`n"
        }
        $materialized += (
            'ORDIVON_WINDOWS_ELEVATED_PRINCIPALS_JSON=' + $ElevatedPrincipalsJson + "`r`n" +
            'ORDIVON_WINDOWS_ELEVATED_PROFILES_JSON=' + $ElevatedProfilesJson + "`r`n" +
            'ORDIVON_WINDOWS_MAINTENANCE_LEASE_PATH=' + $MaintenanceLeasePath + "`r`n"
        )
    }
    [IO.File]::WriteAllText(
        $configTarget,
        $materialized,
        [Text.UTF8Encoding]::new($false))
} else {
    # The operator file is already at its final location. No secret copy or rewrite.
    Assert-PgCandidateCommitments
    if ((Get-FileHash -LiteralPath $runtimeTarget -Algorithm SHA256).Hash -ne $ExpectedRuntimeSha256 -or
        (Get-FileHash -LiteralPath $launcherTarget -Algorithm SHA256).Hash -ne $ExpectedLauncherSha256) {
        throw 'Staged PG binary or launcher digest mismatch.'
    }
}

$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($postgres) { Assert-PgServiceStagingFence $ServiceName ($null -ne $service) }
if ($null -eq $service) {
    Invoke-ScChecked @(
        'create', $ServiceName,
        'type=', 'own',
        'start=', $startMode,
        'error=', 'normal',
        'binPath=', $imagePath,
        'obj=', $serviceAccount,
        'DisplayName=', $DisplayName
    )
} else {
    if ($service.Status -ne [ServiceProcess.ServiceControllerStatus]::Stopped) {
        throw "Service $ServiceName already exists and must be stopped before materialization."
    }
    Invoke-ScChecked @(
        'config', $ServiceName,
        'type=', 'own',
        'start=', $startMode,
        'error=', 'normal',
        'binPath=', $imagePath,
        'obj=', $serviceAccount,
        'DisplayName=', $DisplayName
    )
}

if ($postgres) { Assert-PgServiceStagingFence $ServiceName $true }

Invoke-ScChecked @('description', $ServiceName, 'Native Ordivon Runtime control plane')
Invoke-ScChecked @('sidtype', $ServiceName, 'unrestricted')
Invoke-ScChecked @(
    'failure', $ServiceName,
    'reset=', '86400',
    'actions=', 'restart/5000/restart/15000/restart/60000'
)
Invoke-ScChecked @('failureflag', $ServiceName, '1')

# Membership changes use Windows local-group authority, not a custom elevation broker.
# They take effect in the service token on the next SCM start; acceptance must prove
# the effective token before Runtime may advertise elevated Windows authority.
$administratorMembership = Set-LocalAdministratorsMembership $serviceAccount $requiresLocalAdministrators

$serviceSid = [Security.Principal.NTAccount]::new($serviceAccount).Translate(
    [Security.Principal.SecurityIdentifier])

$readExecute = [Security.AccessControl.FileSystemRights]::ReadAndExecute
$readOnly = [Security.AccessControl.FileSystemRights]::Read
$fullControl = [Security.AccessControl.FileSystemRights]::FullControl

foreach ($directory in @($ProgramDataRoot, $binRoot, $configRoot, $secretRoot)) {
    Set-ExactPrivateAcl $directory $serviceSid $readExecute
}
foreach ($directory in $stateDirectories) {
    Set-ExactPrivateAcl $directory $serviceSid $fullControl
}
foreach ($file in @($runtimeTarget, $launcherTarget)) {
    Set-ExactPrivateAcl $file $serviceSid $readExecute
}
foreach ($file in @($configTarget, $tokenTarget)) {
    Set-ExactPrivateAcl $file $serviceSid $readOnly
}

$plan.service.builtinAdministratorsMembershipObserved = $administratorMembership
if ($postgres) { Assert-PgServiceStagingFence $ServiceName $true }

# Re-query through native SCM tooling. These are evidence surfaces; this script never starts the service.
Invoke-ScChecked @('qc', $ServiceName)
Invoke-ScChecked @('qsidtype', $ServiceName)
Invoke-ScChecked @('qfailure', $ServiceName)
Invoke-ScChecked @('qfailureflag', $ServiceName)

$plan | ConvertTo-Json -Depth 10
