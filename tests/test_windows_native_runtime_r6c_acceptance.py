from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "windows-native-runtime-r6c-acceptance.ps1"


def test_r6c_acceptance_harness_is_candidate_only_and_faults_are_opt_in():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "[ValidateSet('Status', 'CrashRecovery', 'ActiveJobRecovery')]" in text
    assert "[switch]$ApplyFault" in text
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
    assert "Get-RuntimeDescribe -Id 10" in text
    assert "Get-RuntimeDescribe -Id 11" in text
    assert "pidChanged" in text
    assert "oldPidAbsent" in text


def test_r6c_active_job_witness_replays_exact_request_without_new_identity():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "workspace.open" in text
    assert "workspace.exec" in text
    assert "task.observe" in text
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
