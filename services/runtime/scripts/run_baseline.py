#!/usr/bin/env python3
"""Ordivon Verification Baseline — auto-discovery edition.

Replaces the manually-maintained gate lists. Discovers checkers from
the checkers/ directory structure, runs them, and produces a unified
pass/fail summary.

Adding a checker: create checkers/<name>/ with CHECKER.md + run.py.
That's it. No manifest edit. No baseline edit. No runner dict edit.

Usage:
    python scripts/run_baseline.py                     # full profile
    python scripts/run_baseline.py --pr-fast           # pr-fast profile
    python scripts/run_baseline.py --manifest          # dump auto-generated manifest
    python scripts/run_baseline.py --sync              # sync bundled checkers
"""

from __future__ import annotations

import importlib.util
import json
import logging
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Ensure src/ is importable and scripts/ordivon_verify.py does NOT shadow the package.
# We need to force the package path before any import that resolves 'ordivon_verify'.
_src = ROOT / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

# Import the registry WITHOUT going through scripts/ which has ordivon_verify.py
# that shadows the ordivon_verify package.
import importlib

# Create the full package chain in sys.modules so @dataclass works
_ormod = type(sys)("ordivon_verify")
_ormod.__path__ = [str(_src / "ordivon_verify")]
_ormod.__package__ = "ordivon_verify"
sys.modules["ordivon_verify"] = _ormod

spec = importlib.util.spec_from_file_location(
    "ordivon_verify.checker_registry",
    _src / "ordivon_verify" / "checker_registry.py",
    submodule_search_locations=[str(_src / "ordivon_verify")],
)
_checker_registry = importlib.util.module_from_spec(spec)
sys.modules["ordivon_verify.checker_registry"] = _checker_registry
spec.loader.exec_module(_checker_registry)

discover_checkers = _checker_registry.discover_checkers
generate_manifest = _checker_registry.generate_manifest
sync_bundled_checkers = _checker_registry.sync_bundled_checkers
bump_checker_use = _checker_registry.bump_checker_use
bump_checker_result = _checker_registry.bump_checker_result
run_document_curator = _checker_registry.run_document_curator
CheckerEntry = _checker_registry.CheckerEntry

logger = logging.getLogger(__name__)


# ── Gate result ─────────────────────────────────────────────────────

@dataclass
class GateResult:
    name: str
    gate_class: str
    layer: str
    passed: bool
    output: str
    exit_code: int


@dataclass
class BaselineSummary:
    results: list[GateResult] = field(default_factory=list)

    @property
    def hard_passed(self) -> int:
        return sum(1 for r in self.results if r.gate_class == "hard" and r.passed)

    @property
    def hard_total(self) -> int:
        return sum(1 for r in self.results if r.gate_class == "hard")

    @property
    def hard_failed(self) -> int:
        return self.hard_total - self.hard_passed

    @property
    def overall_ready(self) -> bool:
        return self.hard_failed == 0


# ── Runner ──────────────────────────────────────────────────────────

def _run_checker_subprocess(entry: CheckerEntry, python: str) -> GateResult:
    """Run a checker as subprocess by its file_path."""
    import os as _os
    env = {**_os.environ, "PYTHONPATH": f"src{_os.pathsep}" + _os.environ.get("PYTHONPATH", "")}
    try:
        result = subprocess.run(
            [python, str(entry.file_path)],
            capture_output=True,
            text=True,
            timeout=entry.timeout,
            cwd=str(ROOT),
            env=env,
        )
        output = (result.stdout + result.stderr).strip()
        exit_code = result.returncode
        passed = exit_code == 0 if entry.hardness == "hard" else True
        return GateResult(
            name=entry.display_name,
            gate_class=entry.hardness,
            layer=entry.layer,
            passed=passed,
            output=output[:500],
            exit_code=exit_code,
        )
    except subprocess.TimeoutExpired:
        return GateResult(
            name=entry.display_name,
            gate_class=entry.hardness,
            layer=entry.layer,
            passed=False,
            output=f"TIMEOUT ({entry.timeout}s)",
            exit_code=-1,
        )
    except Exception as exc:
        return GateResult(
            name=entry.display_name,
            gate_class=entry.hardness,
            layer=entry.layer,
            passed=False,
            output=str(exc),
            exit_code=-1,
        )


def _layer_sort_key(layer: str) -> tuple[float, str]:
    """Sort L3, L4.5A, L9F, L10A in numeric layer order."""
    match = re.match(r"^L?(\d+(?:\.\d+)?)(.*)$", str(layer))
    if not match:
        return (9999.0, str(layer))
    return (float(match.group(1)), match.group(2))


def run_all(profile: str = "full", skip_side_effects: bool = False) -> BaselineSummary:
    """Auto-discover and run all registered checkers for a profile.

    If skip_side_effects is True, checkers with side_effects=True in their
    CHECKER.md are excluded. Use for read-only CI runs that must not modify
    any JSONL ledgers or state files.
    """
    summary = BaselineSummary()
    python = sys.executable

    entries = discover_checkers()
    if not entries:
        print("⚠ No checkers discovered. Run --sync first.")
        return summary

    # Filter by profile
    active = [e for e in entries.values() if profile in e.profiles]
    # Filter out side-effect checkers in read-only mode
    if skip_side_effects:
        skipped = [e for e in active if e.side_effects]
        active = [e for e in active if not e.side_effects]
        if skipped:
            print(f"ℹ Read-only mode: skipped {len(skipped)} state-updating checker(s): "
                  f"{', '.join(e.gate_id for e in skipped)}")
    # Sort by layer
    active.sort(key=lambda e: _layer_sort_key(e.layer))

    for entry in active:
        if not entry.file_path:
            continue

        bump_checker_use(entry.gate_id)
        result = _run_checker_subprocess(entry, python)
        bump_checker_result(entry.gate_id, result.passed)
        summary.results.append(result)

    return summary


# ── Output ──────────────────────────────────────────────────────────

def print_summary(summary: BaselineSummary) -> None:
    print("\n" + "=" * 60)
    print("ORDIVON VERIFICATION BASELINE (auto-discovered)")
    print(f"Checkers: {len(summary.results)} registered")
    print("=" * 60)
    for r in summary.results:
        symbol = "✅" if r.passed else "❌"
        tag = f"[{r.gate_class.upper()}]"
        print(f"  {symbol} {tag:15s} {r.name:45s} (L{r.layer})")
        if not r.passed or r.exit_code != 0:
            preview = r.output[:200].replace("\n", " | ")
            print(f"     {'':15s} → {preview}")
    print()
    print("=" * 60)
    print(f"  Hard gates:       {summary.hard_passed}/{summary.hard_total} PASS")
    print(f"  OVERALL: {'READY' if summary.overall_ready else 'BLOCKED'}")
    print()


def print_manifest_json() -> None:
    manifest = generate_manifest()
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


# ── Main ────────────────────────────────────────────────────────────

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Ordivon Verification Baseline (auto-discovery)")
    parser.add_argument("--pr-fast", action="store_true", help="Run PR-fast gates only")
    parser.add_argument("--read-only", action="store_true", help="Skip state-updating checkers (no JSONL writes)")
    parser.add_argument("--manifest", action="store_true", help="Dump auto-generated manifest JSON")
    parser.add_argument("--sync", action="store_true", help="Sync bundled checkers")
    parser.add_argument("--curator", action="store_true", help="Run document curator (detect stale docs)")
    args = parser.parse_args()

    if args.curator:
        result = run_document_curator()
        print(f"Documents: {result.get('total',0)} total, {result.get('fresh',0)} fresh")
        print(f"Stale: {len(result.get('stale',[]))} normal, {len(result.get('critical_stale',[]))} critical")
        for doc in result.get('critical_stale', []):
            print(f"  CRITICAL: {doc['doc_id']} — {doc['age_days']}d old (window={doc['window_days']}d)")
        for doc in result.get('stale', []):
            print(f"  stale: {doc['doc_id']} — {doc['age_days']}d old")
        return 0

    if args.sync:
        result = sync_bundled_checkers()
        print(f"Synced: {len(result['copied'])} new, {len(result['updated'])} updated, "
              f"{result['skipped']} unchanged, {result['total_bundled']} total")
        return 0

    if args.manifest:
        print_manifest_json()
        return 0

    profile = "pr-fast" if args.pr_fast else "full"
    summary = run_all(profile, skip_side_effects=args.read_only)
    print_summary(summary)
    return 0 if summary.overall_ready else 1


if __name__ == "__main__":
    sys.exit(main())
