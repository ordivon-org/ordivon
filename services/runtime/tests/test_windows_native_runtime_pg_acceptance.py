from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "windows-native-runtime-pg-acceptance.ps1"


def test_windows_pg_harness_uses_mcp_metadata_and_never_prints_bearer_value():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "'MCP-Protocol-Version' = $ProtocolVersion" in text
    assert "'Mcp-Method' = $Method" in text
    assert "$headers['Mcp-Name'] = $ToolName" in text
    assert "Authorization = ('Bearer ' + $script:BearerToken)" in text
    assert "Write-Output $script:BearerToken" not in text
    assert "ConvertTo-Json $script:BearerToken" not in text


def test_windows_pg_harness_suppresses_windows_powershell_progress_in_service_context():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "$ProgressPreference = 'SilentlyContinue'" in text


def test_windows_pg_harness_handles_optional_json_properties_under_strict_mode():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "$message.PSObject.Properties['error']" in text
    assert "$message.PSObject.Properties['result']" in text
    assert "$result.PSObject.Properties['isError']" in text
    assert "$result.PSObject.Properties['structuredContent']" in text
    assert 'MCP tool $Name returned isError: $diagnostic' in text
    assert "$message.error" not in text


def test_windows_pg_fixture_is_materialized_by_real_service_identity():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "'PrepareFixture'" in text
    assert "Assert-CurrentTokenIsCandidateServiceIdentity" in text
    assert "PrepareFixture must run under the dedicated candidate service identity." in text
    assert "$PreparedSourceRepo" in text
    assert "$PreparedSourceRevision" in text
    assert "Resolve-PreparedTestRepository" in text
    assert "PreparedSourceRepo is not owned by the dedicated candidate service identity." in text
    assert "workspace.open resolves and verifies the exact" in text
    assert "Set-AcceptanceRepositoryOwnerToService" not in text
    assert ".SetOwner(" not in text
    assert "safe.directory=*" not in text
    assert "git config --global" not in text


def test_native_workspace_cwd_acceptance_rejects_false_success_and_fences_retirement():
    text = SCRIPT.read_text(encoding="utf-8")
    fn = text[text.index("function Invoke-WorkspaceCwdAdmission {"):text.index("function Assert-PgSession1ActiveIdentity {")]
    assert "Invoke-CwdIdentityJob -Authority 'active_user'" in fn
    assert "Invoke-CwdIdentityJob -Authority 'limited'" in fn
    assert "windowsAuthority = $Authority" in fn
    assert "executionDisposition" in fn
    assert "actualCwd" in fn
    assert "expectedCwd" in fn
    assert "active-user target ran outside the bound Workspace" in fn
    assert "workspace.get" in fn
    assert "workspace.close" in fn
    assert "expectedSourceStateDigest" in fn
    assert "force = $false" in fn
    assert "jobId" in fn

def test_session1_cutover_requires_native_and_shell_cwd_exact_replay_and_artifact():
    text = SCRIPT.read_text(encoding="utf-8")
    fn = text[text.index("function Invoke-WorkspaceCwdAdmission {"):text.index("function Assert-PgSession1ActiveIdentity {")]
    assert "[int]$ExpectedActiveUserSessionId = 1" in text
    assert "[Diagnostics.Process]::GetCurrentProcess().SessionId" in fn
    assert "[Environment]::CurrentDirectory" in fn
    assert "$actual.sessionId -ne $ExpectedActiveUserSessionId" in fn
    assert "$replay.jobId -ne $result.jobId" in fn
    assert "$replay.attemptId -ne $result.attemptId" in fn
    assert "Invoke-McpTool -Name 'artifact.read'" in fn
    assert "$digest -ne $descriptor.digest" in fn
    assert "$bytes.Length -ne $descriptor.retainedBytes" in fn
    assert "$actual = Read-VerifiedCwdStdout $active 543" in fn
    assert "active-user target ran outside the bound Workspace" in fn

def test_pg_session1_readback_discriminates_legacy_success_and_reuses_exact_artifact():
    text = SCRIPT.read_text(encoding="utf-8")
    gate = text[text.index("function Assert-PgSession1Projection"):text.index("\nAssert-CandidateBoundary\n")]
    assert "migrationVersion -ne 0" in gate
    assert "PG_SESSION1_REQUIRED_FRESH_PG_PROJECTION" in gate
    assert "DISPATCH_ISSUED" in gate and "$dispatch.Count -ne 1" in gate
    assert "artifact.read" in gate and "$ExpectedAttemptId.stdout" in gate
    assert "ComputeHash($bytes)" in gate and "$body.sessionId -ne 1" in gate
    assert "uniqueWriterQualified = $false; cutoverAccepted = $false" in gate
    assert "workspace.exec" not in gate and "job.cancel" not in gate


def test_fresh_pg_uses_prepared_source_not_fixture_recreation_and_releases_only_on_acceptance():
    text = SCRIPT.read_text(encoding="utf-8")
    fn = text[text.index("function Invoke-WorkspaceCwdAdmission {"):text.index("function Assert-PgSession1ActiveIdentity {")]
    assert "$repo = Resolve-PreparedTestRepository" in fn
    assert "Assert-PgSession1Projection $inspection" in fn
    assert "if ($qualified)" in fn
    assert "$closeRequest.consumerReleased = $true" in fn


def test_single_scm_operator_cannot_auto_start_before_actual_fresh_pg_consumer():
    operator = ROOT / "packaging" / "windows" / "activate-ordivon-runtime-pg-service.ps1"
    text = operator.read_text(encoding="utf-8")
    assert "Automatic PG startup requires exact fresh-PG consumer qualification inputs." in text
    assert "Assert-QualificationInputs\n    Assert-Commitments\n    $legacy=Get-ExactService" in text
    assert "PG activation requires exact release-manifest provenance inputs." in text
    assert "releaseManifestSha256" in text and "sourceCommitClaim" in text
    assert "releaseProvenanceTruthRole" in text
    assert "if ($Direction -eq 'Activate') {'Manual'}" in text
    assert "Mode='WorkspaceCwdAdmission';ServiceName=$PgService" in text
    assert text.index("$consumerReceipt=(& $acceptance @acceptanceArgs)") < text.index("Set-Mode $to.name $targetMode")
    assert text.count("Assert-ListenerOwner $candidatePid $false") == 2
    assert "fullCutoverAccepted=$false" in text


def test_fresh_pg_automatic_start_requires_actual_private_git_consumer():
    text = SCRIPT.read_text(encoding="utf-8")
    fn = text[text.index("function Invoke-WorkspaceCwdAdmission {"):text.index("function Assert-PgSession1ActiveIdentity {")]
    assert "Assert-ProbePath $env:GIT_WORK_TREE $workTree" in fn
    assert "Assert-ProbePath $env:GIT_DIR $gitDir" in fn
    assert "'--absolute-git-dir'" in fn and "'--show-toplevel'" in fn
    assert "'HEAD:' + $sourceFile" in fn
    assert "[IO.FileMode]::CreateNew" in fn
    assert "[IO.File]::ReadAllBytes($marker)" in fn
    assert "@('add','--',$marker)" in fn
    assert "@('rev-parse',(':' + $marker))" in fn
    assert "@('reset','-q','HEAD','--',$marker)" in fn
    assert "$witness.head -ne $repo.revision" in fn
    assert "$baseline.privateGit.$field" in fn and "$actual.privateGit.$field" in fn
    assert fn.index("Fresh PG native Git consumer qualification missing") < fn.index("$qualified = $true")
    assert "privateGitQualified = $true" in fn
    operator = (ROOT / "packaging" / "windows" / "activate-ordivon-runtime-pg-service.ps1").read_text(encoding="utf-8")
    assert operator.index("$consumerReceipt.privateGitQualified -ne $true") < operator.index("Set-Mode $to.name $targetMode")


def test_fresh_pg_reverse_gate_binds_operator_sid_and_attempt_artifact():
    operator = ROOT / "packaging" / "windows" / "activate-ordivon-runtime-pg-service.ps1"
    text = operator.read_text(encoding="utf-8")
    assert "$expectedInteractiveSid=Assert-PgEnvironmentBindings -PassInteractiveSid" in text
    assert "ExpectedActiveUserSid=$expectedInteractiveSid" in text
    assert "$consumerReceipt.activeUserSid -cne $expectedInteractiveSid" in text
    probe = SCRIPT.read_text(encoding="utf-8")
    assert "Assert-PgSession1ActiveIdentity $actual $ExpectedActiveUserSid" in probe
    assert "$descriptor.attemptId -cne $Observation.attemptId" in probe
    assert "$descriptor.artifactId -cne ($Observation.attemptId + '.stdout')" in probe
    assert "$replay.operationDigest -cne $result.operationDigest" in probe
