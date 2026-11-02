"""R2.1 strict input seam for Skills implicit/explicit subtree exclusion.

A DENY path is one canonical POSIX scope, never a caller-created synonym
that matches no Skill when raw string prefix comparison is used.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ordivon_skills import SkillCatalog, SkillCatalogError, SkillSource, TrustState


def _skill(root: Path, relative: str, name: str) -> None:
    path = root / relative / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nname: {name}\ndescription: Review local data with care\n---\n# {name}\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    "prefix",
    (
        "nested/./restricted",
        "nested//restricted",
        r"nested\restricted",
        "nested/\x00restricted",
        ".",
        "./",
    ),
)
@pytest.mark.parametrize("field", ("implicit_deny_prefixes", "explicit_deny_prefixes"))
def test_noncanonical_scope_deny_is_rejected_at_shared_source_boundary(
    tmp_path: Path, prefix: str, field: str
) -> None:
    _skill(tmp_path, "nested/restricted", "restricted")
    with pytest.raises(ValueError, match="canonical"):
        SkillSource(
            "policy",
            tmp_path,
            "user",
            1,
            TrustState.APPROVED,
            **{field: (prefix,)},
        )


@pytest.mark.parametrize("prefix", ("nested/restricted", "nested/restricted/"))
def test_canonical_scope_denies_descendants_not_siblings_in_both_modes(
    tmp_path: Path, prefix: str
) -> None:
    _skill(tmp_path, "nested/restricted", "restricted")
    _skill(tmp_path, "nested/restricted/child", "child")
    _skill(tmp_path, "nested/restricted-peer", "restricted-peer")

    catalog = SkillCatalog.scan(
        [
            SkillSource(
                "policy",
                tmp_path,
                "user",
                1,
                TrustState.APPROVED,
                implicit_deny_prefixes=(prefix,),
                explicit_deny_prefixes=(prefix,),
            )
        ]
    )
    for mode in ("implicit", "explicit"):
        visible = {record.name for record in catalog.view(invocation_mode=mode).records}
        assert visible == {"restricted-peer"}
        for denied in ("restricted", "child"):
            with pytest.raises(SkillCatalogError) as caught:
                catalog.resolve(f"policy/{denied}", invocation_mode=mode)
            assert caught.value.code == "SKILL_NOT_VISIBLE"
        assert (
            catalog.resolve("policy/restricted-peer", invocation_mode=mode).resolved.name
            == "restricted-peer"
        )
        assert [
            record.name for record in catalog.search("review local data", invocation_mode=mode)
        ] == ["restricted-peer"]
        with pytest.raises(SkillCatalogError) as denied:
            catalog.read_text("policy/restricted")
        assert denied.value.code == "SKILL_NOT_VISIBLE"
