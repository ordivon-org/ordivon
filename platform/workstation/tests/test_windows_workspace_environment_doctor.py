"""Windows Runtime active-user, ACL, and owner tool consumption contract."""
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "windows" / "workspace_environment_doctor.ps1"


def test_windows_runtime_agent_doctor_uses_native_cwd_and_refuses_service_identity():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "[IO.Directory]::GetCurrentDirectory()" in text
    assert "SERVICE_IDENTITY_NOT_AGENT" in text
    assert "WORKSPACE_ACCESS_DENIED" in text
    assert "Set-Location -LiteralPath" in text
    assert "OWNER_MANIFEST_MISSING" in text
    assert "OWNER_TOOL_UNAVAILABLE" in text
    assert "mise" in text
    assert "WindowsApps" in text
    assert "Get-Command" in text
    assert "ConvertTo-Json" in text
    # Native exit codes must be captured BEFORE PowerShell transforms output.
    assert "$selected = @(& $mise.Source which $tool 2>$null)" in text
    assert "$selectionExitCode = $LASTEXITCODE" in text
    assert "which $tool 2>$null | Select-Object" not in text
    assert "$ownerSearchBoundary" in text
    assert "WORKSPACE_GIT_UNAVAILABLE" in text
    assert "READY_TO_CONSUME" in text
    assert "dependencies_materialized" in text
    assert "Set-Acl" not in text
    assert "icacls" not in text
    assert "Invoke-WebRequest" not in text



def test_git_worktree_metadata_is_required_by_default_not_opt_in():
    code = SCRIPT.read_text(encoding="utf-8")
    # A mise shim can work from the user's HOME while the service-owned
    # Workspace points .git to inaccessible common metadata. Tool-only
    # readiness must not be mistaken for a working Agent checkout.
    assert "[switch]$RequireGit = $true" in code
    assert "WORKSPACE_GIT_UNAVAILABLE" in code
    assert "linked Git metadata" in code
    # Tool-only callers may explicitly opt out of the Git check; never
    # silently weaken the default normal Agent Golden Path.
    assert "RequireGit:$false" in code


def test_windows_doctor_never_silently_remaps_service_workspace_to_user_home():
    code = SCRIPT.read_text(encoding="utf-8")
    assert "WORKSPACE_ACCESS_DENIED" in code
    assert "SERVICE_IDENTITY_NOT_AGENT" in code
    assert "Set-Location -LiteralPath $physicalCwd" in code
    assert "Set-Acl" not in code


def test_windows_doctor_verifies_checkout_identity_before_scoped_mise_trust():
    code = SCRIPT.read_text(encoding="utf-8")
    # A Git bundle checkout belongs to the active user but is not auto-trusted.
    # Only an exact source revision makes a process-local trust exception safe.
    assert "[string]$ExpectedRevision" in code
    assert "WORKSPACE_REVISION_MISMATCH" in code
    assert "gitRoot" in code
    assert "MISE_TRUSTED_CONFIG_PATHS" in code
    assert "MISE_AUTO_INSTALL" in code
    assert "'false'" in code
    assert code.index("WORKSPACE_REVISION_MISMATCH") < code.index("MISE_TRUSTED_CONFIG_PATHS")
    assert code.index("MISE_TRUSTED_CONFIG_PATHS") < code.index("which $tool")



def test_windows_doctor_returns_exact_owner_tool_paths_for_agent_consumers():
    code = SCRIPT.read_text(encoding="utf-8")
    # A shim in the inherited PATH is not proof of which mise-pinned tool
    # an Agent should execute. The READY receipt includes concrete paths.
    assert "$selectedToolPaths = [ordered]@{}" in code
    assert "Test-Path -LiteralPath $selectedPath -PathType Leaf" in code
    assert "$selectedToolPaths[$tool] = $selectedPath" in code
    assert "selectedToolPaths = $selectedToolPaths" in code
    assert code.index("OWNER_MANIFEST_MISSING") < code.index("$selectedToolPaths[$tool]")
    assert "MISE_AUTO_INSTALL" in code


def test_user_owned_standalone_clone_is_opt_in_and_git_digest_bound():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "[string]$WorkspacePath = ''" in source
    assert "STANDALONE_CHECKOUT_REQUIRED" in source
    assert "objects\\info\\alternates" in source
    assert "status --porcelain" in source
    assert "HEAD:mise.toml" in source
    assert "hash-object mise.toml" in source
    assert "WORKSPACE_REVISION_MISMATCH" in source
    assert "MISE_AUTO_INSTALL" in source
    assert "selectedToolPaths = $selectedToolPaths" in source
    assert "safe.directory=*" not in source
