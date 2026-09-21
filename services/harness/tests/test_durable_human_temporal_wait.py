from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _class(text: str, name: str) -> ast.ClassDef:
    tree = ast.parse(text)
    return next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name)


def test_materialize_workflow_owns_durable_human_wait_and_exact_update() -> None:
    path = ROOT / "scripts/temporal_agent_automation.py"
    text = path.read_text()
    cls = _class(text, "MaterializeWorkflow")
    segment = ast.get_source_segment(text, cls) or ""
    assert "@workflow.update(name=HUMAN_RESUME_UPDATE)" in segment
    assert "workflow.wait_condition" in segment
    assert "HUMAN_RESUME_ACTIVITY" in segment
    assert "handoffDigest" in segment
    assert "self._expected_handoff_digest" in segment
    assert "self._resume_accepted" in segment


def test_materialize_workflow_update_rejects_wrong_handoff_digest() -> None:
    text = (ROOT / "scripts/temporal_agent_automation.py").read_text()
    cls = _class(text, "MaterializeWorkflow")
    segment = ast.get_source_segment(text, cls) or ""
    assert "handoff digest does not match" in segment
    assert "human handoff is not ready for resume" in segment


def test_launcher_human_resume_updates_original_effect_workflow_not_new_resume_workflow() -> None:
    text = (ROOT / "scripts/temporal_agent_automation_launch.py").read_text()
    block = text[
        text.index('elif a.operation == "human-resume":') : text.index(
            "    else:", text.index('elif a.operation == "human-resume":')
        )
    ]
    assert "execute_update(" in block
    assert "HUMAN_RESUME_UPDATE" in block
    assert "workflow_id=resume_id" not in block
    assert "AGENT_HUMAN_RESUME_WORKFLOW" not in block
    assert "materialization.request_id" in block
    assert "id=resume_id" in block


def test_separate_human_resume_workflow_is_retired_from_worker_registration() -> None:
    text = (ROOT / "scripts/temporal_agent_automation.py").read_text()
    run_worker = text[text.index("async def run_worker(") :]

    assert "AgentHumanResumeWorkflow" not in run_worker
    assert "AGENT_HUMAN_RESUME_WORKFLOW" not in run_worker


def test_mcp_human_resume_description_matches_temporal_update_contract() -> None:
    text = (ROOT / "scripts/agent_automation_mcp.py").read_text()
    block = text[
        text.index('name="materialization.humanResume"') : text.index(
            "    @server.tool(", text.index('name="materialization.humanResume"') + 10
        )
    ]
    assert "durable" in block.lower()
    assert "same" in block.lower()
    assert "effect" in block.lower()
