from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "checkers" / "oep-governance" / "run.py"
FIXTURES = ROOT / "tests" / "fixtures" / "egb2_oep"

spec = importlib.util.spec_from_file_location("egb2_oep_governance", SCRIPT)
assert spec is not None
checker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


def test_valid_oep_passes():
    path = FIXTURES / "valid" / "oep-0001.md"
    errors = checker.validate_oep_text(path, path.read_text(encoding="utf-8"))
    assert errors == []


def test_missing_required_sections_fail():
    path = FIXTURES / "invalid" / "missing-sections.md"
    errors = checker.validate_oep_text(path, path.read_text(encoding="utf-8"))
    assert any("missing heading" in e for e in errors)
    assert any("rollback" in e.lower() for e in errors)
    assert any("graduation" in e.lower() for e in errors)


def test_authorization_laundering_fails():
    path = FIXTURES / "invalid" / "authorization.md"
    errors = checker.validate_oep_text(path, path.read_text(encoding="utf-8"))
    assert any("unsafe authorization language" in e for e in errors)
