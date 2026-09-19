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
$runtimeTarget = Join-Path $binRoot 'ordivon-runtime.exe'
$launcherTarget = Join-Path $binRoot 'ordivon-windows-job-launcher.exe'
$configTarget = Join-Path $configRoot 'ordivon-runtime.env'
$tokenTarget = Join-Path $secretRoot 'runtime-mcp.token'
$serviceAccount = "NT SERVICE\$ServiceName"
$requiresLocalAdministrators = $WindowsAuthorityProfile -eq 'limited-and-elevated'
$imagePath = ('"{0}" --windows-service --env-file "{1}"' -f $runtimeTarget, $configTarget)

$plan = [ordered]@{
    schemaVersion = 1
    applyRequested = [bool]$Apply
    programDataRoot = $ProgramDataRoot
    bind = $Bind
    nodeId = $NodeId
    service = [ordered]@{
        name = $ServiceName
        displayName = $DisplayName
        type = 'own'
        start = 'auto'
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

foreach ($directory in @(
    $ProgramDataRoot, $binRoot, $configRoot, $secretRoot, $storeRoot, $registryRoot, $serviceHome
)) {
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
Copy-UnlessSameFile $tokenSourceResolved $tokenTarget

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
[IO.File]::WriteAllText(
    $configTarget,
    $materialized,
    [Text.UTF8Encoding]::new($false))

$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($null -eq $service) {
    Invoke-ScChecked @(
        'create', $ServiceName,
        'type=', 'own',
        'start=', 'auto',
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
        'start=', 'auto',
        'error=', 'normal',
        'binPath=', $imagePath,
        'obj=', $serviceAccount,
        'DisplayName=', $DisplayName
    )
}

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
foreach ($directory in @($storeRoot, $registryRoot, $serviceHome)) {
    Set-ExactPrivateAcl $directory $serviceSid $fullControl
}
foreach ($file in @($runtimeTarget, $launcherTarget)) {
    Set-ExactPrivateAcl $file $serviceSid $readExecute
}
foreach ($file in @($configTarget, $tokenTarget)) {
    Set-ExactPrivateAcl $file $serviceSid $readOnly
}

$plan.service.builtinAdministratorsMembershipObserved = $administratorMembership

# Re-query through native SCM tooling. These are evidence surfaces; this script never starts the service.
Invoke-ScChecked @('qc', $ServiceName)
Invoke-ScChecked @('qsidtype', $ServiceName)
Invoke-ScChecked @('qfailure', $ServiceName)
Invoke-ScChecked @('qfailureflag', $ServiceName)

$plan | ConvertTo-Json -Depth 10
