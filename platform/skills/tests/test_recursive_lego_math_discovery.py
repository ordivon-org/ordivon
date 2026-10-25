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
