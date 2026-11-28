# Native Windows capture adapter only. No desktop capture or input injection.
param(
    [Parameter(Mandatory=$true)][string]$Stage,
    [Parameter(Mandatory=$true)][ValidateSet('room-encounter','beacon-relay')][string]$Product,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$ExpectedSha
)
$ErrorActionPreference = 'Stop'
if (-not [IO.Path]::IsPathRooted($Stage)) { throw 'absolute stage required' }
$root = Get-Item -LiteralPath $Stage
if (-not $root.PSIsContainer -or ($root.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'invalid stage' }
if ([Diagnostics.Process]::GetCurrentProcess().SessionId -ne 1) { throw 'expected interactive session 1' }
$exe = Join-Path $Stage "$Product.exe"
$file = Get-Item -LiteralPath $exe
if ($file.PSIsContainer -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'invalid executable' }
if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedSha) { throw 'executable SHA differs' }
$out = Join-Path $Stage "$Product-capture"
if (Test-Path -LiteralPath $out) { throw 'capture path already exists' }
New-Item -ItemType Directory -Path $out | Out-Null
$frames = Join-Path $out 'frames'
$app = Join-Path $out 'appdata'
$local = Join-Path $out 'localappdata'
foreach ($path in @($frames,$app,$local)) { New-Item -ItemType Directory -Path $path | Out-Null }
$size = if ($Product -eq 'room-encounter') {'1152x648'} else {'480x720'}
$movie = Join-Path $frames 'frame.png'
$log = Join-Path $out 'native.log'
$psi = New-Object Diagnostics.ProcessStartInfo
$psi.FileName = $exe
$psi.WorkingDirectory = $Stage
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.EnvironmentVariables['APPDATA'] = $app
$psi.EnvironmentVariables['LOCALAPPDATA'] = $local
$psi.Arguments = '--windowed --rendering-method gl_compatibility --audio-driver Dummy --resolution ' + $size + ' --write-movie "' + $movie + '" --fixed-fps 30 --quit-after 8 --log-file "' + $log + '"'
$p = New-Object Diagnostics.Process
$p.StartInfo = $psi
$started = $false
try {
    if (-not $p.Start()) { throw 'child start failed' }
    $started = $true
    $pidObserved = $p.Id
    $session = $p.SessionId
    if ($session -ne 1) { throw 'child session differs' }
    $stdout = $p.StandardOutput.ReadToEndAsync()
    $stderr = $p.StandardError.ReadToEndAsync()
    # Window handle is optional evidence: short fixed-frame recordings may exit before polling sees it.
    $hwnd = 0
    for ($i=0; $i -lt 100 -and -not $p.HasExited; $i++) {
        $p.Refresh()
        $hwnd = $p.MainWindowHandle.ToInt64()
        if ($hwnd -ne 0) { break }
        Start-Sleep -Milliseconds 20
    }
    if (-not $p.WaitForExit(30000)) { throw 'native render timed out' }
    $p.WaitForExit()
    [IO.File]::WriteAllText((Join-Path $out 'stdout.txt'), $stdout.Result)
    [IO.File]::WriteAllText((Join-Path $out 'stderr.txt'), $stderr.Result)
    if ($p.ExitCode -ne 0) { throw "native exit $($p.ExitCode)" }
    if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedSha) { throw 'post executable SHA differs' }
    $pngs = @(Get-ChildItem -LiteralPath $frames -File -Filter '*.png' | Sort-Object Name)
    if ($pngs.Count -ne 8) { throw 'wrong PNG inventory' }
    $hashes = @($pngs | ForEach-Object {
        if ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'frame reparse point' }
        @{name=$_.Name; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
    })
    $receipt = @{product=$Product; executable_sha256=$ExpectedSha; pid=$pidObserved; session=$session; hwnd=$hwnd; exit_code=$p.ExitCode; frames=$hashes}
    [IO.File]::WriteAllText((Join-Path $out 'capture.json'), ($receipt | ConvertTo-Json -Depth 5 -Compress))
    Write-Output ($receipt | ConvertTo-Json -Depth 5 -Compress)
} finally {
    if ($started -and -not $p.HasExited) { $p.Kill(); $p.WaitForExit() }
    $p.Dispose()
}
