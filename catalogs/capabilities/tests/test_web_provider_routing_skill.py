from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / ".agents" / "skills" / "web-provider-routing" / "SKILL.md"


def test_web_provider_routing_skill_uses_canonical_monorepo_owner() -> None:
    text = SKILL.read_text(encoding="utf-8")
    commands = re.findall(r"(?m)^python (\S*web_interaction_route\.py)\b", text)
    assert commands, "Skill must give executable routing commands"
    for command in set(commands):
        result = subprocess.run(
            [sys.executable, command, "--help"], cwd=ROOT,
            capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "--adaptive-browser-reasoning" in result.stdout
        assert "--census" in result.stdout
