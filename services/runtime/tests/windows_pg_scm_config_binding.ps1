#requires -version 5.1
# Pure source-bound test: extract only the original commitment functions.
# No SCM access, Runtime process, production environment, or credential read.
param([string]$Operator=(Join-Path $PSScriptRoot '../packaging/windows/activate-ordivon-runtime-pg-service.ps1'))
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $Operator).Path,[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw ($errors|Out-String) }
foreach ($name in @('Assert-Commitment','Assert-PgEnvironmentBindings','Assert-Commitments')) {
    $fn=$ast.Find({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name},$true)
    if ($null -eq $fn) { throw "Missing original function $name" }
    . ([scriptblock]::Create($fn.Extent.Text))
}
$fixture=Join-Path ([IO.Path]::GetTempPath()) ('ordivon-scm-config-'+[Guid]::NewGuid().ToString('N'))
$null=New-Item -ItemType Directory -Path $fixture
try {
    $LegacyBinary=Join-Path $fixture 'legacy.bin';$PgBinary=Join-Path $fixture 'pg.bin'
    $PgLauncher=Join-Path $fixture 'launcher.bin';$PgEnvironment=Join-Path $fixture 'candidate.env'
    $TokenFile=Join-Path $fixture 'token-reference-only'
    foreach ($p in @($LegacyBinary,$PgBinary,$PgLauncher)) { [IO.File]::WriteAllText($p,'fixture') }
    $ExpectedLegacySha256=(Get-FileHash $LegacyBinary).Hash
    $ExpectedPgSha256=(Get-FileHash $PgBinary).Hash
    $ExpectedLauncherSha256=(Get-FileHash $PgLauncher).Hash
    $PgImagePath='"'+$PgBinary+'" --windows-service --env-file "'+$PgEnvironment+'"'
    $LegacyImagePath='"'+$LegacyBinary+'"'
    $Direction='Activate';$selectedQualification=$true
    $PgEndpoint='http://127.0.0.1:19001/mcp';$ExpectedNodeId='windows-pg-fixture'
    $lines=@("ORDIVON_PG_RUNNER=$PgLauncher","ORDIVON_PG_BIND=127.0.0.1:19001",
        "ORDIVON_NODE_ID=$ExpectedNodeId","ORDIVON_BEARER_TOKEN_FILE=$TokenFile")
    $utf8=[Text.UTF8Encoding]::new($false)
    function Write-Fixture([string[]]$body) {
        [IO.File]::WriteAllLines($PgEnvironment,$body,$utf8)
        (Get-FileHash $PgEnvironment).Hash
    }
    function Expect-Rejection([string]$label,[string]$pattern) {
        $caught=$false
        try { Assert-Commitments } catch {
            if ($_.Exception.Message -notmatch $pattern) { throw }
            $caught=$true
        }
        if (-not $caught) { throw "Expected rejection: $label" }
        Write-Output "PASS $label"
    }
    $ExpectedEnvironmentSha256=Write-Fixture $lines
    Assert-Commitments
    'PASS selected exact bindings'
    foreach ($key in @('ORDIVON_PG_RUNNER','ORDIVON_PG_BIND','ORDIVON_NODE_ID','ORDIVON_BEARER_TOKEN_FILE')) {
        $wrong=@($lines | ForEach-Object { if ($_.StartsWith($key+'=')) { $key+'=wrong' } else { $_ } })
        $ExpectedEnvironmentSha256=Write-Fixture $wrong
        Expect-Rejection "rehashed wrong $key" $key
        $ExpectedEnvironmentSha256=Write-Fixture @($lines | Where-Object { -not $_.StartsWith($key+'=') })
        Expect-Rejection "rehashed missing $key" $key
    }
    $ExpectedEnvironmentSha256=Write-Fixture ($lines+$lines[0])
    Expect-Rejection 'duplicate configuration key' 'duplicate'
    $selectedQualification=$false
    $ExpectedEnvironmentSha256=Write-Fixture @($lines[0])
    Assert-Commitments
    'PASS manual stage still binds launcher'
    $ExpectedEnvironmentSha256=Write-Fixture @('ORDIVON_PG_RUNNER=wrong')
    Expect-Rejection 'manual stage wrong launcher' 'ORDIVON_PG_RUNNER'
    $Direction='RestoreLegacy'
    Assert-Commitments
    'PASS explicit restore independent of candidate configuration binding'
} finally { Remove-Item -LiteralPath $fixture -Recurse -Force }
