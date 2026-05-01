"""Tests for ordivon_verify package imports (PV-N1)."""

import subprocess
import sys
from pathlib import Path

from ordivon_verify import (
    build_report,
    determine_status,
    load_config,
    main,
    parse_args,
    print_human,
    run_external_checker,
    run_external_receipts,
    status_to_exit_code,
    validate_config,
)

from ordivon_verify.cli import main as cli_main
from ordivon_verify.config import is_ordivon_native as config_is_native
from ordivon_verify.report import build_report as report_build
from ordivon_verify.runner import run_check as runner_run_check
from ordivon_verify.checks.receipts import scan_receipt_files as receipts_scan
from ordivon_verify.checks.debt import validate_debt_ledger as debt_validate
from ordivon_verify.checks.gates import validate_gate_manifest as gates_validate
from ordivon_verify.checks.docs import validate_document_registry as docs_validate


def test_package_imports_top_level():
    """All top-level public API imports work."""
    assert callable(main)
    assert callable(build_report)
    assert callable(determine_status)
    assert callable(status_to_exit_code)


def test_package_imports_cli():
    assert callable(cli_main)
    assert callable(parse_args)


def test_package_imports_config():
    assert callable(load_config)
    assert callable(validate_config)
    assert callable(config_is_native)


def test_package_imports_report():
    assert callable(report_build)
    assert callable(print_human)


def test_package_imports_runner():
    assert callable(runner_run_check)
    assert callable(run_external_checker)
    assert callable(run_external_receipts)


def test_package_imports_checks():
    assert callable(receipts_scan)
    assert callable(debt_validate)
    assert callable(gates_validate)
    assert callable(docs_validate)


def test_script_wrapper_still_works():
    """scripts/ordivon_verify.py imports and runs main()."""
    script = Path(__file__).resolve().parents[3] / "scripts" / "ordivon_verify.py"
    result = subprocess.run(
        [sys.executable, str(script), "all"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(Path(__file__).resolve().parents[3]),
    )
    assert result.returncode == 0
    assert "READY" in result.stdout


def test_module_entrypoint():
    """python -m ordivon_verify all works (with src/ on PYTHONPATH)."""
    import os

    env = os.environ.copy()
    src_path = str(Path(__file__).resolve().parents[3] / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src_path}:{existing}" if existing else src_path
    result = subprocess.run(
        [sys.executable, "-m", "ordivon_verify", "all"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(Path(__file__).resolve().parents[3]),
        env=env,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "READY" in result.stdout


def test_no_private_core_imports():
    """Package modules must not import finance/broker/risk."""
    src = Path(__file__).resolve().parents[3] / "src" / "ordivon_verify"
    forbidden = ["adapters.finance", "domains.finance", "Alpaca", "broker", "RiskEngine", "Policy"]
    for py_file in src.rglob("*.py"):
        content = py_file.read_text()
        for pattern in forbidden:
            assert pattern not in content, f"{py_file} contains forbidden import: {pattern}"
