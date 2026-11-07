#!/usr/bin/env python3
"""Verify a bounded Paper Accounting arithmetic contract with upstream Z3.

No invented theorem prover: invokes repository-pinned mise Z3 directly.
This checks the abstract integer obligations only, not Python/SQL refinement.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
FORMAL = ROOT / "formal" / "PaperCashSettlementR1.smt2"
TOOL_ROOT = REPO / "tools" / "formal"
SOURCE = ROOT / "src" / "ordivon_capital" / "accounting" / "paper_close.py"
OBLIGATIONS = (
    ("MODEL_NONVACUOUS", "sat"),
    ("NET_ASSET_CONSERVATION", "unsat"),
    ("PURE_SETTLEMENT_DOES_NOT_CREATE_NAV", "unsat"),
    ("INTRADAY_LIQUIDITY_EXCLUDES_RECEIVABLE", "unsat"),
    ("FAULTY_LIQUIDITY_ALLOWANCE_COUNTEREXAMPLE", "sat"),
    ("FAULTY_RECEIVABLE_RETAIN_COUNTEREXAMPLE", "sat"),
)


def main() -> int:
    if not FORMAL.is_file() or FORMAL.is_symlink():
        raise RuntimeError("missing or nonregular Finance formal model")
    check = subprocess.run(
        ["mise", "exec", "--", "z3", "-smt2", str(FORMAL)],
        cwd=TOOL_ROOT,
        text=True,
        capture_output=True,
        timeout=100,
        check=False,
    )
    lines = [line.strip() for line in check.stdout.splitlines() if line.strip()]
    expected = [item for pair in OBLIGATIONS for item in pair]
    if check.returncode != 0 or lines != expected:
        raise RuntimeError(
            "Z3 proof obligation failed or returned UNKNOWN: "
            + json.dumps(
                {"exitCode": check.returncode, "stdout": lines, "stderr": check.stderr[-600:]},
                ensure_ascii=False,
            )
        )
    solver_version = subprocess.check_output(
        ["mise", "exec", "--", "z3", "-version"],
        cwd=TOOL_ROOT, text=True, timeout=15,
    ).strip()
    report = {
        "kind": "ordivon.capital.accounting.paper-cash-settlement-formal-check",
        "status": "PASS_ABSTRACT_QF_LIA_ONLY",
        "model": FORMAL.relative_to(REPO).as_posix(),
        "modelSha256": hashlib.sha256(FORMAL.read_bytes()).hexdigest(),
        "implementation": "domains/capital/src/ordivon_capital/accounting/paper_close.py::value_session",
        "implementationSha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "implementationRefinement": "NOT_FORMALLY_PROVED",
        "postgresConsumer": "NOT_CHECKED_BY_THIS_COMMAND",
        "solver": "Z3 via tools/formal/mise.toml",
        "solverVersion": solver_version,
        "obligations": dict(OBLIGATIONS),
    }
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.SubprocessError, OSError) as error:
        print(f"Finance formal verification rejected: {error}", file=sys.stderr)
        raise SystemExit(2) from error
