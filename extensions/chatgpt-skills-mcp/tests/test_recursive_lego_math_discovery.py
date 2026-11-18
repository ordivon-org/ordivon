from __future__ import annotations

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


def test_strict_declared_r21_is_retrieved_by_real_skill_consumer() -> None:
    repo = Path(__file__).resolve().parents[3]
    catalog = SkillCatalog.scan([
        SkillSource(
            "project-ordivon-next", repo / ".agents" / "skills",
            "project", 900, TrustState.TRUSTED,
        )
    ])
    context = SkillContext(workspace_path=repo)
    resolution = catalog.resolve("recursive-lego-calculus", context=context)
    source = catalog.read_text(
        resolution.resolved.skill_id,
        context=context,
        expected_snapshot_revision=resolution.snapshot_revision,
        projection="raw",
    ).content
    assert "formally DECLARED or ADMITTED" in source
    assert "ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)" in source
    assert "DECLARATION_COMPLETE" in catalog.read_text(
        resolution.resolved.skill_id,
        relative_path="references/formal-model.md",
        context=context,
        expected_snapshot_revision=resolution.snapshot_revision,
        projection="raw",
    ).content
    assert "same full effective R2.1 contract" in source
    assert "current principal, grant, scope" in source
    assert "READ_MORE/UNFOLD or refusal" in source
