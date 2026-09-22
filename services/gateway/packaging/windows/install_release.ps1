[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Repo,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-f]{40}$')]
    [string]$Commit,

    [Parameter(Mandatory = $true)]
    [string]$Prefix,

    [Parameter(Mandatory = $true)]
    [string]$UvPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter()][string[]]$ArgumentList = @()
    )
    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "command failed with exit code ${LASTEXITCODE}: $FilePath $($ArgumentList -join ' ')"
    }
}

function Get-Sha256Lower {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

$git = (Get-Command git.exe -ErrorAction Stop).Source
$tar = (Get-Command tar.exe -ErrorAction Stop).Source

$repoPath = (Resolve-Path -LiteralPath $Repo).Path
$uvResolved = (Resolve-Path -LiteralPath $UvPath).Path
$prefixPath = [System.IO.Path]::GetFullPath($Prefix)

$resolvedOutput = @(
    & $git '-c' "safe.directory=$repoPath" '-C' $repoPath 'rev-parse' '--verify' "$Commit^{commit}" 2>&1
)
$resolveExitCode = $LASTEXITCODE
if ($resolveExitCode -ne 0) {
    throw "commit resolution failed with exit code $resolveExitCode: $($resolvedOutput | Out-String)"
}
$resolved = ($resolvedOutput | Out-String).Trim()
if ($resolved -ne $Commit) {
    throw "commit must resolve exactly to the requested full Git SHA"
}

$releases = Join-Path $prefixPath 'releases'
$pythonRoot = Join-Path $prefixPath 'python'
$receipts = Join-Path $prefixPath 'receipts'
New-Item -ItemType Directory -Force -Path $releases, $pythonRoot, $receipts | Out-Null

$release = Join-Path $releases $Commit
$created = $false

if (-not (Test-Path -LiteralPath $release -PathType Container)) {
    $nonce = [guid]::NewGuid().ToString('N')
    $tmp = Join-Path $releases ".tmp-$Commit-$nonce"
    $archive = Join-Path $releases ".archive-$Commit-$nonce.tar"

    New-Item -ItemType Directory -Path $tmp | Out-Null
    try {
        Invoke-Checked -FilePath $git -ArgumentList @(
            '-c', "safe.directory=$repoPath",
            '-C', $repoPath,
            'archive',
            '--format=tar',
            '-o', $archive,
            $Commit,
            'services/gateway'
        )
        Invoke-Checked -FilePath $tar -ArgumentList @(
            '-xf', $archive,
            '--strip-components=2',
            '-C', $tmp
        )
        if (Test-Path -LiteralPath $release) {
            throw "release path appeared concurrently: $release"
        }
        Move-Item -LiteralPath $tmp -Destination $release
        $created = $true
    }
    finally {
        Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $archive -Force -ErrorAction SilentlyContinue
    }
}

$pythonVersionFile = Join-Path $release '.python-version'
$projectFile = Join-Path $release 'pyproject.toml'
$lockFile = Join-Path $release 'uv.lock'

foreach ($required in @($pythonVersionFile, $projectFile, $lockFile)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "release is missing required file: $required"
    }
}

$pythonRequest = (Get-Content -LiteralPath $pythonVersionFile -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($pythonRequest)) {
    throw '.python-version must contain one Python request'
}

$projectText = Get-Content -LiteralPath $projectFile -Raw
$requiredPython = [regex]::Match($projectText, '(?m)^requires-python\s*=\s*"==([^"]+)"\s*$')
if (-not $requiredPython.Success -or $requiredPython.Groups[1].Value -ne $pythonRequest) {
    throw "pyproject requires-python must exactly match .python-version"
}
$packageVersionMatch = [regex]::Match($projectText, '(?m)^version\s*=\s*"([^"]+)"\s*$')
if (-not $packageVersionMatch.Success) {
    throw "pyproject version is missing"
}

$previousPythonInstall = $env:UV_PYTHON_INSTALL_DIR
try {
    $env:UV_PYTHON_INSTALL_DIR = $pythonRoot

    Invoke-Checked -FilePath $uvResolved -ArgumentList @(
        'python', 'install',
        '--install-dir', $pythonRoot,
        '--no-bin',
        $pythonRequest
    )

    $python = (& $uvResolved 'python' 'find' '--no-project' '--managed-python' $pythonRequest).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($python)) {
        throw "uv did not resolve managed Python $pythonRequest"
    }

    Invoke-Checked -FilePath $uvResolved -ArgumentList @(
        'sync',
        '--frozen',
        '--no-dev',
        '--python', $python,
        '--project', $release
    )
}
finally {
    if ($null -eq $previousPythonInstall) {
        Remove-Item Env:UV_PYTHON_INSTALL_DIR -ErrorAction SilentlyContinue
    }
    else {
        $env:UV_PYTHON_INSTALL_DIR = $previousPythonInstall
    }
}

$venvPython = Join-Path $release '.venv\Scripts\python.exe'
$gatewayExe = Join-Path $release '.venv\Scripts\ordivon-gateway.exe'
foreach ($required in @($venvPython, $gatewayExe)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "materialized release is missing executable: $required"
    }
}

$actualPythonVersion = (& $venvPython '--version' 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $actualPythonVersion -ne "Python $pythonRequest") {
    throw "release-local Python version mismatch: $actualPythonVersion"
}

$receipt = [ordered]@{
    schemaVersion = 1
    kind = 'ordivon.gateway-windows-release-receipt'
    sourceCommit = $Commit
    packageVersion = $packageVersionMatch.Groups[1].Value
    pythonRequest = $pythonRequest
    pythonVersion = $actualPythonVersion
    uvPath = $uvResolved
    uvSha256 = Get-Sha256Lower -Path $uvResolved
    lockSha256 = Get-Sha256Lower -Path $lockFile
    pyprojectSha256 = Get-Sha256Lower -Path $projectFile
    releasePath = $release
    gatewayExecutable = $gatewayExe
    releaseCreated = $created
}
$receiptPath = Join-Path $receipts "$Commit.json"
$receipt | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $receiptPath -Encoding utf8

$receipt | ConvertTo-Json -Depth 4
