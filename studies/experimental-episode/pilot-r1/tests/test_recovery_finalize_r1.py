from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
PILOT_ROOT = HERE.parents[1]
RECOVERY = PILOT_ROOT / "recover_finalize_r1.py"
FROZEN_EVIDENCE = PILOT_ROOT / "evidence" / "20260928-r1"


def load_recovery():
    spec = importlib.util.spec_from_file_location("oef_recovery_r1", RECOVERY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_evidence(tmp_path: Path) -> Path:
    target = tmp_path / "evidence"
    shutil.copytree(FROZEN_EVIDENCE, target)
    for name in ("analysis.json", "forks.json", "acceptance.json", "recovery.json"):
        (target / name).unlink(missing_ok=True)
    return target


def contains_float(value) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_float(item) for item in value)
    return False


def test_recovery_finalizes_only_from_frozen_completed_evidence(tmp_path: Path) -> None:
    module = load_recovery()
    output = copy_evidence(tmp_path)
    result = module.recover(output)

    assert result["acceptance"]["standing"] == "PASS_PILOT_MECHANICS"
    assert result["acceptance"]["observedTrials"] == 12
    assert result["acceptance"]["providerDispatchesDuringRecovery"] == 0
    assert result["forks"]["declared"]["assessment"]["standing"] == "PASS_DECLARED_DIFFERENCE"
    assert result["forks"]["contaminated"]["assessment"]["standing"] == "CONTAMINATED"
    assert result["analysis"]["numericRepresentation"] == "exact-rational-numerator-denominator"
    assert result["analysis"]["cells"]["deepseek-flash|exact-replacement-v1"]["hiddenPassRate"] == {
        "numerator": 1,
        "denominator": 1,
    }
    assert not contains_float(result)
    first_receipt = result["recovery"]["receiptDigest"]
    repeated = module.recover(output)
    assert repeated["recovery"]["receiptDigest"] == first_receipt
    for name in ("analysis.json", "forks.json", "acceptance.json", "recovery.json"):
        assert (output / name).is_file()


def test_recovery_rejects_uncertain_started_trial(tmp_path: Path) -> None:
    module = load_recovery()
    output = copy_evidence(tmp_path)
    journal = output / "journal.jsonl"
    rows = [json.loads(line) for line in journal.read_text().splitlines() if line.strip()]
    removed = False
    kept = []
    for row in rows:
        if not removed and row.get("event") == "trial_completed":
            removed = True
            continue
        kept.append(row)
    journal.write_text("\n".join(json.dumps(row, sort_keys=True) for row in kept) + "\n")

    with pytest.raises(RuntimeError, match="zero uncertain starts"):
        module.recover(output)
