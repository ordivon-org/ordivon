#requires -version 5.1
# Side-effect-free validator for the manifest emitted by prepare_windows_pg_release.py.
Set-StrictMode -Version Latest

function Get-OrdivonWindowsPgReleaseProvenance {
    param(
        [Parameter(Mandatory=$true)][string]$ManifestPath,
        [Parameter(Mandatory=$true)][string]$ExpectedSourceCommit,
        [Parameter(Mandatory=$true)][string]$RuntimePath,
        [Parameter(Mandatory=$true)][string]$LauncherPath,
        [Parameter(Mandatory=$true)][string]$ExpectedRuntimeSha256,
        [Parameter(Mandatory=$true)][string]$ExpectedLauncherSha256
    )
    if ($ExpectedSourceCommit -cnotmatch '^[0-9a-f]{40}$') {
        throw 'Windows PG release source commit must be one exact lowercase Git SHA-1.'
    }
    foreach ($digest in @($ExpectedRuntimeSha256,$ExpectedLauncherSha256)) {
        if ($digest -notmatch '^[0-9A-Fa-f]{64}$') {
            throw 'Windows PG release file commitment must be SHA-256.'
        }
    }
    $resolved=(Resolve-Path -LiteralPath $ManifestPath -ErrorAction Stop).Path
    $item=Get-Item -LiteralPath $resolved -Force
    if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $item.Length -gt 1048576) {
        throw 'Windows PG release manifest must be one regular file of at most 1 MiB.'
    }
    $bytes=[IO.File]::ReadAllBytes($resolved)
    $sha=[Security.Cryptography.SHA256]::Create()
    try { $manifestSha=([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose() }
    try {
        $utf8=[Text.UTF8Encoding]::new($false,$true)
        $manifest=($utf8.GetString($bytes) | ConvertFrom-Json -ErrorAction Stop)
    } catch {
        throw ('Windows PG release manifest JSON is invalid: '+$_.Exception.Message)
    }
    if ($manifest.schemaVersion -ne 1 -or $manifest.kind -cne 'ordivon.windows-pg-release' -or
        $manifest.truthRole -cne 'builder-manifest-claim-bound-to-exact-bytes-not-reproducible-build-proof') {
        throw 'Windows PG release manifest version, kind, or truth role is invalid.'
    }
    if ($null -eq $manifest.source -or $manifest.source.commit -cne $ExpectedSourceCommit -or
        [string]$manifest.source.runtimeTree -cnotmatch '^[0-9a-f]{40,64}$' -or
        [string]$manifest.source.runtimeSourceArchiveSha256 -cnotmatch '^[0-9a-f]{64}$' -or
        [string]$manifest.source.cargoLockSha256 -cnotmatch '^[0-9a-f]{64}$') {
        throw 'Windows PG release manifest source provenance is invalid or differs from the selected commit.'
    }
    $files=@($manifest.files)
    function Get-ExactManifestFile([string]$Name) {
        $matches=@($files | Where-Object { [string]$_.path -ceq $Name })
        if ($matches.Count -ne 1) { throw ('Windows PG release manifest must contain exactly one '+$Name) }
        return $matches[0]
    }
    $runtime=Get-ExactManifestFile 'ordivon-runtime-pg.exe'
    $launcher=Get-ExactManifestFile 'ordivon-windows-pg-job-launcher.exe'
    foreach ($pair in @(
        @($runtime,$RuntimePath,$ExpectedRuntimeSha256,'runtime'),
        @($launcher,$LauncherPath,$ExpectedLauncherSha256,'launcher')
    )) {
        $entry=$pair[0];$path=[string]$pair[1];$expected=[string]$pair[2];$label=[string]$pair[3]
        if ([string]$entry.sha256 -notmatch '^[0-9a-f]{64}$' -or [string]$entry.sha256 -ine $expected) {
            throw ('Windows PG release manifest '+$label+' digest differs from the selected commitment.')
        }
        $actual=Get-Item -LiteralPath $path -Force
        if ($actual.PSIsContainer -or ($actual.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
            [int64]$entry.size -ne $actual.Length -or
            (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ine $expected) {
            throw ('Windows PG release manifest '+$label+' bytes differ from the selected commitment.')
        }
    }
    [pscustomobject]@{
        truthRole='builder-manifest-claim-bound-to-exact-bytes-not-reproducible-build-proof'
        sourceCommitClaim=[string]$manifest.source.commit
        runtimeTree=[string]$manifest.source.runtimeTree
        runtimeSourceArchiveSha256=[string]$manifest.source.runtimeSourceArchiveSha256
        cargoLockSha256=[string]$manifest.source.cargoLockSha256
        manifestSha256=$manifestSha
    }
}
