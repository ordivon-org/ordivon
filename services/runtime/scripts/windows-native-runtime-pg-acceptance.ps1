#requires -version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('WorkspaceCwdAdmission', 'PrepareFixture', 'PgSession1Readback')]
    [string]$Mode,

    [Parameter(Mandatory=$true)][string]$ServiceName,
    [string]$Endpoint = '',
    [string]$ExpectedNodeId = '',
    [string]$TokenFile = '',
    [string]$AcceptanceRoot = '',
    [string]$PreparedSourceRepo = '',
    [string]$PreparedSourceRevision = '',
    [string]$JobId = '',
    [ValidateRange(1, 65535)]
    [int]$ExpectedActiveUserSessionId = 1,
    [string]$ExpectedActiveUserSid = '',
    [string]$ExpectedAttemptId = '',
    [string]$ExpectedClientRequestId = '',
    [string]$ExpectedMarker = ''
)

$ErrorActionPreference = 'Stop'
# Windows PowerShell 5.1 may attempt to render Invoke-WebRequest progress through a
# non-interactive service console and fail with Win32 ERROR_ACCESS_DENIED. The
# acceptance harness has no interactive progress surface, so suppress it explicitly.
$ProgressPreference = 'SilentlyContinue'
Set-StrictMode -Version Latest

$ProtocolVersion = '2026-07-28'
$ProductionServiceName = 'OrdivonRuntime'
$ProductionEndpoint = 'http://127.0.0.1:8897/mcp'
$ProductionNodeId = 'windows-main'

function Assert-CandidateBoundary {
    if ($ServiceName -eq $ProductionServiceName) {
        throw 'Windows PG acceptance refuses the production service name.'
    }
    if ($Endpoint -eq $ProductionEndpoint -or $Endpoint -match ':8897(?:/|$)') {
        throw 'Windows PG acceptance refuses the production MCP endpoint.'
    }
    if ($ExpectedNodeId -eq $ProductionNodeId) {
        throw 'Windows PG acceptance refuses the production node identity.'
    }
    if ($ServiceName -notmatch 'Candidate' -or $ServiceName -match 'R6') {
        throw 'Windows PG acceptance requires an explicitly candidate-scoped service name.'
    }
}

function Read-BearerToken {
    if (-not [IO.Path]::IsPathRooted($TokenFile) -or -not [IO.File]::Exists($TokenFile)) {
        throw 'TokenFile must be an existing absolute file.'
    }
    $token = [IO.File]::ReadAllText($TokenFile).Trim()
    if ([string]::IsNullOrWhiteSpace($token) -or $token -match '\s') {
        throw 'TokenFile must contain one non-whitespace token.'
    }
    return $token
}

function Invoke-McpRequest {
    param(
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][hashtable]$Params,
        [Parameter(Mandatory = $true)][int]$Id,
        [string]$ToolName = ''
    )

    $requestParams = @{}
    foreach ($key in $Params.Keys) {
        $requestParams[$key] = $Params[$key]
    }
    $requestParams['_meta'] = @{
        'io.modelcontextprotocol/protocolVersion' = $ProtocolVersion
        'io.modelcontextprotocol/clientInfo' = @{
            name = 'ordivon-windows-pg-acceptance'
            version = '1'
        }
        'io.modelcontextprotocol/clientCapabilities' = @{}
    }

    $headers = @{
        Authorization = ('Bearer ' + $script:BearerToken)
        Accept = 'application/json, text/event-stream'
        'MCP-Protocol-Version' = $ProtocolVersion
        'Mcp-Method' = $Method
        'User-Agent' = 'ordivon-windows-pg-acceptance/1'
    }
    if ($ToolName) {
        $headers['Mcp-Name'] = $ToolName
    }

    $body = @{
        jsonrpc = '2.0'
        id = $Id
        method = $Method
        params = $requestParams
    } | ConvertTo-Json -Depth 32 -Compress

    $response = Invoke-WebRequest -UseBasicParsing -Method Post -Uri $Endpoint -Headers $headers -ContentType 'application/json' -Body $body -TimeoutSec 10

    $text = [string]$response.Content
    if ($response.Headers['Content-Type'] -like 'text/event-stream*') {
        $events = @(
            $text -split "\r?\n" |
                Where-Object { $_ -like 'data:*' } |
                ForEach-Object { $_.Substring(5).Trim() }
        )
        if ($events.Count -eq 0) {
            throw "MCP $Method returned an empty event stream."
        }
        $text = $events[-1]
    }
    $message = $text | ConvertFrom-Json
    if ($message.id -ne $Id) {
        throw "MCP $Method returned an unexpected response id."
    }
    $errorProperty = $message.PSObject.Properties['error']
    if ($null -ne $errorProperty -and $null -ne $errorProperty.Value) {
        throw "MCP $Method returned an error: $($errorProperty.Value | ConvertTo-Json -Compress)"
    }
    $resultProperty = $message.PSObject.Properties['result']
    if ($null -eq $resultProperty -or $null -eq $resultProperty.Value) {
        throw "MCP $Method response omitted result."
    }
    return $resultProperty.Value
}

function Invoke-McpTool {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][hashtable]$Arguments,
        [Parameter(Mandatory = $true)][int]$Id
    )
    $result = Invoke-McpRequest -Method 'tools/call' -Params @{ name = $Name; arguments = $Arguments } -Id $Id -ToolName $Name
    $isErrorProperty = $result.PSObject.Properties['isError']
    if ($null -ne $isErrorProperty -and $isErrorProperty.Value -eq $true) {
        $diagnostic = $result | ConvertTo-Json -Depth 16 -Compress
        throw "MCP tool $Name returned isError: $diagnostic"
    }
    $structuredProperty = $result.PSObject.Properties['structuredContent']
    if ($null -eq $structuredProperty -or $null -eq $structuredProperty.Value) {
        throw "MCP tool $Name omitted structuredContent."
    }
    return $structuredProperty.Value
}

function Get-RuntimeDescribe {
    param([int]$Id)
    $runtime = Invoke-McpTool -Name 'runtime.describe' -Arguments @{ schemaVersion = 1 } -Id $Id
    if ($runtime.node.nodeId -ne $ExpectedNodeId) {
        throw "candidate nodeId mismatch: $($runtime.node.nodeId)"
    }
    if ($runtime.node.platform -ne 'windows' -or $runtime.node.native -ne $true) {
        throw 'candidate does not report a native Windows node.'
    }
    return $runtime
}

function Get-CandidateServiceSid {
    $serviceAccount = "NT SERVICE\$ServiceName"
    return [Security.Principal.NTAccount]::new($serviceAccount).Translate(
        [Security.Principal.SecurityIdentifier])
}

function Assert-CurrentTokenIsCandidateServiceIdentity {
    $expected = Get-CandidateServiceSid
    $current = [Security.Principal.WindowsIdentity]::GetCurrent()
    if ($null -eq $current.User -or $current.User.Value -ne $expected.Value) {
        throw 'PrepareFixture must run under the dedicated candidate service identity.'
    }
}

function Ensure-TestRepository {
    Assert-CurrentTokenIsCandidateServiceIdentity
    $git = 'C:\Program Files\Git\cmd\git.exe'
    if (-not [IO.File]::Exists($git)) {
        throw 'Git for Windows is required for PrepareFixture.'
    }
    $repo = Join-Path $AcceptanceRoot 'source'
    if ([IO.Directory]::Exists($repo)) {
        throw 'PrepareFixture requires a fresh acceptance source directory.'
    }
    [IO.Directory]::CreateDirectory($repo) | Out-Null
    & $git -C $repo init --initial-branch main | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'git init failed' }
    & $git -C $repo config user.name 'Ordivon Windows PG Acceptance'
    & $git -C $repo config user.email 'windows-pg-acceptance@localhost'
    [IO.File]::WriteAllText((Join-Path $repo 'README.txt'), ('Windows PG acceptance repository' + [Environment]::NewLine))
    & $git -C $repo add README.txt
    & $git -C $repo commit -m 'Windows PG acceptance seed' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'git commit failed' }
    $revision = (& $git -C $repo rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $revision -notmatch '^[0-9a-f]{40}$') {
        throw 'git rev-parse failed'
    }
    $owner = (Get-Acl -LiteralPath $repo).Owner
    $actualSid = [Security.Principal.NTAccount]::new($owner).Translate(
        [Security.Principal.SecurityIdentifier]).Value
    $expectedSid = (Get-CandidateServiceSid).Value
    if ($actualSid -ne $expectedSid) {
        throw 'PrepareFixture repository owner is not the dedicated candidate service identity.'
    }
    return [pscustomobject]@{ path = $repo; revision = $revision; ownerSid = $actualSid }
}

function Resolve-PreparedTestRepository {
    if ([string]::IsNullOrWhiteSpace($PreparedSourceRepo) -or
        [string]::IsNullOrWhiteSpace($PreparedSourceRevision)) {
        throw 'WorkspaceCwdAdmission requires -PreparedSourceRepo and -PreparedSourceRevision from PrepareFixture.'
    }
    if (-not [IO.Path]::IsPathRooted($PreparedSourceRepo) -or
        -not [IO.Directory]::Exists($PreparedSourceRepo)) {
        throw 'PreparedSourceRepo must be an existing absolute directory.'
    }
    if ($PreparedSourceRevision -notmatch '^[0-9a-f]{40}$') {
        throw 'PreparedSourceRevision must be one exact 40-character Git commit.'
    }
    $root = [IO.Path]::GetFullPath($AcceptanceRoot).TrimEnd('\')
    $repo = [IO.Path]::GetFullPath($PreparedSourceRepo).TrimEnd('\')
    if (-not ($repo + '\').StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'PreparedSourceRepo must stay beneath AcceptanceRoot.'
    }
    # Do not make LocalSystem a second Git authority for a repository owned by the
    # dedicated service identity. workspace.open resolves and verifies the exact
    # PreparedSourceRevision under the Runtime service identity immediately after
    # this ownership/path preflight.
    $owner = (Get-Acl -LiteralPath $repo).Owner
    $actualSid = [Security.Principal.NTAccount]::new($owner).Translate(
        [Security.Principal.SecurityIdentifier]).Value
    $expectedSid = (Get-CandidateServiceSid).Value
    if ($actualSid -ne $expectedSid) {
        throw 'PreparedSourceRepo is not owned by the dedicated candidate service identity.'
    }
    return [pscustomobject]@{ path = $repo; revision = $PreparedSourceRevision; ownerSid = $actualSid }
}

function Invoke-WorkspaceCwdAdmission {
    # Selected PG qualification is an external authenticated consumer of a
    # prepared service-owned repository, not a second source owner.
    if ($ExpectedActiveUserSid -cnotmatch '^S-1-(5-21-(?:[0-9]+-){3}[0-9]+|12-1-(?:[0-9]+-){3}[0-9]+)$') {
        throw 'Fresh PG requires the operator-bound interactive account SID.'
    }
    $runtime = Get-RuntimeDescribe -Id 340
    $windowsNative = @($runtime.targets | Where-Object { $_.target -eq 'windows_native' })[0]
    if ($null -eq $windowsNative -or
        @($windowsNative.windowsAuthorities) -notcontains 'active_user') {
        throw 'candidate has no active_user Windows execution capability.'
    }

    $repo = Resolve-PreparedTestRepository
    $workspaceId = ('ws-winpg-cwd-identity-' + [Guid]::NewGuid().ToString('N').Substring(0, 14))
    $opened = Invoke-McpTool -Name 'workspace.open' -Arguments @{
        schemaVersion = 1
        workspaceId = $workspaceId
        sourceRepo = $repo.path
        sourceRevision = $repo.revision
    } -Id 341
    if ([string]$opened.workspaceId -ne $workspaceId) {
        throw 'candidate returned a different Workspace identity.'
    }

    $qualified = $false
    try {
        $powershell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
        $probe = @'
$ErrorActionPreference = 'Stop'
$id = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($null -eq $id.User) { throw "target user SID is missing" }
# The ordinary native Job must prove its exact private Git carrier,
# not just return a successful process CWD. Use the existing Git for
# Windows executable and process-scoped environment from the provider.
$git = 'C:\Program Files\Git\cmd\git.exe'
if (-not [IO.File]::Exists($git)) { throw 'Native Git executable absent.' }
function Invoke-ProbeGit([string[]]$Arguments) {
    $lines = @(& $git @Arguments)
    if ($LASTEXITCODE -ne 0) { throw 'Native private Git command failed.' }
    return $lines
}
function Assert-ProbePath([string]$Actual, [string]$Expected) {
    if ([string]::IsNullOrWhiteSpace($Actual) -or
        -not [String]::Equals([IO.Path]::GetFullPath($Actual).TrimEnd('\'),
            [IO.Path]::GetFullPath($Expected).TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Native private Git carrier differs from exact Workspace.'
    }
}
$workTree = [IO.Path]::GetFullPath((Get-Location).ProviderPath).TrimEnd('\')
Assert-ProbePath ([Environment]::CurrentDirectory) $workTree
$gitDir = Join-Path ([IO.Path]::GetDirectoryName($workTree)) ('.' + [IO.Path]::GetFileName($workTree) + '.agent-git')
Assert-ProbePath $env:GIT_WORK_TREE $workTree
Assert-ProbePath $env:GIT_DIR $gitDir
Assert-ProbePath ([string](Invoke-ProbeGit @('rev-parse','--show-toplevel'))) $workTree
Assert-ProbePath ([string](Invoke-ProbeGit @('rev-parse','--absolute-git-dir'))) $gitDir
$head = [string](Invoke-ProbeGit @('rev-parse','HEAD'))
if ($head -notmatch '^[0-9a-f]{40}$' -or @(Invoke-ProbeGit @('status','--porcelain=v1','--untracked-files=all')).Count -ne 0) {
    throw 'Native private Git baseline is not a clean exact commit.'
}
$sourceFile = 'README.txt' # original PrepareFixture tracked input
$sourceFileSha256 = (Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash.ToLowerInvariant()
$sourceBlob = [string](Invoke-ProbeGit @('rev-parse',('HEAD:' + $sourceFile)))
$sourceHash = [string](Invoke-ProbeGit @('hash-object',('--path=' + $sourceFile),$sourceFile))
if ($sourceBlob -ne $sourceHash) { throw 'Native tracked source bytes differ from the Git blob.' }

# Use a fresh disposable relative path. A successful probe must leave
# both the private index and linked worktree unchanged for normal close.
$marker = 'ordivon-pg-acceptance-' + [Guid]::NewGuid().ToString('N') + '.txt'
$payload = [Text.Encoding]::UTF8.GetBytes('native-private-git-write-witness')
if ([IO.File]::Exists($marker) -or [IO.Directory]::Exists($marker)) { throw 'Probe marker collision.' }
$created = $false
try {
    $stream = [IO.File]::Open($marker,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    $created = $true
    try { $stream.Write($payload,0,$payload.Length) } finally { $stream.Dispose() }
    if ([Convert]::ToBase64String([IO.File]::ReadAllBytes($marker)) -ne [Convert]::ToBase64String($payload)) {
        throw 'Native relative Workspace write readback differs.'
    }
    $null = Invoke-ProbeGit @('add','--',$marker)
    $markerBlob = [string](Invoke-ProbeGit @('rev-parse',(':' + $marker)))
    $markerHash = [string](Invoke-ProbeGit @('hash-object',('--path=' + $marker),$marker))
    if ($markerBlob -notmatch '^[0-9a-f]{40}$' -or $markerBlob -ne $markerHash) {
        throw 'Native private index did not retain the exact marker blob.'
    }
} finally {
    if ($created) {
        $null = Invoke-ProbeGit @('reset','-q','HEAD','--',$marker)
        [IO.File]::Delete($marker)
    }
}
if (@(Invoke-ProbeGit @('status','--porcelain=v1','--untracked-files=all')).Count -ne 0 -or
    [string](Invoke-ProbeGit @('rev-parse','HEAD')) -ne $head -or [IO.File]::Exists($marker)) {
    throw 'Native private Git probe did not restore the exact clean baseline.'
}
$gitWitness = [ordered]@{
    head = $head; gitDir = $gitDir; workTree = $workTree
    sourceFileSha256 = $sourceFileSha256; sourceBlob = $sourceBlob
    relativeWriteVerified = $true; indexVerified = $true; cleanAfter = $true
}
[ordered]@{
    userSid = $id.User.Value
    sessionId = [Diagnostics.Process]::GetCurrentProcess().SessionId
    nativeCwd = [IO.Path]::GetFullPath([Environment]::CurrentDirectory)
    actualCwd = [IO.Path]::GetFullPath((Get-Location).ProviderPath)
    privateGit = $gitWitness
} | ConvertTo-Json -Compress
'@
        function Invoke-CwdIdentityJob([string]$Authority, [int]$Id) {
            $execution = @{
                workspaceId = $workspaceId
                executable = $powershell
                args = @('-NoProfile', '-NonInteractive', '-Command', $probe)
                cwdRelative = '.'
                executionTarget = 'windows_native'
                windowsAuthority = $Authority
                timeoutMs = 20000
                stdoutLimitBytes = 16384
                stderrLimitBytes = 16384
            }
            $request = @{
                schemaVersion = 1
                clientRequestId = ('winpg-cwd-' + $Authority + '-' + [Guid]::NewGuid().ToString('N'))
                execution = $execution
                waitMs = 30000
                stdoutTailBytes = 16384
                stderrTailBytes = 16384
            }
            $result = Invoke-McpTool -Name 'workspace.exec' -Arguments $request -Id $Id
            if ($result.executionTerminal -eq $true -and $result.executionDisposition -eq 'succeeded') {
                $replay = Invoke-McpTool -Name 'workspace.exec' -Arguments $request -Id ($Id + 100)
                if ($replay.jobId -ne $result.jobId -or $replay.attemptId -ne $result.attemptId -or
                    $replay.executionDisposition -ne 'succeeded') {
                    throw 'exact Workspace CWD replay did not preserve the successful Job and Attempt.'
                }
                if ($result.operationDigest -cnotmatch '^sha256:[0-9a-f]{64}$' -or
                    $replay.operationDigest -cne $result.operationDigest) {
                    throw 'Fresh PG exact replay operation digest differs.'
                }
                $inspection = Invoke-McpTool -Name 'job.get' -Arguments @{
                    schemaVersion = 1; jobId = [string]$result.jobId; eventLimit = 200
                } -Id ($Id + 200)
                Assert-PgSession1Projection $inspection ([string]$result.jobId) ([string]$result.attemptId) ([string]$request.clientRequestId)
                if ($inspection.job.operationDigest -cne $result.operationDigest -or
                    $inspection.job.workspaceId -cne $workspaceId -or $inspection.job.sourceRevision -cne $repo.revision) {
                    throw 'Fresh PG inspection operation or Workspace source identity differs.'
                }
            }
            return $result
        }

        function Read-VerifiedCwdStdout($Observation, [int]$Id) {
            $matches = @($Observation.artifacts | Where-Object { $_.kind -eq 'stdout' })
            if ($matches.Count -ne 1 -or $matches[0].truncated -ne $false -or
                $matches[0].retainedBytes -le 0 -or $matches[0].retainedBytes -gt 16384) {
                throw 'Workspace CWD probe lacks a complete bounded stdout Artifact.'
            }
            $descriptor = $matches[0]
            if ($descriptor.attemptId -cne $Observation.attemptId -or
                $descriptor.artifactId -cne ($Observation.attemptId + '.stdout')) {
                throw 'Fresh PG stdout descriptor belongs to a different Attempt.'
            }
            $read = Invoke-McpTool -Name 'artifact.read' -Arguments @{
                schemaVersion = 1
                jobId = [string]$Observation.jobId
                artifactId = [string]$descriptor.artifactId
                offset = 0
                maxBytes = 16384
            } -Id $Id
            $bytes = [Text.Encoding]::UTF8.GetBytes([string]$read.content)
            $sha = [Security.Cryptography.SHA256]::Create()
            try {
                $digest = 'sha256:' + [BitConverter]::ToString($sha.ComputeHash($bytes)).Replace('-', '').ToLowerInvariant()
            }
            finally {
                $sha.Dispose()
            }
            if ($read.jobId -ne $Observation.jobId -or $read.artifactId -ne $descriptor.artifactId -or
                $read.offset -ne 0 -or $read.eof -ne $true -or
                $read.nextOffset -ne $descriptor.retainedBytes -or $bytes.Length -ne $descriptor.retainedBytes -or
                $read.digest -ne $descriptor.digest -or $digest -ne $descriptor.digest) {
                throw 'Workspace CWD stdout Artifact identity, length or SHA-256 mismatch.'
            }
            return ([string]$read.content).Trim() | ConvertFrom-Json
        }

        $limited = Invoke-CwdIdentityJob -Authority 'limited' -Id 342
        if ($limited.executionTerminal -ne $true -or
            $limited.executionDisposition -ne 'succeeded') {
            throw 'candidate limited Workspace CWD baseline did not succeed.'
        }
        $baseline = Read-VerifiedCwdStdout $limited 542
        $expectedCwd = [IO.Path]::GetFullPath([string]$baseline.actualCwd).TrimEnd('\')
        if (-not $expectedCwd.EndsWith(('\' + $workspaceId), [StringComparison]::OrdinalIgnoreCase)) {
            throw 'candidate limited baseline does not end at the opened Workspace identity.'
        }

        $active = Invoke-CwdIdentityJob -Authority 'active_user' -Id 343
        if ($active.executionTerminal -ne $true) {
            throw 'active-user Workspace Job is unresolved; no semantic acceptance.'
        }
        if ($active.executionDisposition -ne 'succeeded') {
            throw ("active-user Workspace execution is not operationally qualified: " +
                [string]$active.executionDisposition + " jobId=" + [string]$active.jobId)
        }

        $actual = Read-VerifiedCwdStdout $active 543
        Assert-PgSession1ActiveIdentity $actual $ExpectedActiveUserSid $ExpectedActiveUserSessionId
        $actualCwd = [IO.Path]::GetFullPath([string]$actual.actualCwd).TrimEnd('\')
        if ([int]$baseline.sessionId -ne 0 -or [int]$actual.sessionId -ne $ExpectedActiveUserSessionId) {
            throw 'Workspace execution does not preserve the expected service and interactive Session identities.'
        }
        foreach ($probeCwd in @($baseline.nativeCwd, $actual.nativeCwd)) {
            if (-not [String]::Equals($expectedCwd, [IO.Path]::GetFullPath([string]$probeCwd).TrimEnd('\'),
                    [StringComparison]::OrdinalIgnoreCase)) {
                throw 'native process CWD differs from the bound Workspace.'
            }
        }
        if (-not [String]::Equals($expectedCwd, $actualCwd, [StringComparison]::OrdinalIgnoreCase)) {
            throw ("active-user target ran outside the bound Workspace: expectedCwd=" +
                $expectedCwd + " actualCwd=" + $actualCwd)
        }
        if ([String]::Equals([string]$baseline.userSid, [string]$actual.userSid,
                [StringComparison]::OrdinalIgnoreCase)) {
            throw 'active-user Workspace job reused the service principal unexpectedly.'
        }

        foreach ($witness in @($baseline.privateGit,$actual.privateGit)) {
            if ($null -eq $witness -or $witness.head -ne $repo.revision -or
                $witness.relativeWriteVerified -ne $true -or $witness.indexVerified -ne $true -or
                $witness.cleanAfter -ne $true -or $witness.sourceFileSha256 -notmatch '^[0-9a-f]{64}$' -or
                $witness.sourceBlob -notmatch '^[0-9a-f]{40}$') {
                throw 'Fresh PG native Git consumer qualification missing or incomplete.'
            }
        }
        foreach ($field in @('gitDir','workTree','sourceFileSha256','sourceBlob')) {
            if (-not [String]::Equals([string]$baseline.privateGit.$field,[string]$actual.privateGit.$field,
                    [StringComparison]::OrdinalIgnoreCase)) {
                throw 'Service and Session1 Git consumers observed different exact source carriers.'
            }
        }
        $qualified = $true
        return [ordered]@{
            schemaVersion = 1
            mode = 'WorkspaceCwdAdmission'
            workspaceId = $workspaceId
            limitedJobId = $limited.jobId
            activeUserJobId = $active.jobId
            expectedCwd = $expectedCwd
            actualCwd = $actualCwd
            activeUserSid = [string]$actual.userSid
            activeUserSessionId = [int]$actual.sessionId
            activeUserAttemptId = [string]$active.attemptId
            verifiedStdoutDigest = [string](@($active.artifacts | Where-Object { $_.kind -eq 'stdout' })[0].digest)
            exactReplayVerified = $true
            freshPgProjectionQualified = $true
            privateGitQualified = $true
            privateGitWitness = $actual.privateGit
            passed = $true
        }
    }
    finally {
        # A failed fresh-PG probe is retained for original Job reconciliation.
        if ($qualified) {
            # Source-digest CAS, active-Job fence and consumer checks remain Runtime
            # authority; never force-delete a possibly changed physical Workspace.
            $state = Invoke-McpTool -Name 'workspace.get' -Arguments @{
                schemaVersion = 1
                workspaceId = $workspaceId
            } -Id 344
            $closeRequest = @{
                schemaVersion = 1
                workspaceId = $workspaceId
                expectedSourceStateDigest = [string]$state.sourceStateDigest
                force = $false
            }
            $closeRequest.consumerReleased = $true
            $closed = Invoke-McpTool -Name 'workspace.close' -Arguments $closeRequest -Id 345
            if ($closed.closureDisposition -notin @('removed', 'already_closed')) {
                throw 'candidate test Workspace did not close with an exact source digest.'
            }
        }
    }
}

function Assert-PgSession1ActiveIdentity {
    param($Observation,[string]$ExpectedSid,[int]$ExpectedSession)
    if ($ExpectedSid -cnotmatch '^S-1-(5-21-(?:[0-9]+-){3}[0-9]+|12-1-(?:[0-9]+-){3}[0-9]+)$' -or
        $Observation.userSid -isnot [string] -or $Observation.userSid -cne $ExpectedSid -or
        ($Observation.sessionId -isnot [int] -and $Observation.sessionId -isnot [long]) -or
        $Observation.sessionId -ne $ExpectedSession) {
        throw 'PG_SESSION1_OPERATOR_ACCOUNT_IDENTITY_MISMATCH'
    }
}

function Assert-PgSession1Projection {
    param($Inspection, [string]$ExpectedJob, [string]$ExpectedAttempt, [string]$ExpectedRequest)
    if (($Inspection.schemaVersion -isnot [int] -and $Inspection.schemaVersion -isnot [long]) -or
        $Inspection.schemaVersion -ne 2 -or
        ($Inspection.migrationVersion -isnot [int] -and $Inspection.migrationVersion -isnot [long]) -or
        $Inspection.migrationVersion -ne 0) {
        throw 'PG_SESSION1_REQUIRED_FRESH_PG_PROJECTION'
    }
    if ($Inspection.job.jobId -cne $ExpectedJob -or
        $Inspection.job.clientRequestId -cne $ExpectedRequest -or
        $Inspection.job.resolution -cne 'succeeded' -or
        $Inspection.job.mechanicallyConverged -ne $true -or
        $Inspection.attemptsTruncated -ne $false -or
        $Inspection.eventsTruncated -ne $false -or
        @($Inspection.attempts).Count -ne 1) {
        throw 'PG_SESSION1_JOB_IDENTITY_OR_TERMINAL_MISMATCH'
    }
    $a = @($Inspection.attempts)[0]
    if ($a.attemptId -cne $ExpectedAttempt -or $a.state -cne 'succeeded' -or
        $a.exitCode -ne 0 -or $a.resultAvailable -ne $true -or
        $a.reservationState -cne 'released' -or $Inspection.artifacts.truncated -ne 0) {
        throw 'PG_SESSION1_ATTEMPT_NOT_QUALIFIED'
    }
    # PG inspection episodes are currently a default projection; use the actual
    # bounded event timeline instead of treating a zero aggregate as proof.
    $dispatch = @($Inspection.timeline | Where-Object { $_.eventType -ceq 'DISPATCH_ISSUED' })
    if ($dispatch.Count -ne 1 -or $dispatch[0].attemptId -cne $ExpectedAttempt) {
        throw 'PG_SESSION1_DISPATCH_IDENTITY_MISMATCH'
    }
}

function Assert-PgSession1Artifact {
    param($Artifact, [string]$ExpectedJob, [string]$ExpectedAttempt, [string]$Marker)
    $expectedArtifact = "$ExpectedAttempt.stdout"
    if ($Artifact.jobId -cne $ExpectedJob -or $Artifact.artifactId -cne $expectedArtifact -or
        $Artifact.eof -ne $true -or $Artifact.offset -ne 0) {
        throw 'PG_SESSION1_ARTIFACT_IDENTITY_MISMATCH'
    }
    $bytes = [Text.Encoding]::UTF8.GetBytes([string]$Artifact.content)
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $actual = 'sha256:' + ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
    if ($Artifact.digest -cne $actual -or $Artifact.nextOffset -ne $bytes.Length) {
        throw 'PG_SESSION1_ARTIFACT_BYTES_MISMATCH'
    }
    $body = $Artifact.content | ConvertFrom-Json
    if (($body.sessionId -isnot [int] -and $body.sessionId -isnot [long]) -or $body.sessionId -ne 1 -or $body.marker -cne $Marker) {
        throw 'PG_SESSION1_PHYSICAL_PROBE_MISMATCH'
    }
}

function Invoke-PgSession1Readback {
    if ($JobId -notmatch '^job-[A-Za-z0-9-]+$' -or
        $ExpectedAttemptId -notmatch '^attempt-[A-Za-z0-9-]+$' -or
        [string]::IsNullOrWhiteSpace($ExpectedClientRequestId) -or
        [string]::IsNullOrWhiteSpace($ExpectedMarker)) {
        throw 'PgSession1Readback requires explicit Job, Attempt, request and probe marker identities.'
    }
    $runtime = Get-RuntimeDescribe -Id 410
    $inspection = Invoke-McpTool -Name 'job.get' -Arguments @{
        schemaVersion = 1; jobId = $JobId; eventLimit = 200
    } -Id 411
    Assert-PgSession1Projection $inspection $JobId $ExpectedAttemptId $ExpectedClientRequestId
    $artifact = Invoke-McpTool -Name 'artifact.read' -Arguments @{
        schemaVersion = 1; jobId = $JobId; artifactId = "$ExpectedAttemptId.stdout"; offset = 0; maxBytes = 4096
    } -Id 412
    Assert-PgSession1Artifact $artifact $JobId $ExpectedAttemptId $ExpectedMarker
    return [ordered]@{
        schemaVersion = 1; mode = 'PgSession1Readback'; node = $runtime.node
        jobId = $JobId; attemptId = $ExpectedAttemptId; stdoutDigest = $artifact.digest
        pgProjectionQualified = $true; session1ArtifactQualified = $true
        uniqueWriterQualified = $false; cutoverAccepted = $false
    }
}

Assert-CandidateBoundary
if ($Mode -in @('PrepareFixture', 'WorkspaceCwdAdmission') -and
    -not [IO.Path]::IsPathRooted($AcceptanceRoot)) {
    throw 'An absolute AcceptanceRoot is required for fixture operations.'
}
if ($Mode -ne 'PrepareFixture') {
    if ($Endpoint -notmatch '^http://127\.0\.0\.1:[0-9]{1,5}/mcp$' -or
        [string]::IsNullOrWhiteSpace($ExpectedNodeId)) {
        throw 'An exact loopback MCP endpoint and expected PG node are required.'
    }
    $script:BearerToken = Read-BearerToken
}

switch ($Mode) {
    'WorkspaceCwdAdmission' {
        (Invoke-WorkspaceCwdAdmission) | ConvertTo-Json -Depth 16
    }
    'PrepareFixture' {
        $repo = Ensure-TestRepository
        [ordered]@{
            schemaVersion = 1
            mode = 'PrepareFixture'
            sourceRepo = $repo.path
            sourceRevision = $repo.revision
            ownerSid = $repo.ownerSid
            passed = $true
        } | ConvertTo-Json -Depth 16
    }
    'PgSession1Readback' {
        (Invoke-PgSession1Readback) | ConvertTo-Json -Depth 16
    }
}
