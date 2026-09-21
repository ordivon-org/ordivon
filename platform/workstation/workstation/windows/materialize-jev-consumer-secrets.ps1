[CmdletBinding()]
param(
    [string]$TargetRoot = (Join-Path $env:LOCALAPPDATA 'Ordivon\Secrets\jev-fastpath-v1')
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Security
$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) {
    throw 'Expected one JSON object on stdin.'
}
$value = $raw | ConvertFrom-Json
$typesafe = [string]$value.TYPESAFE_API_KEY
$textModel = [string]$value.TEXT_MODEL_API_KEY
if ([string]::IsNullOrWhiteSpace($typesafe)) {
    throw 'TYPESAFE_API_KEY is required.'
}

New-Item -ItemType Directory -Path $TargetRoot -Force | Out-Null
$current = [Security.Principal.WindowsIdentity]::GetCurrent()
$user = $current.User

function Write-DpapiSecret([string]$Path, [string]$Plaintext) {
    $plainBytes = [Text.Encoding]::UTF8.GetBytes($Plaintext)
    try {
        $protected = [Security.Cryptography.ProtectedData]::Protect(
            $plainBytes, $null,
            [Security.Cryptography.DataProtectionScope]::CurrentUser
        )
        try { [IO.File]::WriteAllBytes($Path, $protected) }
        finally { [Array]::Clear($protected, 0, $protected.Length) }
    }
    finally { [Array]::Clear($plainBytes, 0, $plainBytes.Length) }
}

$typesafePath = Join-Path $TargetRoot 'typesafe-api-key.dpapi'
$textPath = Join-Path $TargetRoot 'text-model-api-key.dpapi'
Write-DpapiSecret $typesafePath $typesafe
if (-not [string]::IsNullOrWhiteSpace($textModel)) {
    Write-DpapiSecret $textPath $textModel
} elseif (Test-Path -LiteralPath $textPath) {
    Remove-Item -LiteralPath $textPath -Force
}

$typesafe = $null
$textModel = $null
$raw = $null

[ordered]@{
    schemaVersion = 1
    kind = 'ordivon.workstation.windows-jev-consumer-secrets'
    materialized = $true
    protection = 'windows-dpapi-current-user'
    ownerSid = $user.Value
    targetRoot = $TargetRoot
    typesafePresent = (Test-Path -LiteralPath $typesafePath)
    textModelPresent = (Test-Path -LiteralPath $textPath)
    secretContentReturned = $false
    secretDigestReturned = $false
} | ConvertTo-Json -Compress
