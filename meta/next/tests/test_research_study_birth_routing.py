from pathlib import Path

ROOT = Path(__file__).parents[3]
BIRTH_SKILL = ROOT / ".agents/skills/research-study-birth/SKILL.md"
METHOD_ROUTER = ROOT / ".agents/skills/method-router/SKILL.md"
METHOD_MAP = ROOT / ".agents/skills/method-router/references/method-map.md"


def test_birth_skill_routes_to_research_owner_without_copying_defaults() -> None:
    text = BIRTH_SKILL.read_text(encoding="utf-8")
    assert "ordivon-research-study create" in text
    assert "ordivon-research-study defaults" in text
    assert "ordivon-research-study list-study-types" in text
    assert "study-birth.json" in text
    assert "MUST NOT duplicate the current provider list" in text
    assert "Research-v2 source authority" in text


def test_birth_skill_preserves_owner_boundaries() -> None:
    text = BIRTH_SKILL.read_text(encoding="utf-8")
    assert "Workstation may materialize the locked environment" in text
    assert "Runtime may execute commands" in text
    assert "neither becomes Research Study semantic authority" in text
    assert "Method/reporting standards remain external scientific authorities" in text
    assert "editing an adopted frozen Birth Policy" in text


def test_method_router_hands_new_study_birth_to_dedicated_skill() -> None:
    router = METHOD_ROUTER.read_text(encoding="utf-8")
    method_map = METHOD_MAP.read_text(encoding="utf-8")
    assert "use `research-study-birth` first" in router
    assert "Route that action to `research-study-birth`" in method_map
    assert "Do not encode Research data-plane providers" in method_map
