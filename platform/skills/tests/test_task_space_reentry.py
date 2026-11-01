from __future__ import annotations

from pathlib import Path

from ordivon_skills.catalog import SkillCatalog
from ordivon_skills.model import SkillContext, SkillSource, TrustState


def _catalog():
    root = Path(__file__).resolve().parents[3]
    return root, SkillCatalog.scan([
        SkillSource("project-ordivon-next", root / ".agents" / "skills", "project", 900, TrustState.TRUSTED)
    ])


def test_task_space_reentry_is_safe_and_discoverable_only_in_project_scope():
    root, catalog = _catalog()
    expected = "project-ordivon-next/task-space-reentry"
    row = next(r for r in catalog.inventory if r.skill_id == expected)
    assert row.scan_state == "PASS"
    assert row.implicit_invocation is True
    for query in ("task space", "task handoff", "Space reentry"):
        matches = {r.skill_id for r in catalog.search(query, context=SkillContext(workspace_path=root))}
        assert expected in matches, (query, matches)
    assert expected not in {r.skill_id for r in catalog.search("task space")}


def test_task_space_reentry_materializes_bounded_fenced_guidance():
    root, catalog = _catalog()
    context = SkillContext(workspace_path=root)
    result = catalog.resolve("task-space-reentry", context=context)
    skill = catalog.read_text(
        result.resolved.skill_id, context=context,
        expected_snapshot_revision=result.snapshot_revision, projection="raw",
    ).content
    for clause in (
        "work.get", "topic.resume", "attention.reentry", "UNKNOWN",
        "authority", "not automatic", "source",
    ):
        assert clause.lower() in skill.lower(), clause
    ref = catalog.read_text(
        result.resolved.skill_id, relative_path="references/task-packet.md",
        context=context, expected_snapshot_revision=result.snapshot_revision,
        projection="raw",
    ).content
    assert "space:ordivon-capability-task-forum-r1:20261101" in ref
    assert "work:ordivon:capability-program-root-r1:20261101" in ref
    assert "No task is assigned by Space participation" in ref
