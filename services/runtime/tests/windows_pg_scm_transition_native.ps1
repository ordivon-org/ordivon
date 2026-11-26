#requires -version 5.1
<#
Opt-in native Windows SCM acceptance. Run from an elevated test operator
session. Only two unique, disposable own-process fixture services are
created; neither service is an actual Runtime or database Writer.
#>
[CmdletBinding()]
param(
    [string]$Operator=(Join-Path $PSScriptRoot '..\packaging\windows\activate-ordivon-runtime-pg-service.ps1')
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$run=[Guid]::NewGuid().ToString('N').Substring(0,12)
$root=Join-Path ([Environment]::GetFolderPath('CommonApplicationData')) ("OrdivonGcaPgScmFixture-"+$run)
$legacy="OrdivonGcaScmFixtureLegacy$run"
$pg="OrdivonGcaScmFixturePg$run"
if ((Test-Path -LiteralPath $root) -or (Get-Service -Name $legacy -ErrorAction SilentlyContinue) -or (Get-Service -Name $pg -ErrorAction SilentlyContinue)) { throw 'fixture identity already exists' }
$null=New-Item -ItemType Directory -Path $root
$sc="$env:SystemRoot\System32\sc.exe"
$legacyExe=Join-Path $root 'legacy.exe'
$pgExe=Join-Path $root 'pg.exe'
$envFile=Join-Path $root 'pg-fixture.env'
$launcher=Join-Path $root 'launcher-fixture.bin'
function Assert-State($name,$status,$mode) {
    $v=Get-Service -Name $name
    if ($v.Status -ne $status -or $v.StartType -ne $mode) { throw "Unexpected state $name $($v.Status) $($v.StartType)" }
}
function Compile-Service($name,$exe) {
    $code=@"
using System;
using System.IO;
using System.ServiceProcess;
public sealed class Fixture : ServiceBase {
    private readonly string env;
    private Fixture(string p) { ServiceName="$name"; env=p; CanStop=true; }
    protected override void OnStart(string[] args) {
        if (env != null && File.ReadAllText(env) == "FAIL") throw new InvalidOperationException("fixture start failure");
    }
    protected override void OnStop() {}
    public static void Main(string[] args) { ServiceBase.Run(new Fixture(args.Length==3?args[2]:null)); }
}
"@
    $cs=Join-Path $root ($name+'.cs')
    [IO.File]::WriteAllText($cs,$code)
    & "$env:SystemRoot\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /target:exe /r:System.ServiceProcess.dll "/out:$exe" $cs
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $exe)) { throw 'fixture compile failed' }
}
function Get-WriterPid($name){ return [uint32](Get-CimInstance Win32_Service -Filter "Name='$name'").ProcessId }
function Expect-Reject([scriptblock]$action,[string]$pattern) {
    $caught=$false
    try { & $action | Out-Null } catch { if ($_.Exception.Message -notmatch $pattern){throw}; $caught=$true }
    if (-not $caught) { throw 'expected rejection absent' }
}
try {
    $Operator=(Resolve-Path -LiteralPath $Operator).Path
    $errors=$null;$tokens=$null
    [System.Management.Automation.Language.Parser]::ParseFile($Operator,[ref]$tokens,[ref]$errors)|Out-Null
    if ($errors.Count) { throw ($errors|Out-String) }
    'PASS_NATIVE_SCRIPT_PARSER'
    Compile-Service $legacy $legacyExe
    Compile-Service $pg $pgExe
    [IO.File]::WriteAllText($envFile,'OK')
    [IO.File]::WriteAllText($launcher,'fixture only')
    $oldImage='"'+$legacyExe+'"'
    $newImage='"'+$pgExe+'" --windows-service --env-file "'+$envFile+'"'
    # The fixture services do not run Runtime, PG, or user payloads.
    New-Service -Name $legacy -BinaryPathName $oldImage -StartupType Manual | Out-Null
    New-Service -Name $pg -BinaryPathName $newImage -StartupType Disabled | Out-Null
    Start-Service -Name $legacy
    (Get-Service $legacy).WaitForStatus('Running',[TimeSpan]::FromSeconds(20))
    $oldPid=Get-WriterPid $legacy
    $params=@{
      Direction='Activate';LegacyService=$legacy;PgService=$pg
      LegacyImagePath=$oldImage;PgImagePath=$newImage;LegacyAccount='LocalSystem';PgAccount='LocalSystem'
      LegacyStartMode='Manual';PgStartMode='Manual';ExpectedWriterPid=$oldPid
      LegacyBinary=$legacyExe;ExpectedLegacySha256=(Get-FileHash $legacyExe).Hash
      PgBinary=$pgExe;ExpectedPgSha256=(Get-FileHash $pgExe).Hash
      PgLauncher=$launcher;ExpectedLauncherSha256=(Get-FileHash $launcher).Hash
      PgEnvironment=$envFile;ExpectedEnvironmentSha256=(Get-FileHash $envFile).Hash
      TimeoutSeconds=15
    }
    $preview=(& $Operator @params|ConvertFrom-Json)
    if ($preview.effect -ne $false){throw 'preview claims effect'}
    Assert-State $legacy 'Running' 'Manual';Assert-State $pg 'Stopped' 'Disabled'
    'PASS_PREVIEW_NO_SCM_MUTATION'
    Expect-Reject { & $Operator @params -Apply } 'Operator must establish'
    $wrong=@{}+$params;$wrong.PgStartMode='Automatic'
    Expect-Reject { & $Operator @wrong -Apply -IngressQuiesced -OriginalConsumerQualified -OriginalWriterDrained } 'Automatic PG startup requires'
    $wrong=@{}+$params;$wrong.PgEndpoint='http://127.0.0.1:19001/mcp'
    Expect-Reject { & $Operator @wrong -Apply -IngressQuiesced -OriginalConsumerQualified -OriginalWriterDrained } 'inputs must be supplied together'
    Assert-State $legacy 'Running' 'Manual';Assert-State $pg 'Stopped' 'Disabled'
    if ((Get-WriterPid $legacy) -ne $oldPid) {throw 'preflight changed original writer process'}
    'PASS_AUTOMATIC_AND_PARTIAL_QUALIFICATION_REFUSED_BEFORE_EFFECT'

    $wrong=@{}+$params;$wrong.ExpectedWriterPid=$oldPid+1
    Expect-Reject { & $Operator @wrong -Apply -IngressQuiesced -OriginalConsumerQualified -OriginalWriterDrained } 'preimage changed'
    $wrong=@{}+$params;$wrong.ExpectedPgSha256='0'*64
    Expect-Reject { & $Operator @wrong -Apply -IngressQuiesced -OriginalConsumerQualified -OriginalWriterDrained } 'commitment differs'
    Assert-State $legacy 'Running' 'Manual';Assert-State $pg 'Stopped' 'Disabled'
    'PASS_UNQUALIFIED_STALE_PID_HASH_REJECT_BEFORE_EFFECT'
    $receipt=(& $Operator @params -Apply -IngressQuiesced -OriginalConsumerQualified -OriginalWriterDrained|ConvertFrom-Json)
    if (-not $receipt.scmTransitionObserved -or $receipt.consumerQualificationEvaluated -or $receipt.freshPgSessionQualified -or $receipt.fullCutoverAccepted -or $receipt.pgWriterUniquenessEvaluated) {throw 'incorrect truth boundary'}
    Assert-State $legacy 'Stopped' 'Disabled';Assert-State $pg 'Running' 'Manual'
    if (Get-Process -Id $oldPid -ErrorAction SilentlyContinue){throw 'legacy PID present'}
    'PASS_REAL_SCM_ACTIVATE_EXCLUSIVE'
    $params.Direction='RestoreLegacy';$params.ExpectedWriterPid=Get-WriterPid $pg
    $pgPid=$params.ExpectedWriterPid
    $receipt=(& $Operator @params -Apply -IngressQuiesced -OriginalConsumerQualified -OriginalWriterDrained|ConvertFrom-Json)
    Assert-State $legacy 'Running' 'Manual';Assert-State $pg 'Stopped' 'Disabled'
    if (Get-Process -Id $pgPid -ErrorAction SilentlyContinue){throw 'PG PID present'}
    'PASS_REAL_SCM_RESTORE_EXCLUSIVE'
    [IO.File]::WriteAllText($envFile,'FAIL')
    $params.Direction='Activate';$params.ExpectedWriterPid=Get-WriterPid $legacy
    $params.ExpectedEnvironmentSha256=(Get-FileHash $envFile).Hash
    Expect-Reject { & $Operator @params -Apply -IngressQuiesced -OriginalConsumerQualified -OriginalWriterDrained } 'Destination activation failed'
    Assert-State $legacy 'Stopped' 'Disabled';Assert-State $pg 'Stopped' 'Disabled'
    'PASS_FAILED_START_BOTH_DISABLED_NO_AUTOMATIC_ROLLBACK'
    $params.Direction='RestoreLegacy';$params.ExpectedWriterPid=0
    $null=& $Operator @params -Apply -IngressQuiesced -OriginalConsumerQualified -OriginalWriterDrained
    Assert-State $legacy 'Running' 'Manual';Assert-State $pg 'Stopped' 'Disabled'
    'PASS_EXPLICIT_RESTORE_AFTER_FAILED_START'
} finally {
    foreach($name in @($legacy,$pg)){
        if (Get-Service -Name $name -ErrorAction SilentlyContinue){
            & $sc config $name start= disabled | Out-Null
            if ((Get-Service $name).Status -ne 'Stopped'){ Stop-Service $name; (Get-Service $name).WaitForStatus('Stopped',[TimeSpan]::FromSeconds(20)) }
            & $sc delete $name | Out-Null
            if ($LASTEXITCODE -ne 0) {throw "fixture service cleanup failed $name"}
        }
    }
    Remove-Item -LiteralPath $root -Recurse -Force
}
