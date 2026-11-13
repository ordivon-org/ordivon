"""Real native Riskfolio source capture coherence and tamper rejection.

Reuse existing Riskfolio Portfolio.assets_stats/optimization; do not replace
its optimizer. Source bytes remain user-private, historical PIT UNKNOWN.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import runpy
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "riskfolio/etf_riskfolio_native.py"
SOURCE = Path(os.environ["ORDIVON_FINANCE_R3_TEST_CAPTURE_DIR"]).resolve()
manifest_bytes = (SOURCE / "native_study_result.json").read_bytes()
receipt = json.loads(manifest_bytes)
expected = {r["symbol"]: r["normalized_sha256"] for r in receipt["provider_receipts"]}
assert set(expected) == {"SPY", "QQQ", "IWM"}

with TemporaryDirectory(prefix="finance-r3-riskfolio-capture-") as temp:
    captured = Path(temp)
    for symbol in expected:
        shutil.copyfile(
            SOURCE / f"openbb_cboe_{symbol}_normalized.csv",
            captured / f"openbb_cboe_{symbol}_normalized.csv",
        )
    shutil.copyfile(SOURCE / "native_study_result.json",
                    captured / "native_study_result.json")

    path = (captured / "openbb_cboe_SPY_normalized.csv").resolve()
    original = path.read_bytes()
    assert hashlib.sha256(original).hexdigest() == expected["SPY"]
    text = original.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    records = list(reader)
    records[10]["close"] = str(float(records[10]["close"]) + 100.0)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)
    mutated = output.getvalue().encode("utf-8")
    assert original != mutated

    previous = os.environ.get("ORDIVON_FINANCE_R3_ETF_DATA_DIR")
    os.environ["ORDIVON_FINANCE_R3_ETF_DATA_DIR"] = str(captured)
    original_read = Path.read_bytes
    seen = {"count": 0}

    def capture_then_mutate(p: Path) -> bytes:
        raw = original_read(p)
        if p.resolve() == path and seen["count"] == 0:
            seen["count"] += 1
            assert raw == original
            path.write_bytes(mutated)
        return raw

    Path.read_bytes = capture_then_mutate
    try:
        runpy.run_path(str(SCRIPT), run_name="__main__")
    finally:
        Path.read_bytes = original_read
        if previous is None:
            os.environ.pop("ORDIVON_FINANCE_R3_ETF_DATA_DIR", None)
        else:
            os.environ["ORDIVON_FINANCE_R3_ETF_DATA_DIR"] = previous

    assert seen["count"] == 1
    assert path.read_bytes() == mutated
    result = json.loads(
        (ROOT / "riskfolio/native_riskfolio_result.json").read_text(encoding="utf-8")
    )
    assert result["provider_normalized_sha256"]["SPY"] == expected["SPY"]
    assert result["source_manifest_sha256"] == hashlib.sha256(manifest_bytes).hexdigest()
    assert result["capture_input_consumption"] == "one_hash_checked_byte_image"
    assert result["portfolio_target"] is None
    assert result["optimizer_policy_eligible"] is False

    invalid = os.environ.copy()
    invalid["ORDIVON_FINANCE_R3_ETF_DATA_DIR"] = str(captured)
    bad = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=SCRIPT.parent,
        env=invalid,
        capture_output=True,
        text=True,
        timeout=100,
    )
    assert bad.returncode != 0
    assert "Capture hash mismatch: SPY" in bad.stdout + bad.stderr

    print(
        "NATIVE_RISKFOLIO_BYTE_IDENTITY_PASS",
        "input_sha", expected["SPY"],
        "source_path_mutated_after_read", True,
        "captured_same_bytes_optimization", True,
        "pre_admission_tamper_rejected", True,
        "portfolio_target", result["portfolio_target"],
    )
