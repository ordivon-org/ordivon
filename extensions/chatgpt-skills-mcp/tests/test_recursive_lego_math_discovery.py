from __future__ import annotations

import hashlib
from pathlib import Path

from ordivon_skills.catalog import SkillCatalog
from ordivon_skills.model import SkillContext, SkillSource, TrustState


def test_recursive_lego_math_method_is_found_only_in_qualified_project_scope() -> None:
    repo = Path(__file__).resolve().parents[3]
    skills = repo / ".agents" / "skills"
    assert skills.is_dir()
    catalog = SkillCatalog.scan(
        [SkillSource("project-ordivon-next", skills, "project", 900, TrustState.TRUSTED)]
    )
    scoped = SkillContext(workspace_path=repo)
    expected = "project-ordivon-next/recursive-lego-calculus"
    for query in ("algebra", "mathematical contract", "CEGAR"):
        matches = {record.skill_id for record in catalog.search(query, context=scoped)}
        assert expected in matches, (query, matches)

    unscoped = {record.skill_id for record in catalog.search("algebra")}
    assert expected not in unscoped


def test_ol_foundations_are_retrieved_by_real_skill_consumer() -> None:
    repo = Path(__file__).resolve().parents[3]
    catalog = SkillCatalog.scan([
        SkillSource(
            "project-ordivon-next", repo / ".agents" / "skills",
            "project", 900, TrustState.TRUSTED,
        )
    ])
    context = SkillContext(workspace_path=repo)
    resolution = catalog.resolve("recursive-lego-calculus", context=context)
    record = resolution.resolved
    assert record.skill_id == "project-ordivon-next/recursive-lego-calculus"
    skill_root = repo / ".agents" / "skills" / "recursive-lego-calculus"
    # Qualify the actual discovery/read contract, not mutable wording or a
    # mandatory mathematical representation in advisory documentation.
    for path in ("SKILL.md", "references/formal-model.md"):
        expected = (skill_root / path).read_bytes()
        digest = "sha256:" + hashlib.sha256(expected).hexdigest()
        result = catalog.read_text(
            record.skill_id,
            relative_path=path,
            context=context,
            expected_snapshot_revision=resolution.snapshot_revision,
            expected_instruction_digest=record.instruction_digest,
            expected_package_revision=record.package_revision,
            projection="raw",
        )
        assert result.skill_id == record.skill_id
        assert result.path == path
        assert result.projection == "RAW"
        assert result.content.encode("utf-8") == expected
        assert result.raw_digest == result.digest == digest
        assert result.raw_size == result.size == len(expected)
        assert result.next_offset is None
        assert result.instruction_digest == record.instruction_digest
        assert result.package_revision == record.package_revision


def test_topic_retirement_contract_reaches_qualified_skill_consumer() -> None:
    repo = Path(__file__).resolve().parents[3]
    catalog = SkillCatalog.scan([
        SkillSource(
            "project-ordivon-next", repo / ".agents" / "skills",
            "project", 900, TrustState.TRUSTED,
        )
    ])
    context = SkillContext(workspace_path=repo)
    resolution = catalog.resolve("recursive-lego-calculus", context=context)
    guide = catalog.read_text(
        resolution.resolved.skill_id,
        relative_path="references/owner-provider-human-agent.md",
        context=context,
        expected_snapshot_revision=resolution.snapshot_revision,
        projection="raw",
    ).content
    for obligation in (
        "explicit supersession",
        "expectedHighSequence",
        "NOT_FOUND",
        "UNKNOWN",
        "read back",
    ):
        assert obligation in guide, obligation
