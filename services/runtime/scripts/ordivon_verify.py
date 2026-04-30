#!/usr/bin/env python3
"""Ordivon Verify — Local read-only verification CLI.

Wraps existing governance checkers into a unified command surface.

Usage:
    uv run python scripts/ordivon_verify.py              # same as 'all'
    uv run python scripts/ordivon_verify.py all          # run all checks
    uv run python scripts/ordivon_verify.py receipts     # receipt integrity only
    uv run python scripts/ordivon_verify.py debt         # debt ledger only
    uv run python scripts/ordivon_verify.py gates        # gate manifest only
    uv run python scripts/ordivon_verify.py docs         # document registry only
    uv run python scripts/ordivon_verify.py all --json   # JSON output

External repo mode:
    uv run python scripts/ordivon_verify.py all --root /path/to/repo
    uv run python scripts/ordivon_verify.py receipts --root /path/to/repo --config /path/to/ordivon.verify.json
    uv run python scripts/ordivon_verify.py all --root /path/to/repo --mode advisory

Exit codes:
    0 = READY (all checks pass)
    1 = BLOCKED (one or more hard checks failed)
    2 = DEGRADED / NEEDS_REVIEW (warnings present, no hard failures)
    3 = config / usage error
    4 = tool runtime error

Never calls network, broker, API, or writes files. Read-only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

_BUILTIN_ROOT = Path(__file__).resolve().parents[1]

CHECKER_SCRIPTS = {
    "receipts": _BUILTIN_ROOT / "scripts" / "check_receipt_integrity.py",
    "debt": _BUILTIN_ROOT / "scripts" / "check_verification_debt.py",
    "gates": _BUILTIN_ROOT / "scripts" / "check_verification_manifest.py",
    "docs": _BUILTIN_ROOT / "scripts" / "check_document_registry.py",
}

CHECKER_LABELS = {
    "receipts": "Receipt Integrity",
    "debt": "Verification Debt",
    "gates": "Gate Manifest",
    "docs": "Document Registry",
}

ALL_CHECKS = ["receipts", "debt", "gates", "docs"]

# ── Config defaults ─────────────────────────────────────────────────────

DEFAULT_CONFIG: dict = {
    "schema_version": "0.1",
    "mode": "advisory",
    "receipt_paths": [],
    "output": "human",
}

# ── Receipt scan patterns (external mode) ──────────────────────────────

_SKIP_CONTEXT_WORDS = [
    "not run",
    "not separately executed",
    "skipped",
    "omitted",
    "will verify after commit",
    "pending verification",
    "not yet run",
    "addendum required",
    "pending",
]

_SEALED_PATTERN = re.compile(r"(?:Status:\s*\*?\*?SEALED|FULLY SEALED)", re.IGNORECASE)
_SKIP_NONE_PATTERN = re.compile(r"Skipped Verification:\s*None", re.IGNORECASE)
_CLEAN_TREE_PATTERN = re.compile(r"clean working tree", re.IGNORECASE)


def load_config(config_path: Path | None, root: Path) -> dict | None:
    """Load ordivon.verify.json, falling back to defaults."""
    if config_path:
        if not config_path.exists():
            return None
        try:
            with open(config_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    # Auto-detect
    auto = root / "ordivon.verify.json"
    if auto.exists():
        try:
            with open(auto) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def validate_config(cfg: dict) -> list[str]:
    """Validate config, return list of errors."""
    errors = []
    if not isinstance(cfg, dict):
        return ["config must be a JSON object"]
    version = cfg.get("schema_version", "")
    if version != "0.1":
        errors.append(f"unsupported schema_version: {version!r}")
    mode = cfg.get("mode", "")
    if mode and mode not in ("advisory", "standard", "strict"):
        errors.append(f"invalid mode: {mode!r}")
    return errors


def is_ordivon_native(root: Path) -> bool:
    """Check if root looks like an Ordivon-native repo."""
    return (root / "docs" / "governance" / "verification-debt-ledger.jsonl").exists() and (
        root / "docs" / "governance" / "verification-gate-manifest.json"
    ).exists()


# ── External receipt scanner ────────────────────────────────────────────


def _has_skip_context(text_window: str) -> bool:
    lower = text_window.lower()
    return any(w in lower for w in _SKIP_CONTEXT_WORDS)


def _has_skip_context_excluding_match(lines: list[str], match_line_idx: int) -> bool:
    """Check context excluding the matched line itself."""
    ctx_start = max(0, match_line_idx - 5)
    ctx_end = min(len(lines), match_line_idx + 5)
    lines_before = lines[ctx_start:match_line_idx]
    lines_after = lines[match_line_idx + 1 : ctx_end]
    context = "\n".join(lines_before + lines_after)
    return _has_skip_context(context)


def scan_receipt_files(receipt_paths: list[str], root: Path) -> tuple[list[str], int]:
    """Scan receipt files for contradictions. Returns (failures, count)."""
    failures: list[str] = []
    scanned = 0
    for rp in receipt_paths:
        scan_dir = root / rp
        if not scan_dir.is_dir():
            continue
        for md_file in sorted(scan_dir.rglob("*.md")):
            scanned += 1
            try:
                content = md_file.read_text()
            except Exception:
                continue
            lines = content.split("\n")
            rel = str(md_file.relative_to(root))
            for i, line in enumerate(lines, 1):
                idx = i - 1  # 0-indexed

                if _SEALED_PATTERN.search(line) and _has_skip_context_excluding_match(lines, idx):
                    failures.append(f"{rel}:{i}: claims SEALED but nearby text suggests incomplete verification")
                elif _SKIP_NONE_PATTERN.search(line) and _has_skip_context_excluding_match(lines, idx):
                    failures.append(f"{rel}:{i}: claims 'Skipped: None' but nearby text suggests gate was not run")
                elif _CLEAN_TREE_PATTERN.search(line):
                    ctx_start = max(0, idx - 5)
                    ctx_end = min(len(lines), idx + 5)
                    ctx_text = "\n".join(lines[ctx_start:ctx_end])
                    safe = re.compile(r"tracked working tree clean|tracked clean", re.IGNORECASE)
                    if not safe.search(ctx_text):
                        failures.append(
                            f"{rel}:{i}: claims 'clean working tree' — should say 'Tracked working tree clean' if untracked residue exists"
                        )

    return failures, scanned


# ── Check runners ───────────────────────────────────────────────────────


def run_check(check_id: str, root: Path | None = None) -> dict:
    """Run a single checker script and return its result dict."""
    script = CHECKER_SCRIPTS[check_id]
    cmd = [sys.executable, str(script)]
    cwd = str(root) if root else str(_BUILTIN_ROOT)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=cwd,
        )
        return {
            "id": check_id,
            "label": CHECKER_LABELS[check_id],
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except subprocess.TimeoutExpired:
        return {
            "id": check_id,
            "label": CHECKER_LABELS[check_id],
            "status": "FAIL",
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Checker timed out: {check_id}",
        }
    except Exception as exc:
        return {
            "id": check_id,
            "label": CHECKER_LABELS[check_id],
            "status": "FAIL",
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Runtime error: {exc}",
        }


def run_external_receipts(receipt_paths: list[str], root: Path) -> dict:
    """Run receipt scan on external repo using built-in scanner."""
    failures, scanned = scan_receipt_files(receipt_paths, root)
    if failures:
        return {
            "id": "receipts",
            "label": "Receipt Integrity",
            "status": "FAIL",
            "exit_code": 1,
            "stdout": "",
            "stderr": "\n".join(failures),
        }
    return {
        "id": "receipts",
        "label": "Receipt Integrity",
        "status": "PASS",
        "exit_code": 0,
        "stdout": f"{scanned} receipt(s) scanned, 0 contradictions",
        "stderr": "",
    }


def run_external_checker(
    check_id: str,
    root: Path,
    mode: str,
) -> dict:
    """Run a checker against an external repo.

    For debt/gates/docs: if the expected metadata files exist at the target
    root, run the checker. Otherwise, return WARN (advisory) or FAIL (strict).
    """
    meta_files = {
        "debt": root / "docs" / "governance" / "verification-debt-ledger.jsonl",
        "gates": root / "docs" / "governance" / "verification-gate-manifest.json",
        "docs": root / "docs" / "governance" / "document-registry.jsonl",
    }
    need = meta_files.get(check_id)
    if need and need.exists():
        return run_check(check_id, root=root)

    label = CHECKER_LABELS[check_id]
    if mode == "strict":
        return {
            "id": check_id,
            "label": label,
            "status": "FAIL",
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Missing required file: {need}",
        }
    # advisory / standard → warning, not failure
    return {
        "id": check_id,
        "label": label,
        "status": "WARN",
        "exit_code": -1,
        "stdout": "",
        "stderr": f"Not configured: {need} not found",
    }


# ── Report building ─────────────────────────────────────────────────────


def determine_status(results: list[dict]) -> str:
    """Determine overall status from check results."""
    has_fail = any(r["status"] == "FAIL" for r in results)
    has_warn = any(r["status"] == "WARN" for r in results)
    if has_fail:
        return "BLOCKED"
    if has_warn:
        return "DEGRADED"
    return "READY"


def build_report(results: list[dict], mode: str, warnings: list[str] | None = None) -> dict:
    """Build the full report dict (for JSON output)."""
    status = determine_status(results)
    hard_failures = [
        {"id": r["id"], "label": r["label"], "stderr": r["stderr"]} for r in results if r["status"] == "FAIL"
    ]
    warn_entries = [
        {"id": r["id"], "label": r.get("label", r["id"]), "message": r.get("stderr", "")}
        for r in results
        if r["status"] == "WARN"
    ]
    if warnings:
        for w in warnings:
            warn_entries.append({"id": "config", "label": "Config", "message": w})
    return {
        "tool": "ordivon-verify",
        "schema_version": "0.1",
        "status": status,
        "mode": mode,
        "checks": [
            {
                "id": r["id"],
                "status": r["status"],
                "exit_code": r["exit_code"],
                "summary": (r["stdout"].split("\n")[-1] if r["stdout"] else (r["stderr"] or "no output")),
            }
            for r in results
        ],
        "hard_failures": hard_failures,
        "warnings": warn_entries,
    }


def print_human(results: list[dict], warnings: list[str] | None = None) -> None:
    """Print human-readable report."""
    status = determine_status(results)
    print("ORDIVON VERIFY")
    print(f"Status: {status}")
    print("Checks:")
    for r in results:
        if r["status"] == "PASS":
            icon = "\u2713"
        elif r["status"] == "WARN":
            icon = "\u26a0"
        else:
            icon = "\u2717"
        print(f"  - {r['label'].lower()}: {icon} {r['status']}")
    if warnings:
        print("\nConfig warnings:")
        for w in warnings:
            print(f"  - {w}")
    print()


def status_to_exit_code(status: str) -> int:
    """Map status string to exit code."""
    if status == "READY":
        return 0
    if status == "BLOCKED":
        return 1
    if status in ("DEGRADED", "NEEDS_REVIEW"):
        return 2
    return 1


# ── CLI argument parsing ────────────────────────────────────────────────


def _parse_unknown(parser, unknown: list[str], ns) -> None:
    """Handle unknown args: --json, --root, --config, --mode."""
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
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="ordivon-verify",
        description="Ordivon Verify — local read-only verification CLI",
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


# ── Main ────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns exit code 0-4."""
    try:
        args = parse_args(argv)
    except SystemExit:
        return 3

    command = args.command or "all"

    # Determine root and mode
    root = Path(args.root).resolve() if args.root else _BUILTIN_ROOT
    if not root.is_dir():
        print(f"Root directory not found: {root}", file=sys.stderr)
        return 3

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path, root)

    mode = args.mode or (config.get("mode", "") if config else "")
    if not mode:
        # Auto-detect: Ordivon-native = standard, external = advisory
        mode = "standard" if is_ordivon_native(root) else "advisory"

    if mode not in ("advisory", "standard", "strict"):
        print(f"Invalid mode: {mode}", file=sys.stderr)
        return 3

    # Validate config if provided
    config_warnings: list[str] = []
    if config:
        config_errors = validate_config(config)
        if config_errors:
            print(f"Config error: {'; '.join(config_errors)}", file=sys.stderr)
            return 3
    else:
        # No config loaded — use empty defaults
        config = {}

    # Determine which checks to run
    if command == "all":
        check_ids = list(ALL_CHECKS)
    elif command in CHECKER_SCRIPTS:
        check_ids = [command]
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        return 3

    try:
        # Check if this is an external repo (not Ordivon-native)
        native = is_ordivon_native(root)

        if native and not args.root:
            # Native Ordivon mode — use existing checkers as before
            results = [run_check(cid) for cid in check_ids]
        else:
            # External mode — use built-in scanner for receipts,
            # conditional checker for debt/gates/docs
            results = []
            for cid in check_ids:
                if cid == "receipts":
                    receipt_paths = config.get("receipt_paths", []) if config else []
                    if receipt_paths:
                        results.append(run_external_receipts(receipt_paths, root))
                    else:
                        results.append({
                            "id": "receipts",
                            "label": "Receipt Integrity",
                            "status": "WARN" if mode != "strict" else "FAIL",
                            "exit_code": -1,
                            "stdout": "",
                            "stderr": "No receipt_paths configured",
                        })
                elif cid == "debt":
                    results.append(run_external_checker("debt", root, mode))
                elif cid == "gates":
                    results.append(run_external_checker("gates", root, mode))
                elif cid == "docs":
                    results.append(run_external_checker("docs", root, mode))

        status = determine_status(results)

        if args.json:
            report = build_report(results, mode, warnings=config_warnings or None)
            print(json.dumps(report, indent=2))
        else:
            print_human(results, warnings=config_warnings or None)

        return status_to_exit_code(status)
    except Exception as exc:
        print(f"Runtime error: {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
