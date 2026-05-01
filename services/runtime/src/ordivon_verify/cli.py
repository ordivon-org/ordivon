"""Ordivon Verify — CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ordivon_verify.config import is_ordivon_native, load_config, validate_config
from ordivon_verify.report import build_report, determine_status, print_human, status_to_exit_code
from ordivon_verify.runner import (
    ALL_CHECKS,
    CHECKER_SCRIPTS,
)
from ordivon_verify import runner as _runner

_BUILTIN_ROOT = Path(__file__).resolve().parents[2]


def _parse_unknown(parser, unknown: list[str], ns) -> None:
    i = 0
    while i < len(unknown):
        u = unknown[i]
        if u == "--json":
            ns.json = True
        elif u == "--root":
            i += 1
            if i >= len(unknown):
                parser.error("--root requires a path argument")
            ns.root = unknown[i]
        elif u == "--config":
            i += 1
            if i >= len(unknown):
                parser.error("--config requires a path argument")
            ns.config = unknown[i]
        elif u == "--mode":
            i += 1
            if i >= len(unknown):
                parser.error("--mode requires a value (advisory, standard, strict)")
            ns.mode = unknown[i]
        else:
            parser.error(f"unrecognized arguments: {u}")
        i += 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ordivon-verify", description="Ordivon Verify — local read-only verification CLI"
    )
    sub = parser.add_subparsers(dest="command", title="commands")
    sub.add_parser("all", help="Run all checks (receipts + debt + gates + docs)")
    sub.add_parser("receipts", help="Scan receipts for contradictions")
    sub.add_parser("debt", help="Check debt ledger invariants")
    sub.add_parser("gates", help="Verify gate manifest integrity")
    sub.add_parser("docs", help="Check document registry + semantic safety")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    parser.add_argument("--root", type=str, default=None, help="Project root directory")
    parser.add_argument("--config", type=str, default=None, help="Path to ordivon.verify.json")
    parser.add_argument("--mode", type=str, default=None, help="Mode: advisory, standard, strict")
    known, unknown = parser.parse_known_args(argv)
    if unknown:
        _parse_unknown(parser, unknown, known)
    return known


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
    except SystemExit:
        return 3

    command = args.command or "all"
    root = Path(args.root).resolve() if args.root else _BUILTIN_ROOT
    if not root.is_dir():
        print(f"Root directory not found: {root}", file=sys.stderr)
        return 3

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path, root)
    mode = args.mode or (config.get("mode", "") if config else "")
    if not mode:
        mode = "standard" if is_ordivon_native(root) else "advisory"
    if mode not in ("advisory", "standard", "strict"):
        print(f"Invalid mode: {mode}", file=sys.stderr)
        return 3

    if config:
        config_errors = validate_config(config)
        if config_errors:
            print(f"Config error: {'; '.join(config_errors)}", file=sys.stderr)
            return 3
    else:
        config = {}

    if command == "all":
        check_ids = list(ALL_CHECKS)
    elif command in CHECKER_SCRIPTS:
        check_ids = [command]
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        return 3

    try:
        native = is_ordivon_native(root)
        if native and not args.root:
            results = [_runner.run_check(cid) for cid in check_ids]
        else:
            results = []
            for cid in check_ids:
                if cid == "receipts":
                    receipt_paths = config.get("receipt_paths", []) if config else []
                    if receipt_paths:
                        results.append(_runner.run_external_receipts(receipt_paths, root))
                    else:
                        results.append({
                            "id": "receipts",
                            "label": "Receipt Integrity",
                            "status": "WARN" if mode != "strict" else "FAIL",
                            "exit_code": -1,
                            "stdout": "",
                            "stderr": "No receipt_paths configured",
                        })
                else:
                    results.append(_runner.run_external_checker(cid, root, mode, config))

        status = determine_status(results)
        root_str = str(root)
        cfg_str = str(config_path) if config_path else None

        if args.json:
            report = build_report(results, mode, root_str, cfg_str)
            print(json.dumps(report, indent=2))
        else:
            print_human(results, mode, root_str, cfg_str)

        return status_to_exit_code(status)
    except Exception as exc:
        print(f"Runtime error: {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
