#requires -version 5.1
# Pure source-bound test: extract only the original commitment functions.
# No SCM access, Runtime process, production environment, or credential read.
param([string]$Operator=(Join-Path $PSScriptRoot '../packaging/windows/activate-ordivon-runtime-pg-service.ps1'))
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
. (Join-Path (Split-Path (Resolve-Path $Operator).Path -Parent) 'windows-pg-release-provenance.ps1')
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $Operator).Path,[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw ($errors|Out-String) }
foreach ($name in @('Assert-Commitment','Assert-PgEnvironmentBindings','Assert-Commitments')) {
    $fn=$ast.Find({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name},$true)
    if ($null -eq $fn) { throw "Missing original function $name" }
    . ([scriptblock]::Create($fn.Extent.Text))
}
$probe=Join-Path $PSScriptRoot '../scripts/windows-native-runtime-r6c-acceptance.ps1'
$ast=[System.Management.Automation.Language.Parser]::ParseFile($probe,[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw ($errors|Out-String) }
$fn=$ast.Find({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Assert-PgSession1ActiveIdentity'},$true)
if ($null -eq $fn) { throw 'Missing original consumer identity function' }
. ([scriptblock]::Create($fn.Extent.Text))
$fixture=Join-Path ([IO.Path]::GetTempPath()) ('ordivon-scm-config-'+[Guid]::NewGuid().ToString('N'))
$null=New-Item -ItemType Directory -Path $fixture
try {
    $LegacyBinary=Join-Path $fixture 'legacy.bin';$PgBinary=Join-Path $fixture 'pg.bin'
    $PgLauncher=Join-Path $fixture 'launcher.bin';$PgEnvironment=Join-Path $fixture 'candidate.env';$PgReleaseManifest=Join-Path $fixture 'manifest.json'
    $TokenFile=Join-Path $fixture 'token-reference-only'
    foreach ($p in @($LegacyBinary,$PgBinary,$PgLauncher)) { [IO.File]::WriteAllText($p,'fixture') }
    $ExpectedLegacySha256=(Get-FileHash $LegacyBinary).Hash
    $ExpectedPgSha256=(Get-FileHash $PgBinary).Hash
    $ExpectedLauncherSha256=(Get-FileHash $PgLauncher).Hash
    $ExpectedSourceCommit='b'*40
    $release=[ordered]@{schemaVersion=1;kind='ordivon.windows-pg-release';truthRole='builder-manifest-claim-bound-to-exact-bytes-not-reproducible-build-proof';source=[ordered]@{commit=$ExpectedSourceCommit;runtimeTree=('c'*40);runtimeSourceArchiveSha256=('d'*64);cargoLockSha256=('e'*64)};files=@([ordered]@{path='ordivon-runtime-pg.exe';size=(Get-Item $PgBinary).Length;sha256=$ExpectedPgSha256.ToLowerInvariant()},[ordered]@{path='ordivon-windows-pg-job-launcher.exe';size=(Get-Item $PgLauncher).Length;sha256=$ExpectedLauncherSha256.ToLowerInvariant()})}
    [IO.File]::WriteAllText($PgReleaseManifest,($release|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
    $ExpectedReleaseManifestSha256=(Get-FileHash $PgReleaseManifest).Hash
    $PgImagePath='"'+$PgBinary+'" --windows-service --env-file "'+$PgEnvironment+'"'
    $LegacyImagePath='"'+$LegacyBinary+'"'
    $Direction='Activate';$selectedQualification=$true
    $PgEndpoint='http://127.0.0.1:19001/mcp';$ExpectedNodeId='windows-pg-fixture'
    $sid='S-1-5-21-111-222-333-1001'
    $other='S-1-5-21-111-222-333-1002'
    $lines=@("ORDIVON_PG_RUNNER=$PgLauncher","ORDIVON_PG_BIND=127.0.0.1:19001",
        "ORDIVON_NODE_ID=$ExpectedNodeId","ORDIVON_BEARER_TOKEN_FILE=$TokenFile","ORDIVON_PG_INTERACTIVE_WORKSPACE_SID=$sid")
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
    if ((Assert-PgEnvironmentBindings -PassInteractiveSid) -cne $sid) { throw 'Committed interactive SID differs' }
    Assert-PgSession1ActiveIdentity ([pscustomobject]@{userSid=$sid;sessionId=1}) $sid 1
    'PASS exact selected bindings and interactive account'
    foreach ($bad in @(@{userSid=$other;sessionId=1},@{userSid=$sid;sessionId=2},@{userSid=$sid;sessionId='1'})) {
        $caught=$false
        try { Assert-PgSession1ActiveIdentity ([pscustomobject]$bad) $sid 1 }
        catch { if ($_.Exception.Message -notmatch 'OPERATOR_ACCOUNT_IDENTITY_MISMATCH') {throw}; $caught=$true }
        if (-not $caught) { throw 'Incorrect interactive account/session accepted' }
    }
    'PASS wrong interactive account, session, and type refused'
    $ExpectedEnvironmentSha256=Write-Fixture @($lines | Where-Object { -not $_.StartsWith('ORDIVON_PG_INTERACTIVE_WORKSPACE_SID=') })
    Expect-Rejection 'missing interactive SID' 'one exact committed interactive account SID'
    $ExpectedEnvironmentSha256=Write-Fixture @($lines | ForEach-Object { if ($_.StartsWith('ORDIVON_PG_INTERACTIVE_WORKSPACE_SID=')) {'ORDIVON_PG_INTERACTIVE_WORKSPACE_SID=S-1-5-18'} else {$_} })
    Expect-Rejection 'system SID not interactive account' 'one exact committed interactive account SID'
    $ExpectedEnvironmentSha256=Write-Fixture ($lines + $lines[-1])
    Expect-Rejection 'duplicate interactive SID' 'duplicate'
    $ExpectedEnvironmentSha256=Write-Fixture $lines
    [IO.File]::AppendAllText($PgEnvironment,'# changed')
    $caught=$false
    try { Assert-PgEnvironmentBindings -PassInteractiveSid | Out-Null } catch {if ($_.Exception.Message -notmatch 'bytes changed') {throw};$caught=$true}
    if (-not $caught) {throw 'Changed committed bytes accepted'}
    'PASS changed identity carrier bytes refused'
    $ExpectedEnvironmentSha256=Write-Fixture @('x'*65537)
    Expect-Rejection 'oversized environment' 'parser bound'

    foreach ($key in @('ORDIVON_PG_RUNNER','ORDIVON_PG_BIND','ORDIVON_NODE_ID','ORDIVON_BEARER_TOKEN_FILE')) {
        $wrong=@($lines | ForEach-Object { if ($_.StartsWith($key+'=')) { $key+'=wrong' } else { $_ } })
        $ExpectedEnvironmentSha256=Write-Fixture $wrong
        Expect-Rejection "rehashed wrong $key" $key
        $ExpectedEnvironmentSha256=Write-Fixture @($lines | Where-Object { -not $_.StartsWith($key+'=') })
        Expect-Rejection "rehashed missing $key" $key
    }
    $ExpectedEnvironmentSha256=Write-Fixture ($lines+$lines[0])
    Expect-Rejection 'duplicate configuration key' 'duplicate'
    $ExpectedEnvironmentSha256=Write-Fixture $lines
    $originalManifestSha=$ExpectedReleaseManifestSha256
    $ExpectedReleaseManifestSha256='0'*64
    Expect-Rejection 'changed release manifest digest' 'manifest digest changed'
    $ExpectedReleaseManifestSha256=$originalManifestSha
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
