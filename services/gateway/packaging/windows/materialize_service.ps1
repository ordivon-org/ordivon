[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Prefix,
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-f]{40}$')]
    [string]$ReleaseCommit,
    [Parameter()]
    [ValidatePattern('^[A-Za-z0-9._-]{1,128}$')]
    [string]$ServiceName = 'OrdivonGatewayCandidateR1',
    [Parameter()]
    [ValidateRange(1024, 65535)]
    [int]$Port = 18999,
    [Parameter(Mandatory = $true)]
    [string]$ShawlPath,
    [Parameter()]
    [string]$LinuxRuntimeUrl = 'http://127.0.0.1:8897/mcp',
    [Parameter()]
    [string]$WindowsRuntimeUrl = 'http://127.0.0.1:18997/mcp',
    [Parameter()]
    [string]$HostUrl = 'http://127.0.0.1:8898/mcp',
    [Parameter()]
    [string]$LinuxRuntimeBearerTokenFile = '',
    [Parameter()]
    [string]$WindowsRuntimeBearerTokenFile = '',
    [Parameter()]
    [string]$HostBearerTokenFile = '',
    [Parameter()]
    [ValidateSet('Manual', 'Automatic')]
    [string]$StartMode = 'Automatic',
    [Parameter()]
    [switch]$ReplaceExisting
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-NativeChecked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter()][string[]]$ArgumentList = @()
    )
    $output = & $FilePath @ArgumentList 2>&1
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "native command failed with exit code $($exitCode): $FilePath $($ArgumentList -join ' ') | $($output | Out-String)"
    }
    return $output
}

$prefixPath = [System.IO.Path]::GetFullPath($Prefix)
$release = Join-Path (Join-Path $prefixPath 'releases') $ReleaseCommit
$gatewayExe = Join-Path $release '.venv\Scripts\ordivon-gateway.exe'
$shawl = (Resolve-Path -LiteralPath $ShawlPath).Path
$logs = Join-Path $prefixPath 'logs'
$credentials = Join-Path $prefixPath 'credentials'
$receipts = Join-Path $prefixPath 'receipts'
$releaseReceiptPath = Join-Path $receipts "$ReleaseCommit.json"
New-Item -ItemType Directory -Force -Path $logs, $credentials, $receipts | Out-Null

foreach ($required in @($release, $gatewayExe, $shawl, $releaseReceiptPath)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "required Gateway carrier path is missing: $required"
    }
}
$releaseReceipt = Get-Content -LiteralPath $releaseReceiptPath -Raw | ConvertFrom-Json
if ($releaseReceipt.sourceCommit -ne $ReleaseCommit) {
    throw "Gateway release receipt source commit mismatch"
}
if ([System.IO.Path]::GetFullPath([string]$releaseReceipt.releasePath) -ne $release) {
    throw "Gateway release receipt path mismatch"
}
if ([System.IO.Path]::GetFullPath([string]$releaseReceipt.gatewayExecutable) -ne $gatewayExe) {
    throw "Gateway release receipt executable mismatch"
}

$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existing) {
    if (-not $ReplaceExisting) {
        throw "service already exists: $ServiceName"
    }
    if ($existing.Status -ne 'Stopped') {
        Stop-Service -Name $ServiceName -Force
        $existing.WaitForStatus('Stopped', [TimeSpan]::FromSeconds(30))
    }
    Invoke-NativeChecked -FilePath "$env:SystemRoot\System32\sc.exe" -ArgumentList @(
        'delete', $ServiceName
    ) | Out-Null
    $deadline = (Get-Date).AddSeconds(20)
    while ((Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) -and (Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 250
    }
    if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
        throw "service deletion did not converge: $ServiceName"
    }
}

$envPairs = [ordered]@{
    ORDIVON_GATEWAY_TRANSPORT = 'streamable-http'
    ORDIVON_GATEWAY_HOST = '127.0.0.1'
    ORDIVON_GATEWAY_PORT = [string]$Port
    ORDIVON_GATEWAY_PATH = '/mcp'
    ORDIVON_GATEWAY_LINUX_RUNTIME_URL = $LinuxRuntimeUrl
    ORDIVON_GATEWAY_WINDOWS_RUNTIME_URL = $WindowsRuntimeUrl
    ORDIVON_GATEWAY_HOST_URL = $HostUrl
    ORDIVON_GATEWAY_WINDOWS_SERVICE_NAME = $ServiceName
    OTEL_SERVICE_NAME = 'ordivon-gateway'
    OTEL_TRACES_EXPORTER = 'none'
    OTEL_METRICS_EXPORTER = 'none'
    OTEL_LOGS_EXPORTER = 'none'
}
if ($LinuxRuntimeBearerTokenFile) {
    $envPairs.ORDIVON_GATEWAY_LINUX_RUNTIME_BEARER_TOKEN_FILE = (
        [System.IO.Path]::GetFullPath($LinuxRuntimeBearerTokenFile)
    )
}
if ($WindowsRuntimeBearerTokenFile) {
    $envPairs.ORDIVON_GATEWAY_WINDOWS_RUNTIME_BEARER_TOKEN_FILE = (
        [System.IO.Path]::GetFullPath($WindowsRuntimeBearerTokenFile)
    )
}
if ($HostBearerTokenFile) {
    $envPairs.ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE = (
        [System.IO.Path]::GetFullPath($HostBearerTokenFile)
    )
}

$shawlArgs = @(
    'add',
    '--name', $ServiceName,
    '--no-restart',
    '--stop-timeout', '20000',
    '--kill-process-tree',
    '--cwd', $release,
    '--log-dir', $logs
)
foreach ($entry in $envPairs.GetEnumerator()) {
    $shawlArgs += @('--env', "$($entry.Key)=$($entry.Value)")
}
$shawlArgs += @('--', $gatewayExe)

Invoke-NativeChecked -FilePath $shawl -ArgumentList $shawlArgs | Out-Null

$sc = "$env:SystemRoot\System32\sc.exe"
$serviceAccount = "NT SERVICE\$ServiceName"
$scStartMode = if ($StartMode -eq 'Automatic') { 'auto' } else { 'demand' }
$expectedCimStartMode = if ($StartMode -eq 'Automatic') { 'Auto' } else { 'Manual' }
Invoke-NativeChecked -FilePath $sc -ArgumentList @(
    'config', $ServiceName,
    'start=', $scStartMode,
    'obj=', $serviceAccount
) | Out-Null
Invoke-NativeChecked -FilePath $sc -ArgumentList @(
    'sidtype', $ServiceName, 'unrestricted'
) | Out-Null
Invoke-NativeChecked -FilePath $sc -ArgumentList @(
    'failure', $ServiceName,
    'reset=', '86400',
    'actions=', 'restart/5000/restart/15000/restart/60000'
) | Out-Null
Invoke-NativeChecked -FilePath $sc -ArgumentList @(
    'failureflag', $ServiceName, '1'
) | Out-Null

$service = Get-CimInstance Win32_Service -Filter "Name='$ServiceName'"
if (-not $service) {
    throw "SCM read-back failed for $ServiceName"
}
if ($service.StartMode -ne $expectedCimStartMode) {
    throw "Gateway candidate service start mode mismatch: $($service.StartMode)"
}
if ($service.StartName -ne $serviceAccount) {
    throw "Gateway candidate service account mismatch: $($service.StartName)"
}
if ($service.PathName -notlike "*$ReleaseCommit*" -or $service.PathName -notlike "*--no-restart*") {
    throw "Gateway candidate service path does not bind exact release and wrapper policy"
}

$sidType = (Invoke-NativeChecked -FilePath $sc -ArgumentList @('qsidtype', $ServiceName) | Out-String)
if ($sidType -notmatch 'UNRESTRICTED') {
    throw "Gateway candidate service SID type is not UNRESTRICTED"
}
$failure = (Invoke-NativeChecked -FilePath $sc -ArgumentList @('qfailure', $ServiceName) | Out-String)
if ($failure -notmatch '5000' -or $failure -notmatch '15000' -or $failure -notmatch '60000') {
    throw "Gateway candidate SCM failure actions mismatch"
}

$receipt = [ordered]@{
    schemaVersion = 1
    kind = 'ordivon.gateway-windows-service-materialization'
    serviceName = $ServiceName
    serviceAccount = $serviceAccount
    requestedStartMode = $StartMode
    startMode = $service.StartMode
    state = $service.State
    port = $Port
    sourceCommit = $ReleaseCommit
    releasePath = $release
    gatewayExecutable = $gatewayExe
    shawlPath = $shawl
    shawlSha256 = (Get-FileHash -LiteralPath $shawl -Algorithm SHA256).Hash.ToLowerInvariant()
    releaseReceiptSha256 = (Get-FileHash -LiteralPath $releaseReceiptPath -Algorithm SHA256).Hash.ToLowerInvariant()
    serviceSidType = 'UNRESTRICTED'
    wrapperRestartPolicy = 'no-restart'
    scmFailureActionsMs = @(5000, 15000, 60000)
    ownerServiceDependencies = @()
    linuxRuntimeUrl = $LinuxRuntimeUrl
    windowsRuntimeUrl = $WindowsRuntimeUrl
    hostUrl = $HostUrl
    linuxBearerConfigured = [bool]$LinuxRuntimeBearerTokenFile
    windowsBearerConfigured = [bool]$WindowsRuntimeBearerTokenFile
    hostBearerConfigured = [bool]$HostBearerTokenFile
}
$receiptPath = Join-Path $receipts "$ServiceName.materialization.json"
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $receiptPath -Encoding utf8
$receipt | ConvertTo-Json -Depth 5
