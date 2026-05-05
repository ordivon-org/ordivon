"""Ordivon Verify — CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ordivon_verify.config import is_ordivon_native, load_config, validate_config
from ordivon_verify.report import build_report, determine_status, print_human, status_to_exit_code
from ordivon_verify.runner import (
    _ensure_all_checks,
    _get_all_gate_ids,
    ALL_CHECKS,
    _get_entry,
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
    check_parser = sub.add_parser("check", help="Run all checks against a target root")
    check_parser.add_argument("target", nargs="?", help="Project root to verify")
    run_parser = sub.add_parser("run", help="Run a specific checker by gate_id")
    run_parser.add_argument("gate_id", help="Checker gate_id (e.g. receipt_integrity)")
    # Legacy subcommands
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
    target_root = getattr(args, "target", None) if command == "check" else None
    root = Path(args.root or target_root).resolve() if (args.root or target_root) else _BUILTIN_ROOT
    if not root.is_dir():
        print(f"Root directory not found: {root}", file=sys.stderr)
        return 3

    config_path = Path(args.config) if args.config else None
    if config_path and not config_path.exists():
        print(f"Config file not found: {config_path}", file=sys.stderr)
        return 3
    config = load_config(config_path, root)
    if config_path and config is None:
        print(f"Config parse error: {config_path}", file=sys.stderr)
        return 3
    if config is None:
        auto_config_path = root / "ordivon.verify.json"
        if auto_config_path.exists():
            print(f"Config parse error: {auto_config_path}", file=sys.stderr)
            return 3

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

    if command in ("all", "check"):
        _ensure_all_checks()
        check_ids = list(ALL_CHECKS)
    elif command == "run":
        gate_id = getattr(args, "gate_id", None)
        if not gate_id:
            print("Missing gate_id. Usage: ordivon-verify run <gate_id>", file=sys.stderr)
            return 3
        entry = _get_entry(gate_id)
        if not entry:
            available = ", ".join(_get_all_gate_ids())
            print(f"Unknown checker: {gate_id}", file=sys.stderr)
            print(f"Available: {available}", file=sys.stderr)
            return 3
        check_ids = [gate_id]
    elif command in ("receipts", "debt", "gates", "docs"):
        check_ids = [command]
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        return 3

    try:
        native = is_ordivon_native(root)
        if command in ("all", "check") and not native:
            check_ids = ["receipts", "debt", "gates", "docs"]
        if native and not (args.root or target_root):
            results = [_runner.run_check(cid) for cid in check_ids]
        elif native:
            results = [_runner.run_check(cid, root) for cid in check_ids]
        else:
            results = []
            for cid in check_ids:
                if cid == "receipts":
                    receipt_paths = config.get("receipt_paths", []) if config else []
                    if receipt_paths:
                        results.append(_runner.run_external_receipts(receipt_paths, root))
                    else:
                        receipts_required = mode in ("standard", "strict")
                        results.append({
                            "id": "receipts",
                            "label": "Receipt Integrity",
                            "status": "FAIL" if receipts_required else "WARN",
                            "exit_code": -1,
                            "stdout": "",
                            "stderr": "No receipt_paths configured",
                            "missing_evidence": True,
                            "next_action": "Configure receipt_paths so Ordivon can verify agent work claims.",
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
