"""Keep the Agent's advertised source readset bound to the real current tree.

A former Gateway refactor moved capability/logic/security modules but left
historical root-relative names in AGENTS.md and the routing Skill. This is a
source-consumer regression: a fresh Agent cannot follow a nonexistent path.
"""

from __future__ import annotations

import re
from pathlib import Path

GATEWAY = Path(__file__).resolve().parents[1]
REPO = GATEWAY.parents[1]
READSET_FILE = GATEWAY / "AGENTS.md"
SKILL_FILE = REPO / ".agents/skills/gateway-formal-routing/SKILL.md"


def test_agent_source_readset_refers_to_real_gateway_modules() -> None:
    readset = READSET_FILE.read_text(encoding="utf-8").split("## Readset", 1)[1]
    readset = readset.split("## Human", 1)[0]
    relative_paths = re.findall(r"`(src/ordivon_gateway/[a-zA-Z0-9_./-]+\.py)`", readset)
    assert len(relative_paths) >= 15, "Agent readset lost its real source coverage"
    assert len(relative_paths) == len(set(relative_paths))
    for relative in relative_paths:
        assert (GATEWAY / relative).is_file(), f"obsolete Agent readset: {relative}"


def test_gateway_formal_skill_paths_exist_in_current_checkout() -> None:
    source = SKILL_FILE.read_text(encoding="utf-8")
    relative_paths = re.findall(
        r"`(services/gateway/src/ordivon_gateway/[a-zA-Z0-9_./-]+\.py)`",
        source,
    )
    assert len(relative_paths) >= 2
    for relative in relative_paths:
        assert (REPO / relative).is_file(), f"obsolete Skill source path: {relative}"
