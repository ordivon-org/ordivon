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

DISCLAIMER = "READY means selected checks passed; it does not authorize execution."

_FAILURE_ADVICE = {
    "SEALED": (
        "Unverified work was called 'sealed'. Fix the receipt to reflect actual "
        "verification state, or complete the missing verification."
    ),
    "Skipped: None": (
        "Receipt claims no verification was skipped, but evidence shows gate(s) "
        "were not run. Correct the receipt or run the missing checks."
    ),
    "clean working tree": (
        "Receipt claims 'clean working tree' without acknowledging untracked "
        "residue. Either remove residue or qualify as 'Tracked working tree clean'."
    ),
}

_WARN_ADVICE = {
    "debt": "Add verification-debt-ledger.jsonl when moving from advisory to standard mode.",
    "gates": "Add verification-gate-manifest.json before strict CI use.",
    "docs": "Add document-registry.jsonl for document governance.",
}

# ── Receipt scan patterns ──────────────────────────────────────────────

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
    if config_path:
        if not config_path.exists():
            return None
        try:
            with open(config_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    auto = root / "ordivon.verify.json"
    if auto.exists():
        try:
            with open(auto) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def validate_config(cfg: dict) -> list[str]:
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
    return (root / "docs" / "governance" / "verification-debt-ledger.jsonl").exists() and (
        root / "docs" / "governance" / "verification-gate-manifest.json"
    ).exists()


# ── External receipt scanner ────────────────────────────────────────────


def _has_skip_context_excluding_match(lines: list[str], match_line_idx: int) -> bool:
    ctx_start = max(0, match_line_idx - 5)
    ctx_end = min(len(lines), match_line_idx + 5)
    lines_before = lines[ctx_start:match_line_idx]
    lines_after = lines[match_line_idx + 1 : ctx_end]
    context = "\n".join(lines_before + lines_after)
    lower = context.lower()
    return any(w in lower for w in _SKIP_CONTEXT_WORDS)


def _classify_failure(reason: str) -> str:
    """Return a human-readable classification for a receipt failure."""
    if "SEALED" in reason:
        return "receipt_contradiction"
    if "Skipped: None" in reason:
        return "skipped_verification_claim"
    if "clean working tree" in reason:
        return "clean_tree_overclaim"
    return "receipt_contradiction"


def _why_it_matters(reason: str) -> str:
    if "SEALED" in reason:
        return "Unverified work must not be called sealed."
    if "Skipped: None" in reason:
        return "Skipped verification must be registered, not claimed as 'None'."
    if "clean working tree" in reason:
        return "Untracked residue contradicts 'clean working tree' claim."
    return "Receipt language contradicts evidence."


def _next_action(reason: str) -> str:
    for key, advice in _FAILURE_ADVICE.items():
        if key in reason:
            return advice
    return "Review the receipt and correct contradictory claims."


def scan_receipt_files(receipt_paths: list[str], root: Path) -> tuple[list[dict], int]:
    """Scan receipt files. Returns (structured_failures, scanned_count)."""
    failures: list[dict] = []
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
                idx = i - 1
                if _SEALED_PATTERN.search(line) and _has_skip_context_excluding_match(lines, idx):
                    reason = "Status SEALED but nearby text suggests incomplete verification"
                    failures.append({
                        "id": _classify_failure(reason),
                        "file": rel,
                        "line": i,
                        "reason": reason,
                        "why_it_matters": _why_it_matters(reason),
                        "next_action": _next_action(reason),
                    })
                elif _SKIP_NONE_PATTERN.search(line) and _has_skip_context_excluding_match(lines, idx):
                    reason = "Claims 'Skipped: None' but nearby text suggests gate was not run"
                    failures.append({
                        "id": _classify_failure(reason),
                        "file": rel,
                        "line": i,
                        "reason": reason,
                        "why_it_matters": _why_it_matters(reason),
                        "next_action": _next_action(reason),
                    })
                elif _CLEAN_TREE_PATTERN.search(line):
                    ctx_start = max(0, idx - 5)
                    ctx_end = min(len(lines), idx + 5)
                    ctx_text = "\n".join(lines[ctx_start:ctx_end])
                    safe = re.compile(r"tracked working tree clean|tracked clean", re.IGNORECASE)
                    if not safe.search(ctx_text):
                        reason = "Claims 'clean working tree' without acknowledging untracked residue"
                        failures.append({
                            "id": _classify_failure(reason),
                            "file": rel,
                            "line": i,
                            "reason": reason,
                            "why_it_matters": _why_it_matters(reason),
                            "next_action": _next_action(reason),
                        })
    return failures, scanned


# ── Check runners ───────────────────────────────────────────────────────


def run_check(check_id: str, root: Path | None = None) -> dict:
    script = CHECKER_SCRIPTS[check_id]
    cmd = [sys.executable, str(script)]
    cwd = str(root) if root else str(_BUILTIN_ROOT)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=cwd)
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
    failures, scanned = scan_receipt_files(receipt_paths, root)
    if failures:
        return {
            "id": "receipts",
            "label": "Receipt Integrity",
            "status": "FAIL",
            "exit_code": 1,
            "stdout": "",
            "stderr": f"{len(failures)} contradiction(s) in {scanned} receipt(s)",
            "failures": failures,
        }
    return {
        "id": "receipts",
        "label": "Receipt Integrity",
        "status": "PASS",
        "exit_code": 0,
        "stdout": f"{scanned} receipt(s) scanned, 0 contradictions",
        "stderr": "",
    }


def run_external_checker(check_id: str, root: Path, mode: str) -> dict:
    meta_files = {
        "debt": root / "docs" / "governance" / "verification-debt-ledger.jsonl",
        "gates": root / "docs" / "governance" / "verification-gate-manifest.json",
        "docs": root / "docs" / "governance" / "document-registry.jsonl",
    }
    need = meta_files.get(check_id)
    if need and need.exists():
        return run_check(check_id, root=root)

    label = CHECKER_LABELS[check_id]
    msg = f"Not configured: {need} not found"
    advice = _WARN_ADVICE.get(check_id, f"Configure {check_id} when ready.")
    if mode == "strict":
        return {
            "id": check_id,
            "label": label,
            "status": "FAIL",
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Missing required file: {need}",
        }
    return {
        "id": check_id,
        "label": label,
        "status": "WARN",
        "exit_code": -1,
        "stdout": "",
        "stderr": msg,
        "next_action": advice,
    }


# ── Report building ─────────────────────────────────────────────────────


def determine_status(results: list[dict]) -> str:
    has_fail = any(r["status"] == "FAIL" for r in results)
    has_warn = any(r["status"] == "WARN" for r in results)
    if has_fail:
        return "BLOCKED"
    if has_warn:
        return "DEGRADED"
    return "READY"


def build_report(results: list[dict], mode: str, root: str, config_path: str | None) -> dict:
    status = determine_status(results)
    hard_failures = []
    warn_entries = []

    for r in results:
        if r["status"] == "FAIL":
            sub_failures = r.get("failures", [])
            if sub_failures:
                for sf in sub_failures:
                    hard_failures.append({
                        "id": sf["id"],
                        "check": r["id"],
                        "file": sf["file"],
                        "line": sf.get("line", 0),
                        "reason": sf["reason"],
                        "why_it_matters": sf["why_it_matters"],
                        "next_action": sf["next_action"],
                    })
            else:
                hard_failures.append({
                    "id": r["id"],
                    "check": r["id"],
                    "reason": r.get("stderr", "Checker failed"),
                    "why_it_matters": "A hard verification gate failed.",
                    "next_action": f"Review {r['label'].lower()} checker output.",
                })
        elif r["status"] == "WARN":
            warn_entries.append({
                "id": r["id"],
                "check": r["id"],
                "reason": r.get("stderr", "Warning"),
                "next_action": r.get("next_action", f"Configure {r['label'].lower()} when ready."),
            })

    return {
        "tool": "ordivon-verify",
        "schema_version": "0.1",
        "status": status,
        "mode": mode,
        "root": root,
        "config": config_path,
        "checks": [
            {
                "id": r["id"],
                "status": r["status"],
                "severity": _severity(r["status"]),
                "summary": (r["stdout"].split("\n")[-1] if r["stdout"] else (r.get("stderr", "") or "no output")),
                "exit_code": r["exit_code"],
            }
            for r in results
        ],
        "hard_failures": hard_failures,
        "warnings": warn_entries,
        "disclaimer": DISCLAIMER,
    }


def _severity(status: str) -> str:
    if status == "FAIL":
        return "hard"
    if status == "WARN":
        return "warning"
    return "info"


def print_human(results: list[dict], mode: str, root: str, config_path: str | None) -> None:
    status = determine_status(results)
    print("ORDIVON VERIFY")
    print(f"Status:  {status}")
    print(f"Mode:    {mode}")
    print(f"Root:    {root}")
    if config_path:
        print(f"Config:  {config_path}")
    print()

    print("Checks:")
    for r in results:
        if r["status"] == "PASS":
            icon, label_status = "\u2713", ""
        elif r["status"] == "WARN":
            icon, label_status = "\u26a0", " (not configured)"
        else:
            icon, label_status = "\u2717", ""
        print(f"  {r['label'].lower()}: {icon} {r['status']}{label_status}")

    # Hard failures
    failures = [r for r in results if r["status"] == "FAIL"]
    if failures:
        print("\nHard failures:")
        for f in failures:
            sub = f.get("failures", [])
            if sub:
                for sf in sub:
                    print(f"  {sf['id']}")
                    print(f"    File:    {sf['file']}")
                    print(f"    Line:    {sf.get('line', '?')}")
                    print(f"    Reason:  {sf['reason']}")
                    print(f"    Why:     {sf['why_it_matters']}")
                    print(f"    Action:  {sf['next_action']}")
                    print()
            else:
                print(f"  {f['id']}")
                reason = f.get("stderr", "Checker failed")
                print(f"    Reason:  {reason}")
                print()

    # Warnings
    warns = [r for r in results if r["status"] == "WARN"]
    if warns:
        print("Warnings:")
        for w in warns:
            print(f"  {w['id']}")
            print(f"    Reason:  {w.get('stderr', 'Warning')}")
            na = w.get("next_action", "")
            if na:
                print(f"    Action:  {na}")
            print()

    # Next suggested actions
    if failures or warns:
        print("Next suggested action:")
        if failures:
            print("  - Fix hard failures above. They block CI / trust.")
        if warns:
            print("  - Address warnings before moving to a stricter mode.")
        print()

    print(DISCLAIMER)
    print()


def status_to_exit_code(status: str) -> int:
    return {"READY": 0, "BLOCKED": 1, "DEGRADED": 2, "NEEDS_REVIEW": 2}.get(status, 1)


# ── CLI argument parsing ────────────────────────────────────────────────


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
            results = [run_check(cid) for cid in check_ids]
        else:
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
                else:
                    results.append(run_external_checker(cid, root, mode))

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
