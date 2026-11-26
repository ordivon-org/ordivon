#requires -version 5.1
[CmdletBinding()]
param(
    [string]$Materializer = (Join-Path $PSScriptRoot '..\packaging\windows\materialize-ordivon-runtime-service.ps1')
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Materializer = (Resolve-Path -LiteralPath $Materializer).Path
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('ordivon-pg-materializer-' + [Guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($fixture) | Out-Null
try {
    $root = Join-Path $fixture 'candidate'
    $cfg = Join-Path $root 'config\ordivon-runtime-pg.env'
    $runtime = Join-Path $fixture 'fixture-runtime.exe'
    $launcher = Join-Path $fixture 'fixture-launcher.exe'
    $token = Join-Path $root 'secrets\runtime-pg-mcp.token'
    $utf8 = [Text.UTF8Encoding]::new($false)
    [IO.Directory]::CreateDirectory((Split-Path $cfg -Parent)) | Out-Null
    [IO.Directory]::CreateDirectory((Split-Path $token -Parent)) | Out-Null
    [IO.File]::WriteAllText($runtime,'fixture runtime',$utf8)
    [IO.File]::WriteAllText($launcher,'fixture launcher',$utf8)
    [IO.File]::WriteAllText($token,'fixture-not-a-production-token',$utf8)
    $serviceName = 'OrdivonPgFixture' + [Guid]::NewGuid().ToString('N')
    $bind = '127.0.0.1:19487'
    $node = 'windows-pg-fixture'
    $lines = @(
        'ORDIVON_PG_DSN=host=127.0.0.1 port=1 dbname=fixture',
        'ORDIVON_PG_SCHEMA=fixture',
        ('ORDIVON_PG_SOURCE_SHA256=' + ('a'*64)),
        'ORDIVON_PG_PRINCIPAL=fixture',
        'ORDIVON_PG_EXECUTABLE_ROOTS_JSON=["C:\\Windows"]',
        "ORDIVON_PG_BIND=$bind",
        "ORDIVON_NODE_ID=$node",
        ('ORDIVON_PG_STORE_ROOT=' + (Join-Path $root 'pg-store')),
        ('ORDIVON_PG_RUNNER=' + (Join-Path $root 'bin\ordivon-windows-pg-job-launcher.exe')),
        "ORDIVON_BEARER_TOKEN_FILE=$token"
    )
    $options = @{
        RuntimeBinary=$runtime; WindowsJobLauncher=$launcher; TokenSource=$token;
        ServiceName=$serviceName; ProgramDataRoot=$root; Bind=$bind; NodeId=$node;
        PostgresEnvironmentFile=$cfg;
        ExpectedRuntimeSha256=(Get-FileHash -LiteralPath $runtime -Algorithm SHA256).Hash;
        ExpectedLauncherSha256=(Get-FileHash -LiteralPath $launcher -Algorithm SHA256).Hash;
        ExpectedPostgresEnvironmentSha256='';
    }
    function Set-FixtureConfig([string[]]$body) {
        [IO.File]::WriteAllLines($cfg,$body,$utf8)
        $options.ExpectedPostgresEnvironmentSha256 = (Get-FileHash -LiteralPath $cfg -Algorithm SHA256).Hash
    }
    function Assert-Rejected([string]$name,[string]$pattern) {
        $caught=$false
        try { & $Materializer @options | Out-Null }
        catch {
            if ($_.Exception.Message -notmatch $pattern) { throw }
            $caught=$true
        }
        if (-not $caught) { throw "Expected rejection: $name" }
        Write-Output "PASS $name"
    }
    Set-FixtureConfig $lines
    $original=(Get-FileHash -LiteralPath $cfg).Hash
    $p=(& $Materializer @options | ConvertFrom-Json)
    if ($p.registryBackend -ne 'postgresql' -or $p.service.start -ne 'demand' -or
        $p.executionReady -ne $false -or $p.files.runtimeTarget -notlike '*ordivon-runtime-pg.exe' -or
        $p.files.launcherTarget -notlike '*ordivon-windows-pg-job-launcher.exe' -or
        $p.files.tokenTarget -notlike '*runtime-pg-mcp.token') { throw 'wrong PG plan' }
    if ((Get-FileHash -LiteralPath $cfg).Hash -ne $original) { throw 'preview changed env' }
    Write-Output 'PASS native PG preview separate paths/manual-start'
    $options.ExpectedRuntimeSha256='0'*64
    Assert-Rejected 'wrong binary digest' 'SHA-256 commitment mismatch'
    $options.ExpectedRuntimeSha256=(Get-FileHash -LiteralPath $runtime).Hash
    $options.ExpectedPostgresEnvironmentSha256='0'*64
    Assert-Rejected 'wrong environment digest' 'SHA-256 commitment mismatch'
    Set-FixtureConfig ($lines + 'ORDIVON_REGISTRY_ROOT=C:\legacy')
    Assert-Rejected 'legacy SQLite registry refused' 'Legacy or inline secret key forbidden'
    Set-FixtureConfig ($lines + 'ORDIVON_PG_TOKEN=fixture')
    Assert-Rejected 'inline bearer refused' 'Legacy or inline secret key forbidden'
    Set-FixtureConfig ($lines + 'ORDIVON_PG_SCHEMA=duplicate')
    Assert-Rejected 'duplicate key refused' 'Unsupported or duplicate PG environment key'
    Set-FixtureConfig @($lines | Where-Object { $_ -notlike 'ORDIVON_PG_DSN=*' })
    Assert-Rejected 'missing DSN refused' 'Required PG environment key missing'
    $bad=@($lines | ForEach-Object { if ($_ -like 'ORDIVON_PG_STORE_ROOT=*') { 'ORDIVON_PG_STORE_ROOT=C:\wrong' } else { $_ } })
    Set-FixtureConfig $bad
    Assert-Rejected 'wrong PG store refused' 'PG environment does not bind the planned service'
    Set-FixtureConfig $lines
    $options.TokenSource=$runtime
    Assert-Rejected 'wrong token path refused' 'PG TokenSource must be pre-provisioned'
    $options.TokenSource=$token
    $p=(& $Materializer @options | ConvertFrom-Json)
    foreach ($path in @('bin','registry','pg-store','service-home')) {
        if (Test-Path (Join-Path $root $path)) { throw "Preview mutated $path" }
    }
    if (Get-Service -Name $serviceName -ErrorAction SilentlyContinue) { throw 'preview created service' }
    Write-Output 'PASS final no SCM/SQLite/file install side effect'
} finally {
    Remove-Item -LiteralPath $fixture -Recurse -Force
}

