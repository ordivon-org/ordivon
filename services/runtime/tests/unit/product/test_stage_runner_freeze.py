from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "run_stage.py"

spec = importlib.util.spec_from_file_location("run_stage", SCRIPT)
assert spec is not None
runner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)


def test_template_loads_freeze_protocol():
    template = runner.load_template("stage-templates/doc-governance.yaml")
    assert template["freeze_protocol"]["state"] == "open_scope"
    assert template["freeze_protocol"]["enforcement"] == "record_only"


def test_receipt_records_freeze_protocol(monkeypatch):
    monkeypatch.setattr(runner, "_get_modified_files", lambda: [])
    template = {
        "template_id": "fixture",
        "freeze_protocol": {"state": "verification_freeze", "enforcement": "record_only"},
        "verification": [],
    }
    receipt = runner.generate_receipt("fixture-stage", template, [], [], [])
    assert receipt.freeze_protocol["state"] == "verification_freeze"
    assert receipt.overall == "READY"


def test_missing_freeze_protocol_is_compatible(monkeypatch):
    monkeypatch.setattr(runner, "_get_modified_files", lambda: [])
    template = {"template_id": "legacy", "verification": []}
    receipt = runner.generate_receipt("legacy-stage", template, [], [], [])
    assert receipt.freeze_protocol == {}
    assert receipt.overall == "READY"
