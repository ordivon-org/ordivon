#requires -version 5.1
[CmdletBinding()]
param(
    [string]$Materializer = (Join-Path $PSScriptRoot '..\packaging\windows\materialize-ordivon-runtime-service.ps1'),
    [switch]$NativeScm,
    [string]$InteractiveWorkspaceSid = ''
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Materializer = (Resolve-Path -LiteralPath $Materializer).Path
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('ordivon-pg-materializer-' + [Guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($fixture) | Out-Null
try {
    $root = Join-Path $fixture 'candidate'
    $workspaceRoot = Join-Path $fixture 'workspaces'
    $cfg = Join-Path $root 'config\ordivon-runtime-pg.env'
    $runtime = Join-Path $fixture 'fixture-runtime.exe'
    $launcher = Join-Path $fixture 'fixture-launcher.exe'
    $manifest = Join-Path $fixture 'manifest.json'
    $token = Join-Path $root 'secrets\runtime-pg-mcp.token'
    $utf8 = [Text.UTF8Encoding]::new($false)
    [IO.Directory]::CreateDirectory((Split-Path $cfg -Parent)) | Out-Null
    [IO.Directory]::CreateDirectory((Split-Path $token -Parent)) | Out-Null
    [IO.File]::WriteAllText($runtime,'fixture runtime',$utf8)
    [IO.File]::WriteAllText($launcher,'fixture launcher',$utf8)
    [IO.File]::WriteAllText($token,'fixture-not-a-production-token',$utf8)
    $sourceCommit='b'*40
    $release=[ordered]@{schemaVersion=1;kind='ordivon.windows-pg-release';truthRole='builder-manifest-claim-bound-to-exact-bytes-not-reproducible-build-proof';source=[ordered]@{commit=$sourceCommit;runtimeTree=('c'*40);runtimeSourceArchiveSha256=('d'*64);cargoLockSha256=('e'*64)};files=@([ordered]@{path='ordivon-runtime-pg.exe';size=(Get-Item $runtime).Length;sha256=(Get-FileHash $runtime).Hash.ToLowerInvariant()},[ordered]@{path='ordivon-windows-pg-job-launcher.exe';size=(Get-Item $launcher).Length;sha256=(Get-FileHash $launcher).Hash.ToLowerInvariant()})}
    [IO.File]::WriteAllText($manifest,($release|ConvertTo-Json -Depth 8),$utf8)
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
        ('ORDIVON_PG_WORKSPACE_ROOT=' + $workspaceRoot),
        ('ORDIVON_PG_RUNNER=' + (Join-Path $root 'bin\ordivon-windows-pg-job-launcher.exe')),
        "ORDIVON_BEARER_TOKEN_FILE=$token"
    )
    if ($InteractiveWorkspaceSid) { $lines += "ORDIVON_PG_INTERACTIVE_WORKSPACE_SID=$InteractiveWorkspaceSid" }
    $options = @{
        RuntimeBinary=$runtime; WindowsJobLauncher=$launcher; TokenSource=$token;
        ServiceName=$serviceName; ProgramDataRoot=$root; Bind=$bind; NodeId=$node;
        PostgresEnvironmentFile=$cfg; InteractiveWorkspaceSid=$InteractiveWorkspaceSid;
        ExpectedRuntimeSha256=(Get-FileHash -LiteralPath $runtime -Algorithm SHA256).Hash;
        ExpectedLauncherSha256=(Get-FileHash -LiteralPath $launcher -Algorithm SHA256).Hash;
        ExpectedPostgresEnvironmentSha256='';
        WindowsPgReleaseManifest=$manifest;ExpectedWindowsPgSourceCommit=$sourceCommit;
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
    if ($p.registryBackend -ne 'postgresql' -or $p.service.start -ne 'disabled' -or
        $p.executionReady -ne $false -or $p.workspacePresentationRoot -ne $workspaceRoot -or $p.files.runtimeTarget -notlike '*ordivon-runtime-pg.exe' -or
        $p.files.launcherTarget -notlike '*ordivon-windows-pg-job-launcher.exe' -or
        $p.files.tokenTarget -notlike '*runtime-pg-mcp.token' -or
        $p.files.releaseManifestTarget -notlike '*ordivon-runtime-pg-release.json' -or
        $p.releaseProvenance.sourceCommitClaim -cne $sourceCommit) { throw 'wrong PG plan' }
    if ((Get-FileHash -LiteralPath $cfg).Hash -ne $original) { throw 'preview changed env' }
    Write-Output 'PASS native PG preview separate paths/disabled-start'
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
    Set-FixtureConfig @($lines | Where-Object { $_ -notlike 'ORDIVON_PG_WORKSPACE_ROOT=*' })
    Assert-Rejected 'missing separate Workspace root refused' 'Required PG environment key missing'
    foreach ($badRoot in @((Join-Path $root 'pg-store\workspaces'),$root,$fixture)) {
        Set-FixtureConfig @($lines | ForEach-Object { if ($_ -like 'ORDIVON_PG_WORKSPACE_ROOT=*') { "ORDIVON_PG_WORKSPACE_ROOT=$badRoot" } else { $_ } })
        Assert-Rejected 'private nested or ancestor Workspace root refused' 'must be disjoint'
    }
    Set-FixtureConfig $lines
    [IO.Directory]::CreateDirectory($workspaceRoot) | Out-Null
    [IO.File]::WriteAllText((Join-Path $workspaceRoot 'foreign.txt'),'fixture')
    Assert-Rejected 'nonempty Workspace root refused' 'must be empty'
    Remove-Item -LiteralPath $workspaceRoot -Recurse -Force
    Set-FixtureConfig $lines
    $options.TokenSource=$runtime
    Assert-Rejected 'wrong token path refused' 'PG TokenSource must be pre-provisioned'
    $options.TokenSource=$token
    $p=(& $Materializer @options | ConvertFrom-Json)
    foreach ($path in @('bin','registry','pg-store','service-home')) {
        if (Test-Path (Join-Path $root $path)) { throw "Preview mutated $path" }
    }
    if (Test-Path -LiteralPath $workspaceRoot) { throw 'preview created Workspace root' }
    if (Get-Service -Name $serviceName -ErrorAction SilentlyContinue) { throw 'preview created service' }
    Write-Output 'PASS final no SCM/SQLite/file install side effect'
    $wrongAccount = 'S-1-5-21-1-2-3-1234'
    if ($InteractiveWorkspaceSid -eq $wrongAccount) { $wrongAccount = 'S-1-5-21-1-2-3-1235' }
    Set-FixtureConfig @($lines | Where-Object { $_ -notlike 'ORDIVON_PG_INTERACTIVE_WORKSPACE_SID=*' })
    if ($InteractiveWorkspaceSid) {
        Assert-Rejected 'missing interactive account binding refused' 'interactive workspace SID must match'
    } else {
        Set-FixtureConfig @($lines + "ORDIVON_PG_INTERACTIVE_WORKSPACE_SID=$wrongAccount")
        Assert-Rejected 'unbound interactive account refused' 'interactive workspace SID must match'
    }
    $wrongLines = @($lines | Where-Object { $_ -notlike 'ORDIVON_PG_INTERACTIVE_WORKSPACE_SID=*' })
    $wrongLines += "ORDIVON_PG_INTERACTIVE_WORKSPACE_SID=$wrongAccount"
    Set-FixtureConfig $wrongLines
    Assert-Rejected 'mismatched interactive account refused' 'interactive workspace SID must match'
    Set-FixtureConfig $lines
    if ($NativeScm) {
        # Actual NTFS junction negative; the materializer must reject before
        # applying any ACL or SCM effect. The destination is our own fixture.
        $alias = Join-Path $fixture 'workspace-alias'
        $aliasTarget = Join-Path $fixture 'alias-target'
        [IO.Directory]::CreateDirectory($aliasTarget) | Out-Null
        New-Item -ItemType Junction -Path $alias -Target $aliasTarget | Out-Null
        try {
            foreach ($badRoot in @($alias,(Join-Path $alias 'child'))) {
                Set-FixtureConfig @($lines | ForEach-Object { if ($_ -like 'ORDIVON_PG_WORKSPACE_ROOT=*') { "ORDIVON_PG_WORKSPACE_ROOT=$badRoot" } else { $_ } })
                Assert-Rejected 'Workspace junction or junction ancestor refused' 'must not traverse files or reparse points'
            }
        } finally {
            [IO.Directory]::Delete($alias)
            [IO.Directory]::Delete($aliasTarget)
            Set-FixtureConfig $lines
        }
        # Explicit opt-in: a disposable service, invalid fixture executables,
        # no production credentials or service identity. Never enable/start
        # the candidate except to check native refusal while disabled.
        $sc = "$env:SystemRoot\System32\sc.exe"
        $serviceCreated = $false
        try {
            & $Materializer @options -Apply | Out-Null
            $serviceCreated = $true
            $observed = Get-Service -Name $serviceName
            if ($observed.Status -ne 'Stopped' -or $observed.StartType -ne 'Disabled') {
                throw 'SCM staging not disabled/stopped'
            }
            Write-Output 'PASS native SCM applied disabled/stopped'
            if (-not [IO.Directory]::Exists($workspaceRoot)) { throw 'separate Workspace root absent' }
            $acl = Get-Acl -LiteralPath $workspaceRoot
            if (-not $acl.AreAccessRulesProtected) { throw 'Workspace root inherits uncontrolled ACL' }
            if ($InteractiveWorkspaceSid) {
                $sid = [Security.Principal.SecurityIdentifier]::new($InteractiveWorkspaceSid)
                $rules = @($acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier]) | Where-Object { $_.IdentityReference -eq $sid })
                $expected = [Security.AccessControl.FileSystemRights]::ReadAttributes -bor [Security.AccessControl.FileSystemRights]::Traverse -bor [Security.AccessControl.FileSystemRights]::Synchronize
                if ($rules.Count -ne 1 -or $rules[0].FileSystemRights -ne $expected -or $rules[0].InheritanceFlags -ne 'None') {
                    throw 'interactive Workspace metadata-only ACL differs'
                }
                $privateRules = @((Get-Acl -LiteralPath (Join-Path $root 'pg-store')).GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier]) | Where-Object { $_.IdentityReference -eq $sid })
                if ($privateRules.Count -ne 0) { throw 'interactive SID appeared in private PG store ACL' }
                Write-Output 'PASS exact metadata-only Workspace root ACL; private PG store unchanged'
            }

            $startOutput = & $sc start $serviceName 2>&1 | Out-String
            if ($LASTEXITCODE -ne 1058) { throw "Expected native disabled start refusal 1058, got $LASTEXITCODE" }
            Write-Output 'PASS native SCM refused start (1058)'
            & $sc config $serviceName start= demand | Out-Null
            if ($LASTEXITCODE -ne 0) { throw 'Cannot create demand-start negative control' }
            $target = Join-Path $root 'bin\ordivon-runtime-pg.exe'
            $before = (Get-FileHash -LiteralPath $target).Hash
            $caught = $false
            try { & $Materializer @options -Apply | Out-Null }
            catch {
                if ($_.Exception.Message -notmatch 'stopped and disabled') { throw }
                $caught = $true
            }
            if (-not $caught -or (Get-FileHash -LiteralPath $target).Hash -ne $before) {
                throw 'Demand-start service was not refused before file mutation'
            }
            Write-Output 'PASS existing demand-start service rejected before effect'
            & $sc config $serviceName start= disabled | Out-Null
            if ($LASTEXITCODE -ne 0) { throw 'Cannot restore disabled staging fence' }
            & $Materializer @options -Apply | Out-Null
            $observed = Get-Service -Name $serviceName
            if ($observed.Status -ne 'Stopped' -or $observed.StartType -ne 'Disabled') {
                throw 'Idempotent stage lost disabled fence'
            }
            Write-Output 'PASS disabled staging reapply'
        } finally {
            if ($serviceCreated -or (Get-Service -Name $serviceName -ErrorAction SilentlyContinue)) {
                & $sc delete $serviceName | Out-Null
                if ($LASTEXITCODE -ne 0) { throw 'Disposable SCM service cleanup failed' }
            }
        }
    }
} finally {
    Remove-Item -LiteralPath $fixture -Recurse -Force
}
