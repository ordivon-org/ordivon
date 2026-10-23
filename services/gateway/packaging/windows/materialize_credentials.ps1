[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Prefix,
    [Parameter()]
    [ValidatePattern('^[A-Za-z0-9._-]{1,128}$')]
    [string]$ServiceName = 'OrdivonGatewayCandidateR1',
    [Parameter()]
    [string]$LinuxRuntimeBearerSource = '',
    [Parameter()]
    [string]$WindowsRuntimeBearerSource = '',
    [Parameter()]
    [string]$HostBearerSource = '',
    [Parameter()]
    [switch]$CreateLocalServiceBearer,
    [Parameter()]
    [switch]$ReplaceExisting
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

function Get-Sha256Lower {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Protect-CredentialFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$ServiceSid
    )
    Invoke-IcaclsChecked -Arguments @(
        $Path,
        '/inheritance:r',
        '/grant:r',
        '*S-1-5-18:(F)',
        '*S-1-5-32-544:(F)',
        "*$($ServiceSid):(R)"
    )

    $acl = Get-Acl -LiteralPath $Path
    if (-not $acl.AreAccessRulesProtected) {
        throw "credential DACL is not protected: $Path"
    }
    $actualSids = @(
        $acl.Access | ForEach-Object {
            if ($_.IsInherited) {
                throw "credential contains inherited ACE: $Path"
            }
            $_.IdentityReference.Translate(
                [System.Security.Principal.SecurityIdentifier]
            ).Value
        } | Sort-Object -Unique
    )
    $expectedSids = @(
        'S-1-5-18',
        'S-1-5-32-544',
        $ServiceSid
    ) | Sort-Object -Unique
    if (Compare-Object -ReferenceObject $expectedSids -DifferenceObject $actualSids) {
        throw "credential ACL principal set mismatch: $Path"
    }
}

$service = Get-Service -Name $ServiceName -ErrorAction Stop
if ($service.Status -ne 'Stopped') {
    throw "Gateway candidate must be stopped while credentials are materialized"
}

$serviceAccount = New-Object System.Security.Principal.NTAccount("NT SERVICE\$ServiceName")
$serviceSid = $serviceAccount.Translate(
    [System.Security.Principal.SecurityIdentifier]
).Value

$prefixPath = [System.IO.Path]::GetFullPath($Prefix)
$credentials = Join-Path $prefixPath 'credentials'
$receipts = Join-Path $prefixPath 'receipts'
New-Item -ItemType Directory -Force -Path $credentials, $receipts | Out-Null

$specs = @(
    [ordered]@{
        label = 'linux-runtime-bearer'
        source = $LinuxRuntimeBearerSource
        destination = 'linux-runtime-bearer'
    },
    [ordered]@{
        label = 'windows-runtime-bearer'
        source = $WindowsRuntimeBearerSource
        destination = 'windows-runtime-bearer'
    },
    [ordered]@{
        label = 'host-bearer'
        source = $HostBearerSource
        destination = 'host-bearer'
    },
    [ordered]@{
        label = 'local-service-bearer'
        source = ''
        destination = 'local-service-bearer'
    }
)

$materialized = @()
foreach ($spec in $specs) {
    $generate = $CreateLocalServiceBearer -and $spec.label -eq 'local-service-bearer'
    if ([string]::IsNullOrWhiteSpace($spec.source) -and -not $generate) {
        continue
    }

    $source = $null
    if (-not $generate) {
        $source = (Resolve-Path -LiteralPath $spec.source).Path
        $sourceItem = Get-Item -LiteralPath $source -Force
        if ($sourceItem.PSIsContainer -or ($sourceItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "$($spec.label) source must be a non-reparse regular file"
        }
    }

    $destination = Join-Path $credentials $spec.destination
    if ((Test-Path -LiteralPath $destination) -and -not $ReplaceExisting) {
        throw "credential already exists: $destination"
    }

    $tmp = Join-Path $credentials (".$($spec.destination).tmp-" + [guid]::NewGuid().ToString('N'))
    $bytes = $null
    $generatedDigest = $null
    try {
        New-Item -ItemType File -Path $tmp | Out-Null
        Protect-CredentialFile -Path $tmp -ServiceSid $serviceSid
        try {
            if ($generate) {
                $random = New-Object byte[] 32
                $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
                $sha = [Security.Cryptography.SHA256]::Create()
                try {
                    $rng.GetBytes($random)
                    $value = ([BitConverter]::ToString($random)).Replace('-', '').ToLowerInvariant()
                    $bytes = [Text.Encoding]::ASCII.GetBytes($value)
                    $value = $null
                    $generatedDigest = ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
                }
                finally {
                    $rng.Dispose()
                    $sha.Dispose()
                    [Array]::Clear($random, 0, $random.Length)
                }
            }
            else {
                $bytes = [IO.File]::ReadAllBytes($source)
            }
            [IO.File]::WriteAllBytes($tmp, $bytes)
        }
        finally {
            if ($null -ne $bytes) {
                [Array]::Clear($bytes, 0, $bytes.Length)
                $bytes = $null
            }
        }

        Protect-CredentialFile -Path $tmp -ServiceSid $serviceSid
        $sourceDigest = if ($generate) { $generatedDigest } else { Get-Sha256Lower -Path $source }
        $targetDigest = Get-Sha256Lower -Path $tmp
        if ($sourceDigest -ne $targetDigest) {
            throw "$($spec.label) digest mismatch after copy"
        }

        if (Test-Path -LiteralPath $destination) {
            Remove-Item -LiteralPath $destination -Force
        }
        Move-Item -LiteralPath $tmp -Destination $destination
        Protect-CredentialFile -Path $destination -ServiceSid $serviceSid

        $finalItem = Get-Item -LiteralPath $destination
        $finalDigest = Get-Sha256Lower -Path $destination
        if ($finalDigest -ne $sourceDigest) {
            throw "$($spec.label) digest mismatch after finalization"
        }

        $materialized += [ordered]@{
            label = $spec.label
            destination = $destination
            bytes = $finalItem.Length
            sha256 = $finalDigest
            daclProtected = (Get-Acl -LiteralPath $destination).AreAccessRulesProtected
        }
    }
    finally {
        if ($null -ne $bytes) {
            [Array]::Clear($bytes, 0, $bytes.Length)
        }
        Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
    }
}

if ($materialized.Count -eq 0) {
    throw 'at least one credential source is required'
}

$receipt = [ordered]@{
    schemaVersion = 1
    kind = 'ordivon.gateway-windows-credential-materialization'
    serviceName = $ServiceName
    serviceSid = $serviceSid
    credentials = $materialized
}
$receiptPath = Join-Path $receipts "$ServiceName.credentials.json"
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding utf8
$receipt | ConvertTo-Json -Depth 6
