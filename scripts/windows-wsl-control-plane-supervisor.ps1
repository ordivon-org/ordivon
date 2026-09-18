param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9._-]+$')]
    [string]$Distro,

    [ValidateSet('Probe', 'Ensure')]
    [string]$Mode = 'Probe',

    [string[]]$Services = @('ordivon-runtime.service', 'ordivon-host-v2.service'),

    [string]$ReceiptPath = 'C:\ProgramData\Ordivon\Runtime\RecoverySupervisor\latest.json',

    [ValidateRange(1, 120)]
    [int]$MaxAttempts = 20,

    [ValidateRange(100, 60000)]
    [int]$RetryMilliseconds = 500,

    [ValidateRange(1000, 60000)]
    [int]$NativeTimeoutMilliseconds = 5000
)

$ErrorActionPreference = 'Stop'
$wsl = "$env:SystemRoot\System32\wsl.exe"
$kind = 'ordivon.runtime.windows-wsl-control-plane-supervisor'

function Write-JsonAtomic([string]$Path, [object]$Value) {
    $parent = Split-Path -Parent $Path
    if (-not [string]::IsNullOrWhiteSpace($parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $temporary = "$Path.tmp-$PID-$([Guid]::NewGuid().ToString('N'))"
    $Value | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $temporary -Encoding UTF8
    Move-Item -Force -LiteralPath $temporary -Destination $Path
}

function Invoke-WslSystemctl([string]$Verb, [string[]]$Units) {
    $invocationId = [Guid]::NewGuid().ToString('N')
    $stdoutPath = Join-Path $env:TEMP "ordivon-wsl-recovery-$PID-$invocationId.out"
    $stderrPath = Join-Path $env:TEMP "ordivon-wsl-recovery-$PID-$invocationId.err"
    try {
        $arguments = @('-d', $Distro, '-u', 'root', '--', '/usr/bin/systemctl', $Verb) + $Units
        $process = Start-Process `
            -FilePath $wsl `
            -ArgumentList $arguments `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath `
            -PassThru -WindowStyle Hidden
        $exited = $process.WaitForExit($NativeTimeoutMilliseconds)
        if (-not $exited) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            try { $process.WaitForExit(2000) | Out-Null } catch { }
            return [pscustomobject]@{
                exitCode = -2
                stdout = ''
                stderr = "wsl.exe probe exceeded ${NativeTimeoutMilliseconds}ms and its client process was terminated"
            }
        }
        $process.WaitForExit()
        $process.Refresh()
        $exitCode = [int]$process.ExitCode
        $stdout = ''
        if (Test-Path -LiteralPath $stdoutPath) {
            $stdoutRaw = Get-Content -Raw -LiteralPath $stdoutPath
            if ($null -ne $stdoutRaw) {
                $stdout = $stdoutRaw.Trim()
            }
        }
        $stderr = ''
        if (Test-Path -LiteralPath $stderrPath) {
            $stderrRaw = Get-Content -Raw -LiteralPath $stderrPath
            if ($null -ne $stderrRaw) {
                $stderr = $stderrRaw.Trim()
            }
        }
        return [pscustomobject]@{
            exitCode = $exitCode
            stdout = $stdout
            stderr = $stderr
        }
    }
    catch {
        return [pscustomobject]@{
            exitCode = -1
            stdout = ''
            stderr = ($_.Exception.ToString() + "`n" + $_.InvocationInfo.PositionMessage)
        }
    }
    finally {
        Remove-Item -Force -ErrorAction SilentlyContinue $stdoutPath, $stderrPath
    }
}

function Probe-Services() {
    $probe = Invoke-WslSystemctl 'is-active' $Services
    $states = @()
    if (-not [string]::IsNullOrWhiteSpace($probe.stdout)) {
        $states = @($probe.stdout -split "`r?`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    }
    $serviceStates = @()
    for ($index = 0; $index -lt $Services.Count; $index++) {
        $state = if ($index -lt $states.Count) { $states[$index] } else { 'missing' }
        $serviceStates += [ordered]@{
            service = $Services[$index]
            state = $state
        }
    }
    $healthy = ($states.Count -eq $Services.Count)
    if ($healthy) {
        foreach ($entry in $serviceStates) {
            if ($entry.state -ne 'active') {
                $healthy = $false
                break
            }
        }
    }
    return [pscustomobject]@{
        healthy = $healthy
        exitCode = $probe.exitCode
        states = $states
        serviceStates = $serviceStates
        stderr = $probe.stderr
    }
}

if (-not (Test-Path -LiteralPath $wsl)) {
    throw "wsl.exe is unavailable: $wsl"
}
if ($Services.Count -eq 0) {
    throw 'at least one systemd service is required'
}
foreach ($service in $Services) {
    if ($service -notmatch '^[A-Za-z0-9@_.:-]+\.service$') {
        throw "invalid systemd service name: $service"
    }
}

$result = [ordered]@{
    schemaVersion = 1
    kind = $kind
    mode = $Mode.ToLowerInvariant()
    distro = $Distro
    services = @($Services)
    startedAtUtc = [DateTime]::UtcNow.ToString('o')
    mutationAttempted = $false
    action = 'none'
    attempts = @()
}

try {
    $initial = Probe-Services
    $result.attempts += [ordered]@{
        phase = 'initial_probe'
        index = 0
        healthy = $initial.healthy
        exitCode = $initial.exitCode
        states = @($initial.states)
        serviceStates = @($initial.serviceStates)
        stderr = $initial.stderr
    }

    if ($initial.healthy) {
        $result.status = 'healthy'
        $result.finishedAtUtc = [DateTime]::UtcNow.ToString('o')
        Write-JsonAtomic $ReceiptPath $result
        exit 0
    }

    if ($Mode -eq 'Probe') {
        $result.status = 'unhealthy'
        $result.finishedAtUtc = [DateTime]::UtcNow.ToString('o')
        Write-JsonAtomic $ReceiptPath $result
        exit 1
    }

    $result.mutationAttempted = $true
    $result.action = 'systemctl_start'
    $start = Invoke-WslSystemctl 'start' $Services
    $result.startExitCode = $start.exitCode
    $result.startStdout = $start.stdout
    $result.startStderr = $start.stderr
    if ($start.exitCode -ne 0) {
        throw "systemctl start failed with exit code $($start.exitCode): $($start.stderr)"
    }

    for ($index = 1; $index -le $MaxAttempts; $index++) {
        $probe = Probe-Services
        $result.attempts += [ordered]@{
            phase = 'post_start_probe'
            index = $index
            healthy = $probe.healthy
            exitCode = $probe.exitCode
            states = @($probe.states)
            serviceStates = @($probe.serviceStates)
            stderr = $probe.stderr
        }
        if ($probe.healthy) {
            $result.status = 'recovered'
            $result.finishedAtUtc = [DateTime]::UtcNow.ToString('o')
            Write-JsonAtomic $ReceiptPath $result
            exit 0
        }
        Start-Sleep -Milliseconds $RetryMilliseconds
    }

    throw "control-plane services did not become active within $MaxAttempts bounded probes"
}
catch {
    $result.status = 'failed'
    $result.error = $_.Exception.ToString()
    $result.finishedAtUtc = [DateTime]::UtcNow.ToString('o')
    try {
        Write-JsonAtomic $ReceiptPath $result
    }
    catch {
        Write-Error "failed to write Windows recovery supervisor receipt: $($_.Exception)"
    }
    Write-Error $result.error
    exit 1
}
