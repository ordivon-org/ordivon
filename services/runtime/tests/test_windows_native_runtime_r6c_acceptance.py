from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "windows-native-runtime-r6c-acceptance.ps1"


def test_r6c_acceptance_harness_is_candidate_only_and_faults_are_opt_in():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "[ValidateSet('Status', 'AuthorityProfile', 'PrepareFixture', 'CrashRecovery', 'ActiveJobRecovery', 'CancelJob')]" in text
    assert "[switch]$ApplyFault" in text
    assert "[int]$RecoveryTimeoutSeconds = 90" in text
    assert "[ValidateRange(60, 300)]" in text
    assert "R6c acceptance harness refuses the production service name." in text
    assert "R6c acceptance harness refuses the production MCP endpoint." in text
    assert "R6c acceptance harness refuses the production node identity." in text
    assert "CrashRecovery requires -ApplyFault." in text
    assert "ActiveJobRecovery requires -ApplyFault." in text
    assert "$ProductionServiceName = 'OrdivonRuntime'" in text
    assert "$ProductionEndpoint = 'http://127.0.0.1:8897/mcp'" in text


def test_r6c_crash_witness_requires_new_pid_and_authenticated_runtime_describe():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "Stop-Process -Id $before.processId -Force" in text
    assert "$current.processId -ne $PreviousPid" in text
    assert "-not $oldAlive" in text
    assert "-TimeoutSeconds $RecoveryTimeoutSeconds" in text
    assert "recoveryTimeoutSeconds = $RecoveryTimeoutSeconds" in text
    assert "Get-RuntimeDescribe -Id 10" in text
    assert "Get-RuntimeDescribe -Id 11" in text
    assert "pidChanged" in text
    assert "oldPidAbsent" in text


def test_r6c_active_job_witness_replays_exact_request_without_new_identity():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "workspace.open" in text
    assert "workspace.exec" in text
    assert "job.observe" in text
    wait_fn = text[text.index("function Wait-JobWorking"):text.index("function Invoke-AuthorityProfile")]
    assert "Invoke-McpTool -Name 'job.observe'" in wait_fn
    assert "Invoke-McpTool -Name 'job.get'" not in wait_fn
    assert "$job.PSObject.Properties['attemptState']" in wait_fn
    assert "$replay.jobId -ne $jobId" in text
    assert "$replay.attemptId -ne $attemptId" in text
    assert "executionTarget = 'windows_native'" in text
    assert "windowsAuthority = 'limited'" in text
    assert "R6C_ACTIVE_JOB_DONE" in text


def test_r6c_harness_uses_mcp_metadata_and_never_prints_bearer_value():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "'MCP-Protocol-Version' = $ProtocolVersion" in text
    assert "'Mcp-Method' = $Method" in text
    assert "$headers['Mcp-Name'] = $ToolName" in text
    assert "Authorization = ('Bearer ' + $script:BearerToken)" in text
    assert "Write-Output $script:BearerToken" not in text
    assert "ConvertTo-Json $script:BearerToken" not in text


def test_r6c_harness_suppresses_windows_powershell_progress_in_service_context():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "$ProgressPreference = 'SilentlyContinue'" in text


def test_r6c_harness_handles_optional_json_properties_under_strict_mode():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "$message.PSObject.Properties['error']" in text
    assert "$message.PSObject.Properties['result']" in text
    assert "$result.PSObject.Properties['isError']" in text
    assert "$result.PSObject.Properties['structuredContent']" in text
    assert 'MCP tool $Name returned isError: $diagnostic' in text
    assert "$message.error" not in text


def test_r6c_active_job_fixture_is_materialized_by_real_service_identity():
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


def test_r6c_cancel_job_cleanup_uses_candidate_mcp_not_registry_mutation():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "'CancelJob'" in text
    assert "CancelJob requires -ApplyFault." in text
    assert "Invoke-McpTool -Name 'job.cancel'" in text
    assert "jobId = $JobId" in text
    assert "sqlite" not in text.lower()


def test_r6c_authority_profile_runs_real_limited_and_elevated_windows_jobs():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "'AuthorityProfile'" in text
    assert "Invoke-AuthorityProfile" in text
    assert "WindowsPowerShell" in text
    assert "whoami.exe" in text
    assert "windowsAuthority = $Authority" in text
    assert "administratorsEnabled = $admin" in text
    assert "tokenIntegrityLevelRid = $rid" in text
    assert "limited authority target unexpectedly has Administrators enabled" in text
    assert "limited authority target exceeds Medium integrity" in text
    assert "elevated authority target does not have Administrators enabled" in text
    assert "elevated authority target is below High integrity" in text
    assert "sameDedicatedUserSid" in text
    assert "'--describe-runtime-context'" not in text[text.index("function Invoke-AuthorityProfile"):text.index("function Invoke-ActiveJobRecovery")]


def test_r6c_authority_profile_requires_runtime_to_advertise_both_authorities_first():
    text = SCRIPT.read_text(encoding="utf-8")
    fn = text[text.index("function Invoke-AuthorityProfile"):text.index("function Invoke-ActiveJobRecovery")]
    assert "$authorities = @($windowsNative.windowsAuthorities)" in fn
    assert "@('limited', 'elevated')" in fn
    assert "does not advertise required authority" in fn
    assert fn.index("does not advertise required authority") < fn.index("Ensure-TestRepository")
    assert "executionProvider = $windowsNative.executionProvider" in fn
