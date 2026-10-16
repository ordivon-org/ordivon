[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$CarrierId,
    [string]$ContractPath = (Join-Path $PSScriptRoot 'native-tool-carriers.json'),
    [Parameter(Mandatory = $true)][string]$RuntimeRoot,
    [string]$ArchivePath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:MaterializerSha256 = 'sha256:' + (Get-FileHash -Algorithm SHA256 -LiteralPath $PSCommandPath).Hash.ToLowerInvariant()
$script:ContractSha256 = $null

function Get-ExactDigest {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Expected,
        [Parameter(Mandatory = $true)][string]$Label
    )
    if ($Expected -notmatch '^(sha256|sha512):([0-9a-f]+)$') {
        throw "$Label expected digest is malformed"
    }
    $algorithm = $Matches[1].ToUpperInvariant()
    $expectedHex = $Matches[2]
    $requiredLength = if ($algorithm -eq 'SHA256') { 64 } else { 128 }
    if ($expectedHex.Length -ne $requiredLength) {
        throw "$Label expected digest has wrong length"
    }
    $observedHex = (Get-FileHash -Algorithm $algorithm -LiteralPath $Path).Hash.ToLowerInvariant()
    if ($observedHex -ne $expectedHex) {
        throw "$Label digest mismatch: expected $expectedHex, observed $observedHex"
    }
    return "$($algorithm.ToLowerInvariant()):$observedHex"
}

function Assert-SafeRelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$Value,
        [Parameter(Mandatory = $true)][string]$Label
    )
    if (
        [IO.Path]::IsPathRooted($Value) -or
        $Value.Contains(':') -or
        $Value -match '(^|[\\/])\.\.([\\/]|$)'
    ) {
        throw "$Label is not a safe relative path"
    }
}

function Emit-Receipt {
    param(
        [Parameter(Mandatory = $true)]$Carrier,
        [Parameter(Mandatory = $true)][string]$Target,
        [Parameter(Mandatory = $true)][string]$Disposition,
        [Parameter(Mandatory = $true)][bool]$Downloaded
    )
    [ordered]@{
        schemaVersion = 1
        kind = 'ordivon.workstation.windows-native-tool-carrier-materialization'
        carrierId = $CarrierId
        sourceUrl = [string]$Carrier.sourceUrl
        archiveDigest = [string]$Carrier.archiveDigest
        archiveVerified = ($Disposition -eq 'materialized')
        executableSha256 = [string]$Carrier.executableSha256
        materializerSha256 = $script:MaterializerSha256
        contractSha256 = $script:ContractSha256
        target = $Target
        disposition = $Disposition
        downloaded = $Downloaded
        runtimeExecutionAdmitted = $false
        taskAuthorized = $false
        domainSuccess = $false
    } | ConvertTo-Json -Compress
}

try {
    if (-not (Test-Path -LiteralPath $ContractPath -PathType Leaf)) {
        throw 'native tool carrier contract is unavailable'
    }
    $script:ContractSha256 = 'sha256:' + (Get-FileHash -Algorithm SHA256 -LiteralPath $ContractPath).Hash.ToLowerInvariant()
    if (-not (Test-Path -LiteralPath $RuntimeRoot -PathType Container)) {
        throw 'RuntimeRoot must be an existing directory'
    }

    $contract = Get-Content -Raw -LiteralPath $ContractPath | ConvertFrom-Json
    if ($contract.schemaVersion -ne 1 -or $contract.kind -ne 'ordivon.workstation.windows-native-tool-carriers') {
        throw 'native tool carrier contract identity is invalid'
    }
    $carrier = $contract.carriers.PSObject.Properties[$CarrierId].Value
    if ($null -eq $carrier) {
        throw "unknown native tool carrier: $CarrierId"
    }

    $targetRelative = [string]$carrier.targetRelativePath
    Assert-SafeRelativePath -Value $targetRelative -Label 'targetRelativePath'
    if (-not $targetRelative.StartsWith('native-tools\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'targetRelativePath must stay under native-tools'
    }

    $archiveMember = [string]$carrier.archiveMember
    Assert-SafeRelativePath -Value $archiveMember -Label 'archiveMember'

    $runtimeFull = [IO.Path]::GetFullPath($RuntimeRoot).TrimEnd('\') + '\'
    $targetFull = [IO.Path]::GetFullPath((Join-Path $RuntimeRoot $targetRelative))
    if (-not $targetFull.StartsWith($runtimeFull, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'targetRelativePath must stay under RuntimeRoot'
    }

    if (Test-Path -LiteralPath $targetFull) {
        if (-not (Test-Path -LiteralPath $targetFull -PathType Leaf)) {
            throw 'existing target is not a regular file'
        }
        try {
            [void](Get-ExactDigest -Path $targetFull -Expected ([string]$carrier.executableSha256) -Label 'existing target')
        } catch {
            throw "existing target digest mismatch: $($_.Exception.Message)"
        }
        Emit-Receipt -Carrier $carrier -Target $targetFull -Disposition 'unchanged' -Downloaded $false
        exit 0
    }

    $stagingBase = Join-Path $RuntimeRoot 'store\staging\native-tool-carriers'
    New-Item -ItemType Directory -Path $stagingBase -Force | Out-Null
    $stage = Join-Path $stagingBase ($CarrierId + '-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $stage | Out-Null
    $downloaded = $false

    try {
        if ($ArchivePath) {
            if (-not (Test-Path -LiteralPath $ArchivePath -PathType Leaf)) {
                throw 'ArchivePath does not name a regular file'
            }
            $archive = [IO.Path]::GetFullPath($ArchivePath)
        } else {
            Add-Type -AssemblyName System.Net.Http
            $archive = Join-Path $stage 'source.archive'
            $client = [System.Net.Http.HttpClient]::new()
            try {
                $client.Timeout = [TimeSpan]::FromSeconds(120)
                $client.DefaultRequestHeaders.UserAgent.ParseAdd('Ordivon-Workstation-NativeToolCarrier/1')
                $response = $client.GetAsync(
                    [string]$carrier.sourceUrl,
                    [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead
                ).GetAwaiter().GetResult()
                try {
                    [void]$response.EnsureSuccessStatusCode()
                    $input = $response.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
                    try {
                        $output = [IO.File]::Open(
                            $archive,
                            [IO.FileMode]::CreateNew,
                            [IO.FileAccess]::Write,
                            [IO.FileShare]::None
                        )
                        try { $input.CopyTo($output) }
                        finally { $output.Dispose() }
                    } finally { $input.Dispose() }
                } finally { $response.Dispose() }
            } finally { $client.Dispose() }
            $downloaded = $true
        }

        try {
            [void](Get-ExactDigest -Path $archive -Expected ([string]$carrier.archiveDigest) -Label 'archive')
        } catch {
            throw "archive digest mismatch: $($_.Exception.Message)"
        }

        $tar = Join-Path $env:SystemRoot 'System32\tar.exe'
        if (-not (Test-Path -LiteralPath $tar -PathType Leaf)) {
            throw 'Windows tar.exe is unavailable'
        }

        $memberList = @(& $tar -tf $archive)
        if ($LASTEXITCODE -ne 0) {
            throw "cannot list native tool archive: tar exit $LASTEXITCODE"
        }
        $normalizedMember = $archiveMember.Replace('\', '/')
        $memberCount = 0
        foreach ($entry in $memberList) {
            $name = ([string]$entry).Trim()
            if (-not $name) { continue }
            Assert-SafeRelativePath -Value $name -Label 'archive entry'
            if ($name.Replace('\', '/') -eq $normalizedMember) {
                $memberCount += 1
            }
        }
        if ($memberCount -ne 1) {
            throw "archive must contain the exact member once: $archiveMember"
        }

        $extractRoot = Join-Path $stage 'extract'
        New-Item -ItemType Directory -Path $extractRoot | Out-Null
        & $tar -xf $archive -C $extractRoot
        if ($LASTEXITCODE -ne 0) {
            throw "cannot extract native tool archive: tar exit $LASTEXITCODE"
        }

        $memberPath = Join-Path $extractRoot ($archiveMember.Replace('/', '\'))
        if (-not (Test-Path -LiteralPath $memberPath -PathType Leaf)) {
            throw 'archive extraction omitted exact executable member'
        }
        $memberItem = Get-Item -LiteralPath $memberPath -Force
        if (($memberItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'archive executable member must not be a reparse point'
        }
        try {
            [void](Get-ExactDigest -Path $memberPath -Expected ([string]$carrier.executableSha256) -Label 'executable')
        } catch {
            throw "executable digest mismatch: $($_.Exception.Message)"
        }

        $targetParent = Split-Path -Parent $targetFull
        New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
        if (Test-Path -LiteralPath $targetFull) {
            throw 'target appeared during native tool materialization'
        }
        [IO.File]::Move($memberPath, $targetFull)

        try {
            [void](Get-ExactDigest -Path $targetFull -Expected ([string]$carrier.executableSha256) -Label 'installed executable')
        } catch {
            Remove-Item -LiteralPath $targetFull -Force -ErrorAction SilentlyContinue
            throw
        }

        Emit-Receipt -Carrier $carrier -Target $targetFull -Disposition 'materialized' -Downloaded $downloaded
    } finally {
        if (Test-Path -LiteralPath $stage) {
            Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
} catch {
    $failure = [ordered]@{
        schemaVersion = 1
        kind = 'ordivon.workstation.windows-native-tool-carrier-materialization'
        carrierId = $CarrierId
        standing = 'FAILED'
        error = $_.Exception.Message
        materializerSha256 = $script:MaterializerSha256
        contractSha256 = $script:ContractSha256
        runtimeExecutionAdmitted = $false
        taskAuthorized = $false
        domainSuccess = $false
    } | ConvertTo-Json -Compress
    [Console]::Error.WriteLine($failure)
    exit 2
}
