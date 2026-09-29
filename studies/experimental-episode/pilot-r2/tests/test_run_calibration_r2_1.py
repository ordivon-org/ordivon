from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "run_calibration_r2_1.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("experimental_fabric_r2_1_calibration_test", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_successor_preregistration_preserves_r1_and_binds_decision_frontier() -> None:
    m = load_runner()
    value = m.build_preregistration()
    assert value["designRevision"] == "r2.1"
    assert value["schedule"]["trialCount"] == 24
    assert value["schedule"]["taskBlockCount"] == 6
    assert value["decisionFrontier"]["atomicObservationUnit"] == "complete-four-cell-task-block"
    assert value["supersedesPreEffect"]["preregistrationDigest"].startswith("sha256:")
    assert value["claimSpecBinding"]["claimSpecDigest"].startswith("sha256:")
    base = m.load_base_runner()
    assert value["preregistrationDigest"] == base.canonical_digest({key: item for key, item in value.items() if key != "preregistrationDigest"})


def test_old_r1_preregistration_remains_replayable_after_successor_files_exist(tmp_path: Path) -> None:
    m = load_runner()
    base = m.load_base_runner()
    frozen = base.resolve_preregistration(ROOT / "evidence" / "calibration" / "20260929-r1")
    assert frozen["preregistrationDigest"] == "sha256:38d20e4574190527fdf9cc2bb776ca6ca5eb1fd8772ac61b25c024c4bcddb5e6"
