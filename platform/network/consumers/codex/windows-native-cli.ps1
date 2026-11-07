# Scoped Windows native Codex CLI launcher. No global proxy or Desktop mutation.
# The already-running Desktop is not reconfigured by this launcher.
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $CodexArguments
)
$ErrorActionPreference = 'Stop'
if (-not $CodexArguments -or $CodexArguments.Count -eq 0) {
    throw 'Pass native Codex CLI arguments (for example: exec --skip-git-repo-check ...).'
}
$root = Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\bin'
if (-not (Test-Path -LiteralPath $root -PathType Container)) {
    throw 'Native Codex installation root missing.'
}
$prefix = [IO.Path]::GetFullPath($root).TrimEnd('\') + '\'
$running = @(Get-CimInstance Win32_Process -Filter "Name='codex.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.ExecutablePath -and (Test-Path -LiteralPath $_.ExecutablePath -PathType Leaf) } |
    Select-Object -ExpandProperty ExecutablePath)
$installed = @(
    Get-ChildItem -LiteralPath $root -Filter codex.exe -File -Recurse -ErrorAction Stop |
    Sort-Object LastWriteTimeUtc -Descending |
    Select-Object -ExpandProperty FullName
)
$selected = @($running + $installed | Where-Object {
    $path = [IO.Path]::GetFullPath($_)
    $path.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase) -and
    (Split-Path -Leaf $path) -ieq 'codex.exe'
} | Select-Object -First 1)
if ($selected.Count -ne 1) { throw 'No trusted installed native Codex executable found.' }

# Windows GUI/Desktop processes will not inherit changes made inside this
# invocation. These environment variables are scoped to this child tree only.
$proxy = 'http://127.0.0.1:19982'
$env:HTTP_PROXY = $proxy
$env:HTTPS_PROXY = $proxy
$env:http_proxy = $proxy
$env:https_proxy = $proxy
$env:ALL_PROXY = $proxy
$env:all_proxy = $proxy
$env:NO_PROXY = 'localhost,127.0.0.1,::1'
$env:no_proxy = $env:NO_PROXY

# Native Codex emits normal progress on stderr. Windows PowerShell 5.1
# converts native stderr into ErrorRecords; Stop would terminate a healthy CLI.
# The original Codex process exit code, not stderr text, remains authoritative.
$ErrorActionPreference = 'Continue'
& $selected[0] @CodexArguments
exit $LASTEXITCODE
