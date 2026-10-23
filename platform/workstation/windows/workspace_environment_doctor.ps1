# Read-only Windows Runtime Workspace consumer doctor.
# Use windowsAuthority=active_user and native pwsh; never provision a second account.
[CmdletBinding()]
param(
    [string[]]$Tools = @(),
    # Only a caller-supplied, verified SourceCut may receive scoped mise trust.
    [string]$ExpectedRevision = '',
    # Opt-in for login-user-owned standalone Git clone; service-private
    # linked worktrees remain inaccessible to the desktop user.
    [string]$WorkspacePath = '',
    # Normal Agent Golden Path requires a usable Git worktree by default.
    # Explicit -RequireGit:$false is only for a tool-only diagnostic.
    [switch]$RequireGit = $true
)

$ErrorActionPreference = 'Stop'
function Fail-Workspace([string]$Code, [string]$Detail) {
    [Console]::Error.WriteLine((([ordered]@{
        schemaVersion = 1
        kind = 'ordivon.workstation.windows-workspace-environment'
        standing = 'FAILED'
        reasonCode = $Code
        detail = $Detail
    }) | ConvertTo-Json -Compress))
    exit 69
}

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    Fail-Workspace 'WINDOWS_ONLY' 'Native Windows Runtime is required'
}
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($identity.Name.StartsWith('NT SERVICE\', [StringComparison]::OrdinalIgnoreCase) -or
    $identity.User.Value -in @('S-1-5-18', 'S-1-5-19', 'S-1-5-20')) {
    Fail-Workspace 'SERVICE_IDENTITY_NOT_AGENT' 'Select Windows Runtime windowsAuthority=active_user'
}
$physicalCwd = [IO.Directory]::GetCurrentDirectory()
if ($WorkspacePath) {
    if (-not $RequireGit -or $ExpectedRevision -notmatch '^[0-9a-fA-F]{40}$' -or
        -not [IO.Path]::IsPathRooted($WorkspacePath)) {
        Fail-Workspace 'STANDALONE_CHECKOUT_REQUIRED' 'Exact Git SourceCut and absolute standalone checkout required'
    }
    $physicalCwd = [IO.Path]::GetFullPath($WorkspacePath)
    $gitMetadata = Join-Path $physicalCwd '.git'
    if (-not (Test-Path -LiteralPath $gitMetadata -PathType Container) -or
        (Test-Path -LiteralPath (Join-Path $gitMetadata 'objects\info\alternates'))) {
        Fail-Workspace 'STANDALONE_CHECKOUT_REQUIRED' 'Linked worktree, object alternates or missing .git directory'
    }
    $dir = Get-Item -LiteralPath $physicalCwd -ErrorAction Stop
    $metadata = Get-Item -LiteralPath $gitMetadata -Force -ErrorAction Stop
    if (($dir.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
        ($metadata.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        Fail-Workspace 'STANDALONE_CHECKOUT_REQUIRED' 'Clone may not be a reparse point'
    }
}
try {
    # PowerShell may start at PSHOME even though CreateProcessAsUser received
    # the intended cwd. Read the process cwd and exercise real user ACL access.
    Set-Location -LiteralPath $physicalCwd -ErrorAction Stop
    if (-not [string]::Equals(
            (Get-Location).ProviderPath.TrimEnd('\'),
            $physicalCwd.TrimEnd('\'),
            [StringComparison]::OrdinalIgnoreCase)) {
        throw 'PowerShell selected a different working directory'
    }
} catch {
    Fail-Workspace 'WORKSPACE_ACCESS_DENIED' 'Login user cannot enter the Runtime Workspace; verify per-workspace ACL and ancestor traversal'
}

$git = Get-Command git -CommandType Application -ErrorAction SilentlyContinue
if ($RequireGit) {
    if (-not $git) {
        Fail-Workspace 'WORKSPACE_GIT_UNAVAILABLE' 'Git is not available in the active-user PATH'
    }
    $gitRoot = & $git.Source -C $physicalCwd rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $gitRoot) {
        Fail-Workspace 'WORKSPACE_GIT_UNAVAILABLE' 'Git checkout or linked Git metadata is inaccessible to the login user; verify exact worktree and common gitdir access'
    }
}
if ($WorkspacePath) {
    # Git for Windows returns C:/..., PowerShell uses C:\... .
    $gitPath = [IO.Path]::GetFullPath(([string]$gitRoot).Trim().Replace('/', '\'))
    if (-not [string]::Equals($gitPath.TrimEnd('\'), $physicalCwd.TrimEnd('\'),
            [StringComparison]::OrdinalIgnoreCase)) {
        Fail-Workspace 'STANDALONE_CHECKOUT_REQUIRED' 'Git root must be the exact login-user checkout'
    }
    $porcelain = @(& $git.Source -C $physicalCwd status --porcelain 2>$null)
    if ($LASTEXITCODE -ne 0 -or @($porcelain).Count -gt 0) {
        Fail-Workspace 'STANDALONE_CHECKOUT_REQUIRED' 'Git checkout must be clean before trusting owner tools'
    }
    $committed = @(& $git.Source -C $physicalCwd rev-parse 'HEAD:mise.toml' 2>$null)
    $commitExit = $LASTEXITCODE
    $actual = @(& $git.Source -C $physicalCwd hash-object mise.toml 2>$null)
    $actualExit = $LASTEXITCODE
    if ($commitExit -ne 0 -or $actualExit -ne 0 -or
        @($committed).Count -ne 1 -or @($actual).Count -ne 1 -or
        ([string]$committed[0]).Trim() -cne ([string]$actual[0]).Trim()) {
        Fail-Workspace 'STANDALONE_CHECKOUT_REQUIRED' 'Owner mise manifest must exactly match pinned Git source'
    }
}
# A service-provided Git bundle can become a login-user-owned checkout.
# Validate the exact immutable revision before mise reads any project config.
if ($ExpectedRevision -ne '') {
    if (-not $RequireGit -or $ExpectedRevision -notmatch '^[0-9a-fA-F]{40}$') {
        Fail-Workspace 'INVALID_EXPECTED_REVISION' 'Full Git SHA and RequireGit are needed for scoped trust'
    }
    $observedRevision = & $git.Source -C $physicalCwd rev-parse HEAD 2>$null
    if ($LASTEXITCODE -ne 0 -or
        -not [string]::Equals(([string]$observedRevision).Trim(), $ExpectedRevision,
            [StringComparison]::OrdinalIgnoreCase)) {
        Fail-Workspace 'WORKSPACE_REVISION_MISMATCH' 'Checkout HEAD differs from the independently supplied SourceCut'
    }
    $env:MISE_TRUSTED_CONFIG_PATHS = [IO.Path]::GetFullPath(([string]$gitRoot).Trim())
}
# Never auto-download stale versions during an environment diagnostic.
$env:MISE_AUTO_INSTALL = 'false'
$owner = $physicalCwd
$ownerSearchBoundary = if ($RequireGit) {
    [IO.Path]::GetFullPath(([string]$gitRoot).Trim())
} else {
    [IO.Path]::GetPathRoot($physicalCwd)
}
while (-not (Test-Path -LiteralPath (Join-Path $owner 'mise.toml') -PathType Leaf)) {
    $parent = [IO.Directory]::GetParent($owner)
    if ($null -eq $parent -or
        [string]::Equals($owner, $ownerSearchBoundary, [StringComparison]::OrdinalIgnoreCase)) {
        Fail-Workspace 'OWNER_MANIFEST_MISSING' 'No owner mise.toml exists inside the Git Workspace'
    }
    $owner = $parent.FullName
}
Set-Location -LiteralPath $owner

$mise = Get-Command mise -CommandType Application -ErrorAction SilentlyContinue
if (-not $mise) {
    Fail-Workspace 'OWNER_TOOL_UNAVAILABLE' 'mise is not available for the active-user identity'
}
$selectedToolPaths = [ordered]@{}
foreach ($tool in $Tools) {
    if ($tool -notmatch '^[A-Za-z][A-Za-z0-9._-]*$') {
        Fail-Workspace 'INVALID_TOOL' 'Tool names must be plain executable names'
    }
    $selected = @(& $mise.Source which $tool 2>$null)
    $selectionExitCode = $LASTEXITCODE
    if ($selectionExitCode -ne 0 -or -not $selected -or -not $selected[0]) {
        Fail-Workspace 'OWNER_TOOL_UNAVAILABLE' ("mise cannot resolve locked owner tool: " + $tool)
    }
    if (([string]$selected[0]) -match '\\WindowsApps\\') {
        Fail-Workspace 'WINDOWSAPPS_ALIAS_NOT_INTERPRETER' ("The selected tool resolves to a WindowsApps alias: " + $tool)
    }
    $selectedPath = [string]$selected[0]
    if (-not (Test-Path -LiteralPath $selectedPath -PathType Leaf)) {
        Fail-Workspace 'OWNER_TOOL_UNAVAILABLE' ("Selected owner tool is not an accessible file: " + $tool)
    }
    $selectedToolPaths[$tool] = $selectedPath
}
[ordered]@{
    schemaVersion = 1
    kind = 'ordivon.workstation.windows-workspace-environment'
    standing = 'READY_TO_CONSUME'
    selectedToolCount = @($Tools).Count
    selectedToolPaths = $selectedToolPaths
    nonClaims = @('dependencies_materialized', 'task_completed', 'external_effects')
} | ConvertTo-Json -Compress
