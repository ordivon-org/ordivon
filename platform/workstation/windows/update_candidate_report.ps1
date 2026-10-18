[CmdletBinding()]
param(
    [string]$Output = "C:\ProgramData\Ordivon\UpdateDiscovery\current.json",
    [string]$WingetFixturePath = ""
)

$ErrorActionPreference = "Stop"

function Convert-WingetUpgradeOutput {
    param([string[]]$Lines)

    $rows = @()
    $separator = -1
    for ($i = 0; $i -lt $Lines.Count; $i++) {
        if ($Lines[$i] -match '^-{4,}') {
            $separator = $i
            break
        }
    }
    if ($separator -lt 0) {
        return @()
    }

    for ($i = $separator + 1; $i -lt $Lines.Count; $i++) {
        $line = $Lines[$i].Trim()
        if (-not $line) { continue }
        if ($line -match '^\d+\s+upgrades?\s+available\.$') { break }
        if ($line -match '^No installed package found') { break }

        # WinGet display names may overflow their visual column. Package IDs and
        # versions are single tokens, so parse those three fields from the right.
        if ($line -notmatch '^(?<name>.+)\s+(?<id>\S+)\s+(?<current>\S+)\s+(?<available>\S+)$') {
            continue
        }
        $rows += [ordered]@{
            name = $Matches.name.Trim()
            id = $Matches.id
            current = $Matches.current
            available = $Matches.available
        }
    }
    return @($rows)
}

function Get-WingetBinary {
    $package = Get-AppxPackage -AllUsers -Name Microsoft.DesktopAppInstaller -ErrorAction SilentlyContinue |
        Sort-Object Version -Descending |
        Select-Object -First 1
    if (-not $package) { return $null }

    $candidate = Join-Path $package.InstallLocation "winget.exe"
    if (Test-Path -LiteralPath $candidate) { return $candidate }
    return $null
}

function Get-WingetCandidates {
    if ($WingetFixturePath) {
        $lines = @(Get-Content -LiteralPath $WingetFixturePath)
        $fixtureItems = @(Convert-WingetUpgradeOutput -Lines $lines)
        return [ordered]@{
            state = if ($fixtureItems.Count) { "updates_available" } else { "current" }
            items = $fixtureItems
            source = "fixture"
        }
    }

    $winget = Get-WingetBinary
    if (-not $winget) {
        return [ordered]@{
            state = "missing"
            items = @()
            reason = "desktop_app_installer_or_winget_missing"
        }
    }

    $lines = @(& $winget upgrade --source winget --accept-source-agreements --disable-interactivity 2>&1 |
        ForEach-Object { "$_" })
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        return [ordered]@{
            state = "unknown"
            items = @()
            reason = "winget_upgrade_exit_nonzero"
            exitCode = $exitCode
        }
    }

    $items = @(Convert-WingetUpgradeOutput -Lines $lines)
    $joined = $lines -join [Environment]::NewLine
    if ($items.Count -gt 0) {
        return [ordered]@{
            state = "updates_available"
            items = $items
            version = (& $winget --version | Select-Object -First 1)
        }
    }
    if ($joined -match 'No installed package found matching input criteria' -or
        $joined -match '0\s+upgrades?\s+available\.') {
        return [ordered]@{
            state = "current"
            items = @()
            version = (& $winget --version | Select-Object -First 1)
        }
    }
    return [ordered]@{
        state = "unknown"
        items = @()
        reason = "winget_output_unrecognized"
        version = (& $winget --version | Select-Object -First 1)
    }
}

function Get-WindowsUpdateHealth {
    $service = Get-Service wuauserv -ErrorAction SilentlyContinue
    $tasks = @(Get-ScheduledTask -TaskPath "\Microsoft\Windows\WindowsUpdate\" -ErrorAction SilentlyContinue)
    $lastDetect = $null
    try {
        $lastDetect = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\Results\Detect" -ErrorAction Stop).LastSuccessTime
    } catch {
        $lastDetect = $null
    }

    $state = if ($service -and $tasks.Count -gt 0) { "native_scheduler_present" } else { "unknown" }
    return [ordered]@{
        state = $state
        service = if ($service) { "$($service.Status)" } else { "missing" }
        startType = if ($service) { "$($service.StartType)" } else { "missing" }
        scheduledTaskCount = $tasks.Count
        lastDetectSuccess = $lastDetect
        note = "Health only; no Microsoft.Update.Session scan is executed."
    }
}

function Write-PrivateAtomicJson {
    param(
        [Parameter(Mandatory)]$Value,
        [Parameter(Mandatory)][string]$Path
    )

    $directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
    $temporary = Join-Path $directory (".update-candidates-" + [guid]::NewGuid().ToString("N") + ".tmp")
    try {
        $json = $Value | ConvertTo-Json -Depth 8
        [IO.File]::WriteAllText($temporary, $json + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
        Move-Item -Force -LiteralPath $temporary -Destination $Path
        & icacls.exe $Path /inheritance:r /grant:r "*S-1-5-18:F" "*S-1-5-32-544:F" | Out-Null
    } finally {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -Force -LiteralPath $temporary
        }
    }
}

$report = [ordered]@{
    schemaVersion = 1
    kind = "ordivon.workstation.windows-update-candidates"
    generatedAt = [DateTimeOffset]::UtcNow.ToString("o")
    source = "windows-native-read-only-probes"
    checks = [ordered]@{
        winget = Get-WingetCandidates
        windowsUpdateHealth = Get-WindowsUpdateHealth
    }
    effects = [ordered]@{
        packagesUpgraded = 0
        windowsUpdatesInstalled = 0
        processesRestarted = 0
        rebootRequested = $false
    }
}

Write-PrivateAtomicJson -Value $report -Path $Output
Write-Output ("Update candidate report written: " + $Output)
Write-Output ("Probe states: winget=" + $report.checks.winget.state +
    ", windowsUpdateHealth=" + $report.checks.windowsUpdateHealth.state)
