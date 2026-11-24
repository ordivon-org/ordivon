"""Independent Automation MCP surface consumer tests: no tool invocation."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "evals/automation-mcp-surface-005/verify.py"
spec = importlib.util.spec_from_file_location("automation_mcp_surface_gate", GATE)
assert spec is not None and spec.loader is not None
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def _mcp_source(tools: tuple[str, ...], fields: tuple[str, ...] = ("campaignId", "workBinding")) -> str:
    names = [f"    @server.tool(name={name!r})\n    def f{i}(): pass" for i, name in enumerate(tools)]
    body = "\n".join(f"    {field}: str" for field in fields)
    return "class CampaignSpecInput:\n" + body + "\n\n" + "def build():\n" + "\n".join(names) + "\n"


def test_matching_live_installed_candidate_does_not_claim_release_safety() -> None:
    source = _mcp_source(("campaign.launch", "conversation.turnOutput"))
    result = audit.compare(
        frozenset({"campaign.launch", "conversation.turnOutput"}), source, source,
    )
    assert result["status"] == "NO_NAME_OR_FIELD_SUBTRACTION_DETECTED_NOT_RELEASE_APPROVED"
    assert result["releaseQualified"] is False
    assert result["callerUsageProven"] is False


def test_existing_live_tools_removed_by_candidate_are_detected() -> None:
    installed = _mcp_source(("campaign.launch", "conversation.turnOutput", "browser.route.plan"))
    candidate = _mcp_source(("campaign.launch",))
    result = audit.compare(
        frozenset({"campaign.launch", "conversation.turnOutput", "browser.route.plan"}),
        installed, candidate,
    )
    assert result["status"] == "BREAKING_NAME_OR_FIELD_SUBTRACTION_DETECTED"
    assert result["removedLiveToolNames"] == ["browser.route.plan", "conversation.turnOutput"]


def test_campaign_existing_fields_removed_without_tool_name_change() -> None:
    installed = _mcp_source(("campaign.launch",), ("campaignId", "workBinding", "sharedAttachments"))
    candidate = _mcp_source(("campaign.launch",), ("campaignId",))
    result = audit.compare(frozenset({"campaign.launch"}), installed, candidate)
    assert result["removedCampaignSpecFields"] == ["sharedAttachments", "workBinding"]
    assert result["status"] == "BREAKING_NAME_OR_FIELD_SUBTRACTION_DETECTED"


def test_dynamic_tool_registration_refuses_to_guess() -> None:
    text = _mcp_source(("campaign.launch",)).replace(
        "@server.tool(name='campaign.launch')", "@server.tool(name=runtime_name)"
    )
    with pytest.raises(audit.ContractIndeterminate, match="dynamic"):
        audit.inspect_source(text)


def test_installed_script_disagrees_with_live_toolset_is_unknown() -> None:
    source = _mcp_source(("campaign.launch",))
    result = audit.compare(frozenset({"different.tool"}), source, source)
    assert result["status"] == "INDETERMINATE_INSTALLED_SOURCE_LIVE_MISMATCH"
    assert result["releaseQualified"] is False


def test_duplicate_names_in_tool_capture_refused() -> None:
    with pytest.raises(audit.ContractIndeterminate, match="duplicate"):
        audit.capture_live_names([{"name": "campaign.launch"}, {"name": "campaign.launch"}])


def test_live_capture_rejects_schema_or_sensitive_payload() -> None:
    with pytest.raises(audit.ContractIndeterminate, match="names only"):
        audit.capture_live_names([{"name": "campaign.launch", "inputSchema": {"properties": {}}}])


def test_parse_only_does_not_import_or_execute_candidate() -> None:
    installed = _mcp_source(("campaign.launch",))
    candidate = "raise RuntimeError('must not execute')\n" + installed
    result = audit.compare(frozenset({"campaign.launch"}), installed, candidate)
    assert result["candidateSourceToolCount"] == 1


def test_cli_exit_code_breaking_and_safe_names_only(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    live = tmp_path / "installed-names.json"
    installed = tmp_path / "installed.py"
    candidate = tmp_path / "candidate.py"
    live.write_text(json.dumps([{"name": "campaign.launch"}, {"name": "conversation.turnOutput"}]))
    installed.write_text(_mcp_source(("campaign.launch", "conversation.turnOutput")))
    candidate.write_text(_mcp_source(("campaign.launch",)))
    args = [
        "--live-names-json", str(live),
        "--installed-source", str(installed),
        "--candidate-source", str(candidate),
    ]
    assert audit.main(args) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["removedLiveToolNames"] == ["conversation.turnOutput"]
    candidate.write_text(installed.read_text())
    assert audit.main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["releaseQualified"] is False


def test_same_name_new_required_tool_argument_is_not_static_compatible() -> None:
    installed = _mcp_source(("campaign.launch",))
    candidate = installed.replace("def f0(): pass", "def f0(required_new: str): pass")
    result = audit.compare(frozenset({"campaign.launch"}), installed, candidate)
    assert result["status"] == "INDETERMINATE_TOOL_OR_FIELD_SHAPE_CHANGED"
    assert result["changedToolSignatures"] == ["campaign.launch"]
    assert result["releaseQualified"] is False


def test_same_name_default_removed_is_not_static_compatible() -> None:
    installed = _mcp_source(("campaign.launch",)).replace(
        "def f0(): pass", "def f0(request: str = 'optional'): pass",
    )
    candidate = installed.replace("request: str = 'optional'", "request: str")
    result = audit.compare(frozenset({"campaign.launch"}), installed, candidate)
    assert result["status"] == "INDETERMINATE_TOOL_OR_FIELD_SHAPE_CHANGED"
    assert result["changedToolSignatures"] == ["campaign.launch"]


def test_same_campaign_field_name_with_new_type_or_requiredness_is_not_safe() -> None:
    installed = _mcp_source(("campaign.launch",)).replace(
        "workBinding: str", "workBinding: str | None = None",
    )
    candidate = installed.replace("workBinding: str | None = None", "workBinding: str")
    result = audit.compare(frozenset({"campaign.launch"}), installed, candidate)
    assert result["status"] == "INDETERMINATE_TOOL_OR_FIELD_SHAPE_CHANGED"
    assert result["changedCampaignFieldShapes"] == ["workBinding"]


def test_only_tool_body_changed_is_not_falsely_called_contract_shape_change() -> None:
    installed = _mcp_source(("campaign.launch",))
    candidate = installed.replace("def f0(): pass", "def f0(): return 1")
    result = audit.compare(frozenset({"campaign.launch"}), installed, candidate)
    assert result["status"] == "NO_NAME_OR_FIELD_SUBTRACTION_DETECTED_NOT_RELEASE_APPROVED"
    assert result["releaseQualified"] is False


def test_async_tool_entrypoint_replacing_sync_is_unknown() -> None:
    installed = _mcp_source(("campaign.launch",))
    candidate = installed.replace("def f0(): pass", "async def f0(): pass")
    result = audit.compare(frozenset({"campaign.launch"}), installed, candidate)
    assert result["status"] == "INDETERMINATE_TOOL_OR_FIELD_SHAPE_CHANGED"
    assert result["changedToolSignatures"] == ["campaign.launch"]


def test_cli_fail_closed_exit_3_for_same_name_required_argument_change(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    installed = _mcp_source(("campaign.launch",))
    candidate = installed.replace("def f0(): pass", "def f0(required_new: str): pass")
    live = tmp_path / "live.json"
    live.write_text(json.dumps([{"name": "campaign.launch"}]))
    old = tmp_path / "installed.py"
    new = tmp_path / "candidate.py"
    old.write_text(installed)
    new.write_text(candidate)
    assert audit.main([
        "--live-names-json", str(live), "--installed-source", str(old),
        "--candidate-source", str(new),
    ]) == 3
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "INDETERMINATE_TOOL_OR_FIELD_SHAPE_CHANGED"
    assert result["releaseQualified"] is False


def test_same_name_tool_return_schema_annotation_change_is_unknown() -> None:
    installed = _mcp_source(("campaign.launch",)).replace(
        "def f0(): pass", "def f0() -> str: pass",
    )
    candidate = installed.replace("def f0() -> str", "def f0() -> dict")
    result = audit.compare(frozenset({"campaign.launch"}), installed, candidate)
    assert result["status"] == "INDETERMINATE_TOOL_OR_FIELD_SHAPE_CHANGED"
    assert result["changedToolSignatures"] == ["campaign.launch"]


def test_same_name_tool_readonly_annotation_change_is_unknown() -> None:
    installed = _mcp_source(("campaign.launch",)).replace(
        "@server.tool(name='campaign.launch')",
        "@server.tool(name='campaign.launch', annotations={'readOnlyHint': True})",
    )
    candidate = installed.replace(
        "annotations={'readOnlyHint': True}",
        "annotations={'readOnlyHint': False}",
    )
    result = audit.compare(frozenset({"campaign.launch"}), installed, candidate)
    assert result["status"] == "INDETERMINATE_TOOL_OR_FIELD_SHAPE_CHANGED"
    assert result["changedToolSignatures"] == ["campaign.launch"]


def test_dynamic_registration_keyword_expansion_is_unknown_not_crash() -> None:
    source = _mcp_source(("campaign.launch",)).replace(
        "@server.tool(name='campaign.launch')",
        "@server.tool(name='campaign.launch', annotations={'readOnlyHint': True}, **runtime_options)",
    )
    with pytest.raises(audit.ContractIndeterminate, match="dynamic"):
        audit.inspect_source(source)


def test_cli_unknown_dynamic_registration_metadata_has_structured_exit3(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    installed = _mcp_source(("campaign.launch",))
    candidate = installed.replace(
        "@server.tool(name='campaign.launch')",
        "@server.tool(name='campaign.launch', annotations={'readOnlyHint': True}, **runtime_options)",
    )
    live = tmp_path / "live.json"
    live.write_text(json.dumps([{"name": "campaign.launch"}]))
    old = tmp_path / "installed.py"
    new = tmp_path / "candidate.py"
    old.write_text(installed)
    new.write_text(candidate)
    assert audit.main([
        "--live-names-json", str(live), "--installed-source", str(old),
        "--candidate-source", str(new),
    ]) == 3
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "INDETERMINATE"
    assert result["releaseQualified"] is False
