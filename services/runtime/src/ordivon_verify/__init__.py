"""Ordivon Verify — Local read-only verification CLI.

Package public API. Import from here for programmatic use.
"""

from ordivon_verify.cli import main as main, parse_args as parse_args  # noqa: F811
from ordivon_verify.report import (
    build_report as build_report,
    determine_status as determine_status,
    print_human as print_human,
    status_to_exit_code as status_to_exit_code,
)
from ordivon_verify.config import (
    is_ordivon_native as is_ordivon_native,
    load_config as load_config,
    validate_config as validate_config,
)
from ordivon_verify.runner import (
    run_check as run_check,
    run_external_checker as run_external_checker,
    run_external_receipts as run_external_receipts,
)
from ordivon_verify.checks.receipts import scan_receipt_files as scan_receipt_files
from ordivon_verify.checks.debt import validate_debt_ledger as validate_debt_ledger
from ordivon_verify.checks.gates import validate_gate_manifest as validate_gate_manifest
from ordivon_verify.checks.docs import validate_document_registry as validate_document_registry

__all__ = [
    "main",
    "parse_args",
    "build_report",
    "determine_status",
    "print_human",
    "status_to_exit_code",
    "is_ordivon_native",
    "load_config",
    "validate_config",
    "run_check",
    "run_external_checker",
    "run_external_receipts",
    "scan_receipt_files",
    "validate_debt_ledger",
    "validate_gate_manifest",
    "validate_document_registry",
]
