from datetime import date
from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "report_governance_delivery_metrics.py"

spec = importlib.util.spec_from_file_location("report_governance_delivery_metrics", SCRIPT)
assert spec is not None
reporter = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = reporter
spec.loader.exec_module(reporter)


def test_collect_metrics_shape_is_stable():
    metrics = reporter.collect_metrics(reference_date=date(2026, 5, 5))
    expected = {
        "missing_evidence_count",
        "degraded_count",
        "blocked_count",
        "stale_source_count",
        "registry_drift_count",
        "open_debt_count",
        "checker_shadow_count",
        "rework_placeholder",
        "disclaimer",
    }
    assert expected == set(metrics)
    assert "authorization" in metrics["disclaimer"]


def test_collect_metrics_handles_missing_optional_files(tmp_path, monkeypatch):
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setattr(reporter, "ROOT", tmp_path)
    monkeypatch.setattr(reporter, "DOC_REGISTRY", empty / "missing-docs.jsonl")
    monkeypatch.setattr(reporter, "ARTIFACT_REGISTRY", empty / "missing-artifacts.jsonl")
    monkeypatch.setattr(reporter, "DEBT_LEDGER", empty / "missing-debt.jsonl")
    monkeypatch.setattr(reporter, "MATURITY_LEDGER", empty / "missing-maturity.jsonl")
    monkeypatch.setattr(reporter, "SOURCE_REGISTRY", empty / "missing-sources.jsonl")
    monkeypatch.setattr(reporter, "RUNTIME_DIR", empty / "runtime")
    metrics = reporter.collect_metrics(reference_date=date(2026, 5, 5))
    assert metrics["missing_evidence_count"] == 0
    assert metrics["open_debt_count"] == 0
    assert metrics["registry_drift_count"] == 0
