from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from ordivon_skills import SkillCatalog, SkillCatalogError, SkillContext, SkillSource, TrustState

_ROOT = Path(__file__).resolve().parents[3]
_SOURCE = _ROOT / ".agents" / "skills" / "task-space-reentry"


def _isolated(tmp_path: Path) -> tuple[SkillCatalog, SkillContext, Path]:
    target = tmp_path / ".agents" / "skills" / "task-space-reentry"
    target.parent.mkdir(parents=True)
    shutil.copytree(_SOURCE, target)
    catalog = SkillCatalog.scan(
        [SkillSource("bounded", target.parent, "project", 900, TrustState.TRUSTED)]
    )
    return catalog, SkillContext(workspace_path=tmp_path), target


def test_task_entry_explicit_scope_does_not_leak_across_projects(tmp_path: Path) -> None:
    catalog, context, _ = _isolated(tmp_path)
    selected = catalog.resolve("task-space-reentry", context=context, invocation_mode="implicit")
    assert selected.resolved.scan_state == "PASS"
    assert selected.resolved.implicit_invocation
    assert not selected.resolved.risk_tags
    with pytest.raises(SkillCatalogError) as exc:
        catalog.resolve(
            "task-space-reentry",
            context=SkillContext(workspace_path=Path("/tmp/non_ordivon_project")),
            invocation_mode="explicit",
        )
    assert exc.value.code == "SKILL_NOT_VISIBLE"


def test_task_entry_owner_fenced_read_denies_stale_snapshot_or_instruction(tmp_path: Path) -> None:
    catalog, context, skill_dir = _isolated(tmp_path)
    selected = catalog.resolve("task-space-reentry", context=context)
    kwargs = {
        "context": context,
        "expected_snapshot_revision": selected.snapshot_revision,
        "expected_instruction_digest": selected.resolved.instruction_digest,
        "expected_package_revision": selected.resolved.package_revision,
    }
    skill_id = selected.resolved.skill_id
    assert catalog.read_text(skill_id, **kwargs).instruction_digest == selected.resolved.instruction_digest
    with pytest.raises(SkillCatalogError) as exc:
        catalog.read_text(skill_id, **{**kwargs, "expected_snapshot_revision": "sha256:wrong"})
    assert exc.value.code == "SNAPSHOT_STALE"

    path = skill_dir / "SKILL.md"
    original = path.read_bytes()
    try:
        path.write_bytes(original + b"\n# changed after catalog scan\n")
        with pytest.raises(SkillCatalogError) as exc:
            catalog.read_text(skill_id, **kwargs)
        assert exc.value.code == "DIGEST_MISMATCH"
    finally:
        path.write_bytes(original)

    packet = skill_dir / "references" / "task-packet.md"
    packet.write_bytes(packet.read_bytes() + b"\n# unreviewed packet change\n")
    with pytest.raises(SkillCatalogError) as exc:
        catalog.read_text(skill_id, **kwargs)
    assert exc.value.code == "PACKAGE_CHANGED"


def test_task_entry_source_only_search_does_not_auto_grant_work(tmp_path: Path) -> None:
    catalog, context, _ = _isolated(tmp_path)
    expected = "bounded/task-space-reentry"
    positives = ("task space", "task handoff", "Space reentry")
    negatives = ("just convert 4miles to km", "What did I eat for breakfast?")
    assert all(expected in {v.skill_id for v in catalog.search(query, context=context)}
               for query in positives)
    assert all(expected not in {v.skill_id for v in catalog.search(query, context=context)}
               for query in negatives)
    body = catalog.read_text(expected, context=context).content
    assert "Participation is NOT task assignment" in body
    assert "not automatic Skill injection" in body
