"""R2.1 source-policy representation: no caller-controlled duplicate JSON keys.

A source permission/denial policy is a function of its serialized key to one
unambiguous value. Invalid source text must be denied before Skills MCP admission.
"""

from __future__ import annotations

import asyncio
import json
from itertools import product
from pathlib import Path

import pytest
from skills_mcp import CatalogProvider, build_server

from ordivon_skills import SkillCatalog
from ordivon_skills.config import _single_valued_policy_object, load_skills_mcp_config


def _source_text(tmp_path: Path) -> tuple[str, Path]:
    root = tmp_path / "sources"
    path = root / "nested" / "restricted" / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "---\nname: restricted\ndescription: Ordinary document review\n---\n# restricted\n",
        encoding="utf-8",
    )
    return str(root), tmp_path / "skills.json"


@pytest.mark.parametrize(
    "insert_at,duplicate",
    (
        ("source", '"implicitDenyPrefixes":["nested/restricted"],"implicitDenyPrefixes":[]'),
        ("source", '"explicitDenyPrefixes":["nested/restricted"],"explicitDenyPrefixes":[]'),
        ("source", '"trust":"UNTRUSTED","trust":"APPROVED"'),
        ("source", '"trust":"UNTRUSTED","tr\\u0075st":"APPROVED"'),
        ("source", '"enabled":false,"enabled":true'),
        (
            "root",
            '"standardDiscovery":{"user":false,"projects":false},"standardDiscovery":{"user":true,"projects":true}',
        ),
        ("workspace", '"trusted":false,"trusted":true'),
    ),
)
def test_duplicate_policy_key_is_rejected_before_admission(
    tmp_path: Path, insert_at: str, duplicate: str
) -> None:
    source_root, config_file = _source_text(tmp_path)
    source_extra = (
        duplicate if insert_at == "source" else '"implicitDenyPrefixes":["nested/restricted"]'
    )
    root_extra = duplicate + "," if insert_at == "root" else ""
    workspace_policy = (
        '{"path":'
        + json.dumps(str(tmp_path))
        + ","
        + (duplicate if insert_at == "workspace" else '"trusted":false')
        + "}"
    )
    data = (
        '{"schemaVersion":2,'
        + root_extra
        + '"standardDiscovery":{"user":false,"projects":false},'
        + '"workspaces":{"w":'
        + workspace_policy
        + "},"
        + '"additionalSources":[{"sourceId":"a","root":'
        + json.dumps(source_root)
        + ',"scope":"user",'
        + source_extra
        + '}],"compatibilitySources":[]}'
    )
    config_file.write_text(data, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key"):
        load_skills_mcp_config(config_file)


def test_valid_single_valued_policy_still_denies_implicit_mcp_skill(
    tmp_path: Path,
) -> None:
    source_root, config_file = _source_text(tmp_path)
    config_file.write_text(
        json.dumps(
            {
                "schemaVersion": 2,
                "standardDiscovery": {"user": False, "projects": False},
                "additionalSources": [
                    {
                        "sourceId": "a",
                        "root": source_root,
                        "scope": "user",
                        "trust": "APPROVED",
                        "implicitDenyPrefixes": ["nested/restricted"],
                        "explicitDenyPrefixes": ["nested/restricted"],
                    }
                ],
                "compatibilitySources": [],
            }
        ),
        encoding="utf-8",
    )
    config = load_skills_mcp_config(config_file)
    assert not SkillCatalog.scan(config.sources).view(invocation_mode="implicit").records
    tools = {
        tool.name: tool
        for tool in build_server(CatalogProvider(config_file))._tool_manager.list_tools()
    }
    result = asyncio.run(tools["skills.list"].fn())
    assert result.structured_content["skills"] == []


def test_real_catalog_provider_refuses_ambiguous_policy_before_mcp_list(
    tmp_path: Path,
) -> None:
    source_root, config_file = _source_text(tmp_path)
    config_file.write_text(
        '{"schemaVersion":2,"standardDiscovery":{"user":false,"projects":false},'
        '"additionalSources":[{"sourceId":"a","root":'
        + json.dumps(source_root)
        + ',"scope":"user","trust":"APPROVED",'
        '"implicitDenyPrefixes":["nested/restricted"],'
        '"implicitDenyPrefixes":[]}],"compatibilitySources":[]}',
        encoding="utf-8",
    )
    # The real MCP provider consumes the same source policy before any catalog
    # can be returned; no partial cache or overwritten DENY is admitted.
    with pytest.raises(ValueError, match="duplicate JSON key"):
        CatalogProvider(config_file).get(force_refresh=True)


def test_finite_exhaustion_single_valued_policy_json_mapping() -> None:
    """Check the actual parser against the unique-map predicate in 340 cases."""
    keys = ("trust", "enabled", "implicitDenyPrefixes", "explicitDenyPrefixes")
    for width in range(1, 5):
        for labels in product(keys, repeat=width):
            serialized = (
                "{"
                + ",".join(json.dumps(key) + ":" + str(index) for index, key in enumerate(labels))
                + "}"
            )
            if len(set(labels)) != len(labels):
                with pytest.raises(ValueError, match="duplicate JSON key"):
                    json.loads(serialized, object_pairs_hook=_single_valued_policy_object)
            else:
                decoded = json.loads(serialized, object_pairs_hook=_single_valued_policy_object)
                assert decoded == dict(zip(labels, range(width), strict=True))
