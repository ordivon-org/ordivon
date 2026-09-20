[CmdletBinding()]
param(
    [string]$SourceEnvPath = '\\wsl.localhost\archlinux\etc\cloudflared\canary.env',
    [string]$TargetPath = 'C:\ProgramData\Ordivon\Cloudflare\windows-runtime-canary.token'
)

$ErrorActionPreference = 'Stop'

$current = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($current)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Token materialization requires an elevated interactive Windows administrator.'
}

$lines = Get-Content -LiteralPath $SourceEnvPath -ErrorAction Stop
$matches = @($lines | Where-Object { $_ -match '^TUNNEL_TOKEN=' })
if ($matches.Count -ne 1) {
    throw "Expected exactly one TUNNEL_TOKEN entry in source material; observed $($matches.Count)."
}

$token = $matches[0].Substring('TUNNEL_TOKEN='.Length).Trim().Trim('"').Trim("'")
if ([string]::IsNullOrWhiteSpace($token)) {
    throw 'Tunnel token is empty.'
}

$target = [IO.Path]::GetFullPath($TargetPath)
$parent = Split-Path -Parent $target
New-Item -ItemType Directory -Path $parent -Force | Out-Null

$utf8NoBom = [Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText($target, $token, $utf8NoBom)
$token = $null

$system = [Security.Principal.NTAccount]::new('NT AUTHORITY', 'SYSTEM')
$admins = [Security.Principal.NTAccount]::new('BUILTIN', 'Administrators')
$acl = [Security.AccessControl.FileSecurity]::new()
$acl.SetAccessRuleProtection($true, $false)
$acl.SetOwner($admins)
$acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new(
    $system,
    [Security.AccessControl.FileSystemRights]::Read,
    [Security.AccessControl.AccessControlType]::Allow
))
$acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new(
    $admins,
    [Security.AccessControl.FileSystemRights]::FullControl,
    [Security.AccessControl.AccessControlType]::Allow
))
Set-Acl -LiteralPath $target -AclObject $acl

$actual = Get-Acl -LiteralPath $target
if (-not $actual.AreAccessRulesProtected) {
    throw 'Tunnel token ACL inheritance remains enabled.'
}
$identities = @($actual.Access | ForEach-Object { $_.IdentityReference.Value } | Sort-Object -Unique)
$expected = @('BUILTIN\Administrators', 'NT AUTHORITY\SYSTEM')
if (@(Compare-Object $expected $identities).Count -ne 0) {
    throw 'Tunnel token ACL identities do not match the required SYSTEM/Administrators boundary.'
}

[ordered]@{
    schemaVersion = 1
    kind = 'ordivon.workstation.windows-cloudflared-token-materialization'
    materialized = $true
    targetPath = $target
    secretContentReturned = $false
} | ConvertTo-Json -Compress
