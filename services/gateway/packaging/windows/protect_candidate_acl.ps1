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
    [Parameter(Mandatory = $true)]
    [string]$ShawlPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-IcaclsChecked {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    $output = & "$env:SystemRoot\System32\icacls.exe" @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "icacls failed with exit code $($LASTEXITCODE): $($Arguments -join ' ') | $($output | Out-String)"
    }
}

function Protect-Directory {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$ServiceSid,
        [Parameter(Mandatory = $true)][ValidateSet('RX','M','R')][string]$ServiceRights
    )
    Invoke-IcaclsChecked -Arguments @(
        $Path,
        '/inheritance:r',
        '/grant:r',
        '*S-1-5-18:(OI)(CI)(F)',
        '*S-1-5-32-544:(OI)(CI)(F)',
        "*$($ServiceSid):(OI)(CI)($ServiceRights)"
    )
    $childPattern = Join-Path $Path '*'
    if (Test-Path -LiteralPath $Path -PathType Container) {
        Invoke-IcaclsChecked -Arguments @(
            $childPattern,
            '/reset',
            '/T',
            '/C'
        )
    }
}

function Grant-TraverseDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$ServiceSid
    )
    Invoke-IcaclsChecked -Arguments @(
        $Path,
        '/grant:r',
        "*$($ServiceSid):(RX)"
    )
}

function Protect-File {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$ServiceSid,
        [Parameter(Mandatory = $true)][ValidateSet('RX','R')][string]$ServiceRights
    )
    Invoke-IcaclsChecked -Arguments @(
        $Path,
        '/inheritance:r',
        '/grant:r',
        '*S-1-5-18:(F)',
        '*S-1-5-32-544:(F)',
        "*$($ServiceSid):($ServiceRights)"
    )
}

Get-Service -Name $ServiceName -ErrorAction Stop | Out-Null
$serviceAccount = New-Object System.Security.Principal.NTAccount("NT SERVICE\$ServiceName")
$serviceSid = $serviceAccount.Translate(
    [System.Security.Principal.SecurityIdentifier]
).Value

$prefixPath = [System.IO.Path]::GetFullPath($Prefix)
$release = Join-Path (Join-Path $prefixPath 'releases') $ReleaseCommit
$pythonRoot = Join-Path $prefixPath 'python'
$logs = Join-Path $prefixPath 'logs'
$credentials = Join-Path $prefixPath 'credentials'
$shawl = (Resolve-Path -LiteralPath $ShawlPath).Path

foreach ($required in @($release, $pythonRoot, $logs, $credentials, $shawl)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "ACL target is missing: $required"
    }
}

Invoke-IcaclsChecked -Arguments @(
    $prefixPath,
    '/inheritance:r',
    '/grant:r',
    '*S-1-5-18:(OI)(CI)(F)',
    '*S-1-5-32-544:(OI)(CI)(F)',
    "*$($serviceSid):(RX)"
)

Grant-TraverseDirectory -Path (Join-Path $prefixPath 'releases') -ServiceSid $serviceSid
Grant-TraverseDirectory -Path (Join-Path $prefixPath 'toolchain') -ServiceSid $serviceSid
Grant-TraverseDirectory -Path (Join-Path $prefixPath 'toolchain\shawl') -ServiceSid $serviceSid
Grant-TraverseDirectory -Path (Split-Path -Parent $shawl) -ServiceSid $serviceSid
Protect-Directory -Path $release -ServiceSid $serviceSid -ServiceRights RX
Protect-Directory -Path $pythonRoot -ServiceSid $serviceSid -ServiceRights RX
Protect-Directory -Path $logs -ServiceSid $serviceSid -ServiceRights M
Protect-Directory -Path $credentials -ServiceSid $serviceSid -ServiceRights R
Protect-File -Path $shawl -ServiceSid $serviceSid -ServiceRights RX

$gatewayExe = Join-Path $release '.venv\Scripts\ordivon-gateway.exe'
$basePython = Join-Path $pythonRoot 'cpython-3.14-windows-x86_64-none\python.exe'
foreach ($probe in @($gatewayExe, $basePython, $shawl)) {
    if (-not (Test-Path -LiteralPath $probe -PathType Leaf)) {
        throw "ACL read-back probe missing: $probe"
    }
}

$receipt = [ordered]@{
    schemaVersion = 1
    kind = 'ordivon.gateway-windows-acl-materialization'
    serviceName = $ServiceName
    serviceSid = $serviceSid
    prefix = $prefixPath
    release = $release
    pythonRoot = $pythonRoot
    logs = $logs
    credentials = $credentials
    shawl = $shawl
}
$receiptPath = Join-Path (Join-Path $prefixPath 'receipts') "$ServiceName.acl.json"
$receipt | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $receiptPath -Encoding utf8
$receipt | ConvertTo-Json -Depth 4
