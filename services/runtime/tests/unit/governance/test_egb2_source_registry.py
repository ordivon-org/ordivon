from datetime import date
from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "checkers" / "external-source-registry" / "run.py"
FIXTURES = ROOT / "tests" / "fixtures" / "egb2_source_registry"

spec = importlib.util.spec_from_file_location("egb2_external_source_registry", SCRIPT)
assert spec is not None
checker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


def _entries(path: Path):
    entries, errors = checker.load_jsonl(path)
    assert errors == []
    return entries


def test_valid_source_registry_passes():
    errors = checker.validate_entries(
        _entries(FIXTURES / "valid" / "sources.jsonl"),
        reference_date=date(2026, 5, 5),
    )
    assert errors == []


def test_missing_required_field_fails():
    errors = checker.validate_entries(
        _entries(FIXTURES / "invalid" / "missing-field.jsonl"),
        reference_date=date(2026, 5, 5),
    )
    assert any("missing required fields" in e for e in errors)


def test_stale_source_fails():
    errors = checker.validate_entries(
        _entries(FIXTURES / "invalid" / "stale.jsonl"),
        reference_date=date(2026, 5, 5),
    )
    assert any("source is stale" in e for e in errors)


def test_forbidden_overclaim_language_fails():
    errors = checker.validate_entries(
        _entries(FIXTURES / "invalid" / "overclaim.jsonl"),
        reference_date=date(2026, 5, 5),
    )
    assert any("unsafe external benchmark claim" in e for e in errors)
