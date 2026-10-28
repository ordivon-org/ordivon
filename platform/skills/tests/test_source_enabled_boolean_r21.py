"""R2.1 typed admission: enabled is a Boolean policy, never Python truthiness.

Both direct SkillSource construction and Skills MCP JSON config must share
the same admission invariant before any source becomes model-visible.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from skills_mcp import CatalogProvider, build_server

from ordivon_skills import SkillCatalog, SkillSource, TrustState
from ordivon_skills.config import load_skills_mcp_config


def _skill_root(tmp_path: Path) -> Path:
    root = tmp_path / "skills"
    path = root / "hidden" / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\nname: hidden\ndescription: Read project notes safely\n---\n# hidden\n",
        encoding="utf-8",
    )
    return root


def _config(tmp_path: Path, root: Path, value: object) -> Path:
    config = tmp_path / "skills.json"
    config.write_text(
        json.dumps(
            {
                "schemaVersion": 2,
                "standardDiscovery": {"user": False, "projects": False},
                "additionalSources": [
                    {
                        "sourceId": "scope",
                        "root": str(root),
                        "scope": "user",
                        "trust": "APPROVED",
                        "enabled": value,
                    }
                ],
                "compatibilitySources": [],
            }
        ),
        encoding="utf-8",
    )
    return config


@pytest.mark.parametrize(
    "value",
    ("false", "true", "", 1, 0, 1.0, None, [], {}),
    ids=[
        "string-false",
        "string-true",
        "empty-string",
        "one",
        "zero",
        "float",
        "null",
        "array",
        "object",
    ],
)
def test_source_enabled_wrong_types_are_rejected_at_shared_boundary(
    tmp_path: Path, value: object
) -> None:
    root = _skill_root(tmp_path)
    with pytest.raises(ValueError, match="enabled.*boolean"):
        SkillSource("scope", root, "user", 1, TrustState.APPROVED, enabled=value)
    with pytest.raises(ValueError, match="enabled.*boolean"):
        load_skills_mcp_config(_config(tmp_path, root, value))
    with pytest.raises(ValueError, match="enabled.*boolean"):
        CatalogProvider(_config(tmp_path, root, value)).get(force_refresh=True)


@pytest.mark.parametrize("value", (False, True), ids=["disabled", "enabled"])
def test_boolean_source_enabled_controls_real_mcp_discovery(tmp_path: Path, value: bool) -> None:
    root = _skill_root(tmp_path)
    config = _config(tmp_path, root, value)
    parsed = load_skills_mcp_config(config)
    assert parsed.sources[0].enabled is value
    catalog = SkillCatalog.scan(parsed.sources)
    for mode in ("implicit", "explicit"):
        assert [rec.skill_id for rec in catalog.view(invocation_mode=mode).records] == (
            ["scope/hidden"] if value else []
        )
    tools = {
        tool.name: tool for tool in build_server(CatalogProvider(config))._tool_manager.list_tools()
    }
    listed = asyncio.run(tools["skills.list"].fn())
    assert [row["skillId"] for row in listed.structured_content["skills"]] == (
        ["scope/hidden"] if value else []
    )
