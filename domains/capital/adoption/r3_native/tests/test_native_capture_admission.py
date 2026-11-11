"""Regression for single-consumed-byte native ETF replay and next-open payoff label.

Executes the *real* installed OpenBB/Qlib native consumer in a private
race-mutated capture directory. No broker, paper or PG effect.
"""
from __future__ import annotations
import csv
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ["ORDIVON_FINANCE_R3_TEST_CAPTURE_DIR"]).resolve()
MANIFEST = json.loads((SOURCE / "native_study_result.json").read_text(encoding="utf-8"))
EXPECTED = {r["symbol"]: r["normalized_sha256"] for r in MANIFEST["provider_receipts"]}
assert set(EXPECTED) == {"SPY", "QQQ", "IWM"}

with TemporaryDirectory(prefix="finance-r3-byte-admission-") as tmp:
    test_dir = Path(tmp)
    for sym in EXPECTED:
        shutil.copyfile(SOURCE / f"openbb_cboe_{sym}_normalized.csv",
                        test_dir / f"openbb_cboe_{sym}_normalized.csv")
    shutil.copyfile(SOURCE / "native_study_result.json",
                    test_dir / "native_study_result.json")

    spy = (test_dir / "openbb_cboe_SPY_normalized.csv").resolve()
    original = spy.read_bytes()
    assert sha256(original).hexdigest() == EXPECTED["SPY"]
    mutated = original.replace(b"391.49", b"1391.49", 1)
    if mutated == original:
        # Preserve parseable schema while definitely changing a price.
        text = original.decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(text)))
        rows[10]["close"] = str(float(rows[10]["close"]) + 1000.0)
        out = io.StringIO()
        w = csv.DictWriter(out, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
        mutated = out.getvalue().encode("utf-8")
    assert mutated != original
    old_read_bytes = Path.read_bytes
    hit = {"count": 0}

    def concurrent_source_mutation(path: Path) -> bytes:
        data = old_read_bytes(path)
        if Path(path).resolve() == spy and hit["count"] == 0:
            hit["count"] += 1
            assert data == original, "Pinned source was already altered"
            spy.write_bytes(mutated)  # changes source PATH after verify/read
        return data

    old_capture = os.environ.get("ORDIVON_FINANCE_R3_CAPTURE_DIR")
    os.environ["ORDIVON_FINANCE_R3_CAPTURE_DIR"] = str(test_dir)
    Path.read_bytes = concurrent_source_mutation
    try:
        runpy.run_path(str(ROOT / "etf_qlib_consumer.py"), run_name="__main__")
    finally:
        Path.read_bytes = old_read_bytes
        if old_capture is None:
            os.environ.pop("ORDIVON_FINANCE_R3_CAPTURE_DIR", None)
        else:
            os.environ["ORDIVON_FINANCE_R3_CAPTURE_DIR"] = old_capture

    assert hit["count"] == 1, "Expected exactly one admitted SPY byte capture"
    assert spy.read_bytes() == mutated, "Source path must have changed during run"
    snapshot = (ROOT / "output/openbb_cboe_SPY_normalized.csv").read_bytes()
    assert snapshot == original, "Consumer snapshot was not the admitted input bytes"
    result = json.loads((ROOT / "output/native_study_result.json").read_text(encoding="utf-8"))
    assert result["provider_receipts"][0]["normalized_sha256"] == EXPECTED["SPY"]
    assert result["qlib_prediction_rows"] > 0
    assert result["portfolio_target"] is None
    assert result["forecast"]["usable_as_optimizer_expected_return"] is False
    assert result["forecast"]["target_horizon"] == "new_entry_next_session_open_to_close"

    # Historical QQQ example: previous-session close->next close and
    # next-session open->close can have opposite signs (entry timing matters).
    q = pd.read_csv(SOURCE / "openbb_cboe_QQQ_normalized.csv",
                    parse_dates=["session_date"], index_col="session_date")
    day = pd.Timestamp("2024-08-05")
    previous = q.index[q.index.get_loc(day)-1]
    actual_entry_return = float(q.loc[day, "close"]/q.loc[day, "open"]-1)
    inadmissible_old_label = float(q.loc[day, "close"]/q.loc[previous, "close"]-1)
    recorded = pd.read_parquet(ROOT / "output/qlib_static_dataset.parquet")
    qlib_label = float(recorded.loc[(previous, "QQQ"), ("label", "LABEL0")])
    assert abs(qlib_label - actual_entry_return) < 1e-12
    assert actual_entry_return * inadmissible_old_label < 0

    # A capture altered BEFORE admission must be rejected.
    env = os.environ.copy()
    env["ORDIVON_FINANCE_R3_CAPTURE_DIR"] = str(test_dir)
    probe = subprocess.run(
        [sys.executable, str(ROOT / "etf_qlib_consumer.py")],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=100
    )
    assert probe.returncode != 0, "Pre-admission tamper was accepted"
    assert "Capture hash mismatch: SPY" in probe.stderr + probe.stdout

    print("NATIVE_CAPTURE_SINGLE_BYTES_PASS",
          "sha", EXPECTED["SPY"], "source_mutated_after_read", True,
          "snapshot_admitted_bytes_equal", True,
          "pre_admission_tamper_rejected", True,
          "research_recorder", result["qlib_recorder_id"],
          "forecast_to_trade_not_admitted", True)
    print("NATIVE_NEXT_OPEN_LABEL_PASS", "QQQ", str(day.date()),
          "old_close_close", inadmissible_old_label,
          "new_open_close", actual_entry_return,
          "stored_model_label", qlib_label)
