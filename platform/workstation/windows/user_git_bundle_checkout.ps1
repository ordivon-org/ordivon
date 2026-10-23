# Native Windows active_user Git bundle consumer. The Runtime service produces
# a source-pinned bundle separately. Git owns clone/revision/object semantics;
# this script only applies the consumer's exact fail-closed handoff contract.
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$BundlePath,
    [Parameter(Mandatory)][string]$TargetPath,
    [Parameter(Mandatory)][string]$ExpectedRevision
)

$ErrorActionPreference = 'Stop'
function Fail-Checkout([string]$Code, [string]$Detail) {
    [Console]::Error.WriteLine((([ordered]@{
        schemaVersion = 1
        kind = 'ordivon.workstation.windows-user-git-bundle'
        standing = 'FAILED'
        reasonCode = $Code
        detail = $Detail
    }) | ConvertTo-Json -Compress))
    exit 69
}

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    Fail-Checkout 'WINDOWS_ONLY' 'Native Windows active-user consumption is required'
}
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($identity.Name.StartsWith('NT SERVICE\', [StringComparison]::OrdinalIgnoreCase) -or
    $identity.User.Value -in @('S-1-5-18', 'S-1-5-19', 'S-1-5-20')) {
    Fail-Checkout 'SERVICE_IDENTITY_NOT_AGENT' 'Clone must be owned by the login user'
}
if ($ExpectedRevision -cnotmatch '^[0-9a-fA-F]{40}$') {
    Fail-Checkout 'INVALID_EXPECTED_REVISION' 'ExpectedRevision must be a full Git SHA'
}
$git = Get-Command git -CommandType Application -ErrorAction SilentlyContinue
if (-not $git) {
    Fail-Checkout 'GIT_UNAVAILABLE' 'Native Git is not on the login user PATH'
}
try {
    $source = (Resolve-Path -LiteralPath $BundlePath -ErrorAction Stop).ProviderPath
    $target = [IO.Path]::GetFullPath($TargetPath)
    $parent = [IO.Path]::GetDirectoryName($target)
} catch {
    Fail-Checkout 'INVALID_PATH' 'Bundle or target path is not an accessible native file path'
}
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    Fail-Checkout 'INVALID_BUNDLE' 'Bundle is not an accessible regular file'
}
if (Test-Path -LiteralPath $target) {
    Fail-Checkout 'TARGET_ALREADY_EXISTS' 'Never overwrite an existing working directory'
}
if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
    Fail-Checkout 'TARGET_PARENT_MISSING' 'Parent directory must already exist'
}
$parentInfo = Get-Item -LiteralPath $parent -Force
if (($parentInfo.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    Fail-Checkout 'TARGET_PARENT_REPARSE_POINT' 'Consumer directory cannot be a reparse point'
}
$owner = (Get-Acl -LiteralPath $parent).GetOwner([Security.Principal.SecurityIdentifier])
if ($owner.Value -ne $identity.User.Value) {
    Fail-Checkout 'TARGET_PARENT_NOT_USER_OWNED' 'Target parent must belong to current login user'
}

# The signed release/Runtime caller freezes the exact SourceCut. A bundle
# must actually advertise that SHA BEFORE any worktree directory is created.
$heads = @(& $git.Source bundle list-heads $source 2>$null)
if ($LASTEXITCODE -ne 0) {
    Fail-Checkout 'INVALID_BUNDLE' 'Native Git could not list bundle heads'
}
$revision = $ExpectedRevision.ToLowerInvariant()
$matching = @($heads | Where-Object { $_ -match ('(?i)^' + [regex]::Escape($revision) + '\s+') })
if ($matching.Count -lt 1) {
    Fail-Checkout 'SOURCE_REVISION_MISMATCH' 'Bundle does not advertise the exact SourceCut'
}

# Clone and validate in a fresh sibling directory. Only a fully qualified
# checkout is published to the requested user-visible target; a bad pack,
# failed checkout, unexpected remote or promotion race must not poison retry.
# A sibling rename stays on the same filesystem and uses native .NET semantics.
$staging = Join-Path $parent ('.ordivon-checkout-' + [IO.Path]::GetRandomFileName())
if (Test-Path -LiteralPath $staging) {
    Fail-Checkout 'STAGING_COLLISION' 'Fresh checkout staging directory already exists'
}
try {
    # Never share service-owned objects or point the user's Git to ProgramData.
    & $git.Source clone --no-local --no-hardlinks --no-checkout $source $staging 2>$null
    if ($LASTEXITCODE -ne 0) {
        Fail-Checkout 'GIT_CLONE_FAILED' 'Native Git independent bundle clone failed'
    }
    $gitdir = Join-Path $staging '.git'
    if (-not (Test-Path -LiteralPath $gitdir -PathType Container)) {
        Fail-Checkout 'GIT_CLONE_INVALID' 'Expected user-owned independent Git directory'
    }
    if (Test-Path -LiteralPath (Join-Path $gitdir 'objects\info\alternates')) {
        Fail-Checkout 'SHARED_GIT_OBJECTS' 'Bundle clone must not reference the service Git object store'
    }
    & $git.Source -C $staging checkout --detach $revision 2>$null
    if ($LASTEXITCODE -ne 0) {
        Fail-Checkout 'SOURCE_REVISION_MISMATCH' 'Native Git cannot check out the exact SourceCut'
    }
    $observed = @(& $git.Source -C $staging rev-parse HEAD 2>$null)
    if ($LASTEXITCODE -ne 0 -or $observed.Count -ne 1 -or
        -not [string]::Equals($observed[0], $revision, [StringComparison]::OrdinalIgnoreCase)) {
        Fail-Checkout 'SOURCE_REVISION_MISMATCH' 'Checked-out revision differs from caller SourceCut'
    }
    $changes = @(& $git.Source -C $staging status --porcelain 2>$null)
    if ($LASTEXITCODE -ne 0 -or $changes.Count -gt 0) {
        Fail-Checkout 'GIT_CLONE_DIRTY' 'First checkout is not clean'
    }
    & $git.Source -C $staging remote remove origin 2>$null
    if ($LASTEXITCODE -ne 0) {
        Fail-Checkout 'GIT_SOURCE_REMOTE_RETAINED' 'Service bundle path must not remain a Git remote'
    }
    try {
        # Directory.Move refuses an existing destination, including a race;
        # never use Move-Item -Force, which could merge/replace an older target.
        [IO.Directory]::Move($staging, $target)
    } catch {
        Fail-Checkout 'ATOMIC_PROMOTION_FAILED' 'Target is unavailable; existing data not overwritten'
    }
} finally {
    if (Test-Path -LiteralPath $staging) {
        Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction Stop
    }
}
[ordered]@{
    schemaVersion = 1
    kind = 'ordivon.workstation.windows-user-git-bundle'
    standing = 'READY_TO_CONSUME'
    checkoutPath = $target
    sourceRevision = $revision
    nonClaims = @('dependencies_materialized', 'external_effects', 'runtime_workspace_provisioned')
} | ConvertTo-Json -Compress
