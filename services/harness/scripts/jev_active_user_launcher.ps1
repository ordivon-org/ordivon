[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PythonExe,
    [Parameter(Mandatory = $true)][string]$AdapterPath,
    [Parameter(Mandatory = $true)][string]$RequestFile,
    [Parameter(Mandatory = $true)][string]$ChromePath,
    [Parameter(Mandatory = $true)][string]$ChromeProfile,
    [Parameter(Mandatory = $true)][string]$CdpPort,
    [Parameter(Mandatory = $true)][string]$TypesafeDpapiFile,
    [string]$TextModelDpapiFile = ''
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
    throw 'Jev Python executable is unavailable.'
}
if (-not (Test-Path -LiteralPath $AdapterPath -PathType Leaf)) {
    throw 'Harness route adapter is unavailable.'
}
if (-not (Test-Path -LiteralPath $RequestFile -PathType Leaf)) {
    throw 'Harness route request is unavailable.'
}
if (-not (Test-Path -LiteralPath $ChromePath -PathType Leaf)) {
    throw 'Jev Chrome executable is unavailable.'
}
if (-not (Test-Path -LiteralPath $TypesafeDpapiFile -PathType Leaf)) {
    throw 'Jev TypeSafe DPAPI credential is unavailable.'
}
if ($TextModelDpapiFile -and -not (Test-Path -LiteralPath $TextModelDpapiFile -PathType Leaf)) {
    throw 'Jev text-model DPAPI credential is unavailable.'
}

$env:PYTHONUTF8 = '1'
$env:ORDIVON_JEV_CHROME_PATH = $ChromePath
$env:ORDIVON_JEV_CHROME_PROFILE = $ChromeProfile
$env:ORDIVON_JEV_CDP_PORT = $CdpPort
$env:ORDIVON_JEV_TYPESAFE_DPAPI_FILE = $TypesafeDpapiFile
if ($TextModelDpapiFile) {
    $env:ORDIVON_JEV_TEXT_MODEL_DPAPI_FILE = $TextModelDpapiFile
} else {
    Remove-Item Env:ORDIVON_JEV_TEXT_MODEL_DPAPI_FILE -ErrorAction SilentlyContinue
}

& $PythonExe $AdapterPath 'run' '--request-file' $RequestFile
exit $LASTEXITCODE
