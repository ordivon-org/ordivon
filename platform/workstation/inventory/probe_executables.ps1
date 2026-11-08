# Read-only current-process Windows command lookup; not an installation or authority verdict.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidateCount(1,128)][string[]] $Names)
$ErrorActionPreference = 'Stop'
$items = foreach ($name in $Names) {
    if ($name -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$') { throw "Invalid executable name: $name" }
    $command = Get-Command -Name $name -CommandType Application,ExternalScript -ErrorAction SilentlyContinue | Select-Object -First 1
    [ordered]@{
        name = $name
        resolution = if ($null -eq $command) { 'not_on_path' } else { 'on_path' }
        executablePath = if ($null -eq $command) { $null } else { $command.Source }
    }
}
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$path = [string]$env:PATH
$sha = [System.Security.Cryptography.SHA256]::Create()
try {
    $bytes = $sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($path))
    $digest = ([BitConverter]::ToString($bytes)).Replace('-','').ToLowerInvariant()
} finally { $sha.Dispose() }
[ordered]@{
    kind = 'ordivon.workstation.executable-path-observation'
    schemaVersion = 1
    observedAt = [DateTimeOffset]::UtcNow.ToString('o')
    node = [Environment]::MachineName
    platform = 'Windows'
    executionPrincipal = $identity
    pathSha256 = $digest
    verificationBoundary = 'PATH_resolution_only_not_installed_or_authorized_or_executable_success'
    commands = @($items)
} | ConvertTo-Json -Depth 5 -Compress