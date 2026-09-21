from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "web-provider-routing" / "SKILL.md"
SCRIPT = ROOT / "scripts" / "web_interaction_route.py"


def test_web_provider_routing_skill_uses_canonical_monorepo_owner() -> None:
    text = SKILL.read_text(encoding="utf-8")
    canonical = "/root/projects/ordivon/meta/next/scripts/web_interaction_route.py"
    retired = "/root/projects/ordivon-next/scripts/web_interaction_route.py"
    assert SCRIPT.is_file()
    assert text.count(canonical) == 5
    assert retired not in text
