from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "checkers" / "ownership-manifest" / "run.py"
FIXTURES = ROOT / "tests" / "fixtures" / "egb2_ownership"

spec = importlib.util.spec_from_file_location("egb2_ownership_manifest", SCRIPT)
assert spec is not None
checker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


def _entries(path: Path):
    entries, errors = checker.load_jsonl(path)
    assert errors == []
    return entries


def test_valid_ownership_manifest_passes():
    errors = checker.validate_entries(_entries(FIXTURES / "valid" / "ownership.jsonl"))
    assert errors == []


def test_missing_owner_role_fails():
    errors = checker.validate_entries(_entries(FIXTURES / "invalid" / "missing-role.jsonl"))
    assert any("missing required fields" in e for e in errors)


def test_invalid_staleness_fails():
    errors = checker.validate_entries(_entries(FIXTURES / "invalid" / "bad-staleness.jsonl"))
    assert any("staleness_days must be positive integer" in e for e in errors)


def test_missing_required_coverage_fails():
    errors = checker.validate_entries(_entries(FIXTURES / "invalid" / "missing-coverage.jsonl"))
    assert any("missing required ownership coverage" in e for e in errors)
