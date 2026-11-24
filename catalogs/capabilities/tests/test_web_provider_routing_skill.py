"""Skill CLI examples must resolve and parse on the actual checkout."""

import shlex
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / ".agents/skills/web-provider-routing/SKILL.md"
SCRIPT = ROOT / "catalogs/capabilities/routing/web_interaction_route.py"


def test_web_provider_routing_skill_uses_canonical_monorepo_owner() -> None:
    text = SKILL.read_text(encoding="utf-8")
    # Parse examples without probing live providers or performing effects.
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    parser = import_module("catalogs.capabilities.routing.web_interaction_route")._parser()
    commands = [
        shlex.split(line)
        for line in text.replace("\\\n", "").splitlines()
        if line.startswith("python ") and "web_interaction_route.py" in line
    ]
    assert commands
    parsed = []
    for command in commands:
        assert Path(command[1]) == SCRIPT.relative_to(ROOT)
        parsed.append(parser.parse_args(command[2:]))
    assert any(args.census for args in parsed)
    assert any(not args.census for args in parsed)
