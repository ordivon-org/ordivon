#requires -version 5.1
[CmdletBinding()]
param(
    [ValidateSet('Status', 'AuthorityProfile', 'CrashRecovery', 'ActiveJobRecovery', 'CancelJob')]
    [string]$Mode = 'Status',

    [string]$ServiceName = 'OrdivonRuntimeR6Candidate',
    [string]$Endpoint = 'http://127.0.0.1:18997/mcp',
    [string]$ExpectedNodeId = 'windows-main-r6-candidate',
    [string]$TokenFile = 'C:\ProgramData\Ordivon\RuntimeCandidateR6\secrets\runtime-mcp.token',
    [string]$AcceptanceRoot = 'C:\ProgramData\Ordivon\RuntimeCandidateR6Acceptance',
    [string]$JobId = '',
    [switch]$ApplyFault
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
        throw 'R6c acceptance harness refuses the production service name.'
    }
    if ($Endpoint -eq $ProductionEndpoint -or $Endpoint -match ':8897(?:/|$)') {
        throw 'R6c acceptance harness refuses the production MCP endpoint.'
    }
    if ($ExpectedNodeId -eq $ProductionNodeId) {
        throw 'R6c acceptance harness refuses the production node identity.'
    }
    if ($ServiceName -notmatch 'Candidate') {
        throw 'R6c acceptance harness requires an explicitly candidate-scoped service name.'
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
            name = 'ordivon-r6c-native-acceptance'
            version = '1'
        }
        'io.modelcontextprotocol/clientCapabilities' = @{}
    }

    $headers = @{
        Authorization = ('Bearer ' + $script:BearerToken)
        Accept = 'application/json, text/event-stream'
        'MCP-Protocol-Version' = $ProtocolVersion
        'Mcp-Method' = $Method
        'User-Agent' = 'ordivon-r6c-native-acceptance/1'
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

function Get-ServiceWitness {
    $service = Get-CimInstance Win32_Service -Filter "Name='$ServiceName'"
    if ($null -eq $service) {
        throw "Candidate service $ServiceName does not exist."
    }
    return [pscustomobject]@{
        state = [string]$service.State
        processId = [int]$service.ProcessId
        startMode = [string]$service.StartMode
        startName = [string]$service.StartName
        pathName = [string]$service.PathName
    }
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

function Wait-RecoveredService {
    param(
        [Parameter(Mandatory = $true)][int]$PreviousPid,
        [int]$TimeoutSeconds = 30
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        Start-Sleep -Milliseconds 250
        $current = Get-ServiceWitness
        $oldAlive = $null -ne (Get-Process -Id $PreviousPid -ErrorAction SilentlyContinue)
        if (
            $current.state -eq 'Running' -and
            $current.processId -gt 0 -and
            $current.processId -ne $PreviousPid -and
            -not $oldAlive
        ) {
            return $current
        }
    } while ((Get-Date) -lt $deadline)
    throw "SCM did not recover $ServiceName with a new process identity."
}

function Invoke-CrashRecovery {
    if (-not $ApplyFault) {
        throw 'CrashRecovery requires -ApplyFault.'
    }
    $before = Get-ServiceWitness
    if ($before.state -ne 'Running' -or $before.processId -le 0) {
        throw 'candidate must be Running before crash injection.'
    }
    $runtimeBefore = Get-RuntimeDescribe -Id 10

    Stop-Process -Id $before.processId -Force
    $after = Wait-RecoveredService -PreviousPid $before.processId
    $runtimeAfter = Get-RuntimeDescribe -Id 11

    return [ordered]@{
        schemaVersion = 1
        mode = 'CrashRecovery'
        serviceName = $ServiceName
        beforePid = $before.processId
        afterPid = $after.processId
        pidChanged = ($after.processId -ne $before.processId)
        oldPidAbsent = ($null -eq (Get-Process -Id $before.processId -ErrorAction SilentlyContinue))
        scmState = $after.state
        nodeBefore = $runtimeBefore.node
        nodeAfter = $runtimeAfter.node
        passed = $true
    }
}

function Set-AcceptanceRepositoryOwnerToService {
    param([Parameter(Mandatory = $true)][string]$Path)

    $serviceAccount = "NT SERVICE\$ServiceName"
    $owner = [Security.Principal.NTAccount]::new($serviceAccount).Translate(
        [Security.Principal.SecurityIdentifier])

    $items = @([IO.DirectoryInfo]::new($Path))
    $items += @(Get-ChildItem -LiteralPath $Path -Force -Recurse)
    foreach ($item in $items) {
        $acl = Get-Acl -LiteralPath $item.FullName
        $acl.SetOwner($owner)
        Set-Acl -LiteralPath $item.FullName -AclObject $acl
    }
}

function Ensure-TestRepository {
    $git = 'C:\Program Files\Git\cmd\git.exe'
    if (-not [IO.File]::Exists($git)) {
        throw 'Git for Windows is required for ActiveJobRecovery.'
    }
    $repo = Join-Path $AcceptanceRoot 'source'
    if ([IO.Directory]::Exists($repo)) {
        Remove-Item -LiteralPath $repo -Recurse -Force
    }
    [IO.Directory]::CreateDirectory($repo) | Out-Null
    & $git -C $repo init --initial-branch main | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'git init failed' }
    & $git -C $repo config user.name 'Ordivon R6c Acceptance'
    & $git -C $repo config user.email 'r6c-acceptance@localhost'
    [IO.File]::WriteAllText((Join-Path $repo 'README.txt'), ('R6C acceptance repository' + [Environment]::NewLine))
    & $git -C $repo add README.txt
    & $git -C $repo commit -m 'r6c acceptance seed' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'git commit failed' }
    $revision = (& $git -C $repo rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $revision -notmatch '^[0-9a-f]{40}$') {
        throw 'git rev-parse failed'
    }

    # Git safe.directory is owner-based. Keep its protection enabled and make the
    # candidate-only fixture genuinely owned by the virtual service identity.
    Set-AcceptanceRepositoryOwnerToService -Path $repo
    return [pscustomobject]@{ path = $repo; revision = $revision }
}

function Wait-JobWorking {
    param(
        [Parameter(Mandatory = $true)][string]$JobId,
        [int]$TimeoutSeconds = 15
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $id = 100
    do {
        $id++
        $job = Invoke-McpTool -Name 'task.get' -Arguments @{
            schemaVersion = 1
            jobId = $JobId
            eventLimit = 100
        } -Id $id
        if ($job.attemptState -in @('running', 'starting')) {
            return $job
        }
        if ($job.executionTerminal -eq $true) {
            throw "acceptance Job became terminal before fault injection: $($job.status)"
        }
        Start-Sleep -Milliseconds 200
    } while ((Get-Date) -lt $deadline)
    throw 'acceptance Job did not reach starting/running before timeout.'
}

function Invoke-AuthorityProfile {
    $runtime = Get-RuntimeDescribe -Id 121
    $windowsNative = @($runtime.targets | Where-Object { $_.target -eq 'windows_native' })[0]
    if ($null -eq $windowsNative) {
        throw 'candidate omitted windows_native target.'
    }
    $authorities = @($windowsNative.windowsAuthorities)
    foreach ($required in @('limited', 'elevated')) {
        if ($authorities -notcontains $required) {
            throw "candidate windows_native target does not advertise required authority: $required"
        }
    }

    $powershell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    if (-not [IO.File]::Exists($powershell)) {
        throw "Windows PowerShell target does not exist: $powershell"
    }

    [IO.Directory]::CreateDirectory($AcceptanceRoot) | Out-Null
    $repo = Ensure-TestRepository
    $workspaceId = ('ws-r6c-authority-' + [Guid]::NewGuid().ToString('N').Substring(0, 16))
    $opened = Invoke-McpTool -Name 'workspace.open' -Arguments @{
        schemaVersion = 1
        workspaceId = $workspaceId
        sourceRepo = $repo.path
        sourceRevision = $repo.revision
    } -Id 120

    $probeScript = @'
$id = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($null -eq $id.User) {
    throw 'authority probe token has no user SID'
}
$principal = [Security.Principal.WindowsPrincipal]::new($id)
$admin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$rows = @(
    & "$env:SystemRoot\System32\whoami.exe" /groups /fo csv /nh |
        ConvertFrom-Csv -Header Name,Type,Sid,Attributes
)
$integrity = @($rows | Where-Object { $_.Sid -match '^S-1-16-[0-9]+$' })[0]
if ($null -eq $integrity) {
    throw 'authority probe could not resolve mandatory integrity SID'
}
$rid = [int](($integrity.Sid -split '-')[-1])
[ordered]@{
    tokenUserSid = $id.User.Value
    administratorsEnabled = $admin
    tokenIntegrityLevelRid = $rid
    username = $env:USERNAME
} | ConvertTo-Json -Compress
'@

    function Invoke-AuthorityContextJob([string]$Authority, [int]$Id) {
        $clientRequestId = ('r6c-authority-' + $Authority + '-' + [Guid]::NewGuid().ToString('N'))
        $execution = @{
            workspaceId = $workspaceId
            executable = $powershell
            args = @(
                '-NoLogo',
                '-NoProfile',
                '-NonInteractive',
                '-Command',
                $probeScript
            )
            cwdRelative = '.'
            executionTarget = 'windows_native'
            executionProfile = 'trusted_local'
            windowsAuthority = $Authority
            timeoutMs = 15000
            stdoutLimitBytes = 65536
            stderrLimitBytes = 65536
        }
        $result = Invoke-McpTool -Name 'workspace.exec' -Arguments @{
            schemaVersion = 1
            clientRequestId = $clientRequestId
            execution = $execution
            waitMs = 30000
            stdoutTailBytes = 65536
            stderrTailBytes = 65536
        } -Id $Id
        if ($result.executionTerminal -ne $true -or $result.executionDisposition -ne 'succeeded') {
            throw "$Authority authority target Job did not succeed: $($result | ConvertTo-Json -Depth 12 -Compress)"
        }
        $text = ([string]$result.stdoutTail).Trim()
        if ([string]::IsNullOrWhiteSpace($text)) {
            throw "$Authority authority target Job omitted stdout."
        }
        $context = $text | ConvertFrom-Json
        return [pscustomobject]@{
            observation = $result
            context = $context
        }
    }

    $limited = Invoke-AuthorityContextJob -Authority 'limited' -Id 122
    $elevated = Invoke-AuthorityContextJob -Authority 'elevated' -Id 123

    if ($limited.context.administratorsEnabled -ne $false) {
        throw 'limited authority target unexpectedly has Administrators enabled.'
    }
    if ([int]$limited.context.tokenIntegrityLevelRid -gt 8192) {
        throw 'limited authority target exceeds Medium integrity.'
    }
    if ($elevated.context.administratorsEnabled -ne $true) {
        throw 'elevated authority target does not have Administrators enabled.'
    }
    if ([int]$elevated.context.tokenIntegrityLevelRid -lt 12288) {
        throw 'elevated authority target is below High integrity.'
    }
    if ([string]$limited.context.tokenUserSid -ne [string]$elevated.context.tokenUserSid) {
        throw 'limited and elevated authority targets do not preserve one dedicated service identity.'
    }

    return [ordered]@{
        schemaVersion = 1
        mode = 'AuthorityProfile'
        serviceName = $ServiceName
        workspaceId = $workspaceId
        node = $runtime.node
        executionProvider = $windowsNative.executionProvider
        advertisedAuthorities = $authorities
        limited = [ordered]@{
            jobId = $limited.observation.jobId
            attemptId = $limited.observation.attemptId
            tokenUserSid = $limited.context.tokenUserSid
            administratorsEnabled = $limited.context.administratorsEnabled
            tokenIntegrityLevelRid = $limited.context.tokenIntegrityLevelRid
            username = $limited.context.username
        }
        elevated = [ordered]@{
            jobId = $elevated.observation.jobId
            attemptId = $elevated.observation.attemptId
            tokenUserSid = $elevated.context.tokenUserSid
            administratorsEnabled = $elevated.context.administratorsEnabled
            tokenIntegrityLevelRid = $elevated.context.tokenIntegrityLevelRid
            username = $elevated.context.username
        }
        sameDedicatedUserSid = ([string]$limited.context.tokenUserSid -eq [string]$elevated.context.tokenUserSid)
        passed = $true
    }
}

function Invoke-ActiveJobRecovery {
    if (-not $ApplyFault) {
        throw 'ActiveJobRecovery requires -ApplyFault.'
    }

    [IO.Directory]::CreateDirectory($AcceptanceRoot) | Out-Null
    $repo = Ensure-TestRepository
    $workspaceId = ('ws-r6c-native-recovery-' + [Guid]::NewGuid().ToString('N').Substring(0, 16))
    $clientRequestId = ('r6c-native-recovery-' + [Guid]::NewGuid().ToString('N'))

    $opened = Invoke-McpTool -Name 'workspace.open' -Arguments @{
        schemaVersion = 1
        workspaceId = $workspaceId
        sourceRepo = $repo.path
        sourceRevision = $repo.revision
    } -Id 200

    $execution = @{
        workspaceId = $workspaceId
        executable = 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
        args = @(
            '-NoLogo',
            '-NoProfile',
            '-NonInteractive',
            '-Command',
            "Start-Sleep -Seconds 12; Write-Output 'R6C_ACTIVE_JOB_DONE'"
        )
        cwdRelative = '.'
        executionTarget = 'windows_native'
        executionProfile = 'trusted_local'
        windowsAuthority = 'limited'
        timeoutMs = 30000
        stdoutLimitBytes = 65536
        stderrLimitBytes = 65536
    }

    $admitted = Invoke-McpTool -Name 'workspace.exec' -Arguments @{
        schemaVersion = 1
        clientRequestId = $clientRequestId
        execution = $execution
        waitMs = 0
        stdoutTailBytes = 0
        stderrTailBytes = 0
    } -Id 201

    $jobId = [string]$admitted.jobId
    $attemptId = [string]$admitted.attemptId
    if ([string]::IsNullOrWhiteSpace($jobId)) {
        throw 'workspace.exec omitted jobId.'
    }
    $working = Wait-JobWorking -JobId $jobId

    $serviceBefore = Get-ServiceWitness
    if ($serviceBefore.state -ne 'Running' -or $serviceBefore.processId -le 0) {
        throw 'candidate service is not Running before active-Job crash.'
    }
    Stop-Process -Id $serviceBefore.processId -Force
    $serviceAfter = Wait-RecoveredService -PreviousPid $serviceBefore.processId
    $runtimeAfter = Get-RuntimeDescribe -Id 202

    $terminal = Invoke-McpTool -Name 'task.observe' -Arguments @{
        schemaVersion = 1
        jobId = $jobId
        waitMs = 30000
        waitUntil = 'terminal'
        stdoutTailBytes = 65536
        stderrTailBytes = 65536
    } -Id 203

    $replay = Invoke-McpTool -Name 'workspace.exec' -Arguments @{
        schemaVersion = 1
        clientRequestId = $clientRequestId
        execution = $execution
        waitMs = 0
        stdoutTailBytes = 0
        stderrTailBytes = 0
    } -Id 204

    if ($replay.jobId -ne $jobId) {
        throw 'exact replay returned a different Job identity.'
    }
    if ($attemptId -and $replay.attemptId -and $replay.attemptId -ne $attemptId) {
        throw 'exact replay returned a different Attempt identity.'
    }
    if ($terminal.executionTerminal -ne $true) {
        throw 'restarted Runtime did not converge the candidate Job to terminal evidence.'
    }

    return [ordered]@{
        schemaVersion = 1
        mode = 'ActiveJobRecovery'
        workspaceId = $workspaceId
        clientRequestId = $clientRequestId
        jobId = $jobId
        attemptIdBefore = $attemptId
        attemptIdAfterReplay = $replay.attemptId
        servicePidBefore = $serviceBefore.processId
        servicePidAfter = $serviceAfter.processId
        servicePidChanged = ($serviceAfter.processId -ne $serviceBefore.processId)
        workingBeforeFault = $working.status
        terminalStatus = $terminal.status
        executionDisposition = $terminal.executionDisposition
        deliveryDisposition = $terminal.deliveryDisposition
        stdoutTail = $terminal.stdoutTail
        replaySameJob = ($replay.jobId -eq $jobId)
        nodeAfter = $runtimeAfter.node
        passed = $true
    }
}

Assert-CandidateBoundary
$script:BearerToken = Read-BearerToken

switch ($Mode) {
    'Status' {
        $service = Get-ServiceWitness
        $runtime = Get-RuntimeDescribe -Id 1
        [ordered]@{
            schemaVersion = 1
            mode = 'Status'
            service = $service
            node = $runtime.node
            windowsNative = @($runtime.targets | Where-Object { $_.target -eq 'windows_native' })[0]
            localLinux = @($runtime.targets | Where-Object { $_.target -eq 'local_linux' })[0]
            mutationAttempted = $false
        } | ConvertTo-Json -Depth 16
    }
    'AuthorityProfile' {
        (Invoke-AuthorityProfile) | ConvertTo-Json -Depth 16
    }
    'CrashRecovery' {
        (Invoke-CrashRecovery) | ConvertTo-Json -Depth 16
    }
    'ActiveJobRecovery' {
        (Invoke-ActiveJobRecovery) | ConvertTo-Json -Depth 16
    }
    'CancelJob' {
        if (-not $ApplyFault) {
            throw 'CancelJob requires -ApplyFault.'
        }
        if ([string]::IsNullOrWhiteSpace($JobId) -or $JobId -notmatch '^job-[A-Za-z0-9-]+$') {
            throw 'CancelJob requires an explicit candidate JobId.'
        }
        $cancelled = Invoke-McpTool -Name 'task.cancel' -Arguments @{
            schemaVersion = 1
            jobId = $JobId
        } -Id 300
        [ordered]@{
            schemaVersion = 1
            mode = 'CancelJob'
            jobId = $JobId
            observation = $cancelled
            passed = $true
        } | ConvertTo-Json -Depth 16
    }
}
