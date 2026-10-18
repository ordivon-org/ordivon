[CmdletBinding()]
param(
    [string]$SourceScript = (Join-Path $PSScriptRoot "update_candidate_report.ps1"),
    [string]$InstallRoot = "C:\ProgramData\Ordivon\UpdateDiscovery",
    [string]$TaskName = "Ordivon Update Discovery"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $SourceScript)) {
    throw "Source script does not exist: $SourceScript"
}

New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
$installed = Join-Path $InstallRoot "update_candidate_report.ps1"
Copy-Item -Force -LiteralPath $SourceScript -Destination $installed

$powerShell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$actionArgs = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $installed + '"'
$action = New-ScheduledTaskAction -Execute $powerShell -Argument $actionArgs
$trigger = New-ScheduledTaskTrigger -Daily -At 6:30am
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName
Write-Output ("Installed and started scheduled task: " + $TaskName)
Write-Output ("Installed script: " + $installed)
