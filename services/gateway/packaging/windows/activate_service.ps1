[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Prefix,
    [Parameter()]
    [ValidatePattern('^[A-Za-z0-9._-]{1,128}$')]
    [string]$ServiceName = 'OrdivonGatewayCandidateR1',
    [Parameter()]
    [ValidateSet('Manual', 'Automatic')]
    [string]$StartMode = 'Automatic'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-ScChecked {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    $output = & "$env:SystemRoot\System32\sc.exe" @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "sc.exe failed with exit code $($LASTEXITCODE): $($Arguments -join ' ') | $($output | Out-String)"
    }
}

function Assert-CredentialProjection {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][object]$CredentialReceipt,
        [Parameter(Mandatory = $true)][string]$ServiceSid
    )

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        throw "configured credential is absent: $Label"
    }
    $item = Get-Item -LiteralPath $fullPath -Force
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $item.Length -le 0) {
        throw "configured credential is not a non-empty regular file: $Label"
    }

    $matches = @($CredentialReceipt.credentials | Where-Object { $_.label -eq $Label })
    if ($matches.Count -ne 1) {
        throw "credential materialization receipt does not contain exactly one $Label entry"
    }
    $entry = $matches[0]
    if ([System.IO.Path]::GetFullPath([string]$entry.destination) -ne $fullPath) {
        throw "credential materialization destination mismatch: $Label"
    }
    if ([int64]$entry.bytes -ne $item.Length -or -not [bool]$entry.daclProtected) {
        throw "credential materialization metadata mismatch: $Label"
    }
    $actualDigest = (Get-FileHash -LiteralPath $fullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualDigest -ne ([string]$entry.sha256).ToLowerInvariant()) {
        throw "credential bytes no longer match materialization receipt: $Label"
    }

    $acl = Get-Acl -LiteralPath $fullPath
    if (-not $acl.AreAccessRulesProtected) {
        throw "credential DACL is not protected: $Label"
    }
    $actualSids = @(
        $acl.Access | ForEach-Object {
            if ($_.IsInherited) {
                throw "credential contains inherited ACE: $Label"
            }
            $_.IdentityReference.Translate(
                [System.Security.Principal.SecurityIdentifier]
            ).Value
        } | Sort-Object -Unique
    )
    $expectedSids = @('S-1-5-18', 'S-1-5-32-544', $ServiceSid) | Sort-Object -Unique
    if (Compare-Object -ReferenceObject $expectedSids -DifferenceObject $actualSids) {
        throw "credential ACL principal set mismatch: $Label"
    }

    return [ordered]@{
        label = $Label
        path = $fullPath
        bytes = $item.Length
        daclProtected = $true
    }
}

$prefixPath = [System.IO.Path]::GetFullPath($Prefix)
$receipts = Join-Path $prefixPath 'receipts'
$serviceReceiptPath = Join-Path $receipts "$ServiceName.materialization.json"
$credentialReceiptPath = Join-Path $receipts "$ServiceName.credentials.json"
if (-not (Test-Path -LiteralPath $serviceReceiptPath -PathType Leaf)) {
    throw "Gateway service materialization receipt is missing"
}

$serviceReceipt = Get-Content -LiteralPath $serviceReceiptPath -Raw | ConvertFrom-Json
if ($serviceReceipt.kind -ne 'ordivon.gateway-windows-service-materialization' -or $serviceReceipt.serviceName -ne $ServiceName) {
    throw "Gateway service materialization receipt identity mismatch"
}
foreach ($field in @('linuxRuntimeUrl', 'windowsRuntimeUrl', 'linuxBearerTokenFile', 'windowsBearerTokenFile', 'hostBearerTokenFile', 'activationRequired')) {
    if ($serviceReceipt.PSObject.Properties.Name -notcontains $field) {
        throw "Gateway service materialization receipt predates activation contract: $field"
    }
}
if (-not [bool]$serviceReceipt.activationRequired) {
    throw "Gateway service materialization receipt does not require activation"
}
if (-not [string]::IsNullOrWhiteSpace([string]$serviceReceipt.linuxRuntimeUrl) -and [string]::IsNullOrWhiteSpace([string]$serviceReceipt.linuxBearerTokenFile)) {
    throw "Linux Runtime activation requires a bearer token path"
}
if (-not [string]::IsNullOrWhiteSpace([string]$serviceReceipt.windowsRuntimeUrl) -and [string]::IsNullOrWhiteSpace([string]$serviceReceipt.windowsBearerTokenFile)) {
    throw "Windows Runtime activation requires a bearer token path"
}

$service = Get-Service -Name $ServiceName -ErrorAction Stop
if ($service.Status -ne 'Stopped') {
    throw "Gateway candidate must be stopped before activation"
}
$serviceAccount = New-Object System.Security.Principal.NTAccount("NT SERVICE\$ServiceName")
$serviceSid = $serviceAccount.Translate([System.Security.Principal.SecurityIdentifier]).Value

$required = @(
    [ordered]@{ label = 'linux-runtime-bearer'; path = [string]$serviceReceipt.linuxBearerTokenFile },
    [ordered]@{ label = 'windows-runtime-bearer'; path = [string]$serviceReceipt.windowsBearerTokenFile },
    [ordered]@{ label = 'host-bearer'; path = [string]$serviceReceipt.hostBearerTokenFile }
)
$configured = @($required | Where-Object { -not [string]::IsNullOrWhiteSpace($_.path) })
$credentialReceipt = $null
if ($configured.Count -gt 0) {
    if (-not (Test-Path -LiteralPath $credentialReceiptPath -PathType Leaf)) {
        throw "Gateway credential materialization receipt is missing"
    }
    $credentialReceipt = Get-Content -LiteralPath $credentialReceiptPath -Raw | ConvertFrom-Json
    if ($credentialReceipt.kind -ne 'ordivon.gateway-windows-credential-materialization' -or $credentialReceipt.serviceName -ne $ServiceName) {
        throw "Gateway credential materialization receipt identity mismatch"
    }
}

$verifiedCredentials = @()
foreach ($spec in $configured) {
    $verifiedCredentials += Assert-CredentialProjection `
        -Label $spec.label `
        -Path $spec.path `
        -CredentialReceipt $credentialReceipt `
        -ServiceSid $serviceSid
}

$scStartMode = if ($StartMode -eq 'Automatic') { 'auto' } else { 'demand' }
$expectedCimStartMode = if ($StartMode -eq 'Automatic') { 'Auto' } else { 'Manual' }
Invoke-ScChecked -Arguments @('config', $ServiceName, 'start=', $scStartMode)
Start-Service -Name $ServiceName
$service.WaitForStatus('Running', [TimeSpan]::FromSeconds(30))

$current = Get-CimInstance Win32_Service -Filter "Name='$ServiceName'"
if (-not $current -or $current.State -ne 'Running' -or $current.StartMode -ne $expectedCimStartMode) {
    throw "Gateway activation did not converge to requested lifecycle state"
}

$receipt = [ordered]@{
    schemaVersion = 1
    kind = 'ordivon.gateway-windows-service-activation'
    serviceName = $ServiceName
    serviceSid = $serviceSid
    startMode = $current.StartMode
    state = $current.State
    sourceCommit = $serviceReceipt.sourceCommit
    releasePath = $serviceReceipt.releasePath
    credentialPreflight = 'pass'
    verifiedCredentials = $verifiedCredentials
}
$receiptPath = Join-Path $receipts "$ServiceName.activation.json"
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding utf8
$receipt | ConvertTo-Json -Depth 6
