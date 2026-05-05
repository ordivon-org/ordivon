#!/usr/bin/env python3
"""Ordivon Verification Baseline Runner — auto-discovery edition.

Replaces the manually-maintained gate lists in run_verification_baseline.py.
Runs every checker registered via @register_checker for the requested profile.

Key difference from the old baseline:
- Gate list is auto-discovered from the checker registry — no manual list.
- Adding a checker script with @register_checker is sufficient.
- The manifest JSON can be regenerated from the registry at any time.

Usage:
    uv run python scripts/run_verification_baseline_v2.py              # full
    uv run python scripts/run_verification_baseline_v2.py --pr-fast    # pr-fast
    uv run python scripts/run_verification_baseline_v2.py --manifest   # dump manifest
"""

from __future__ import annotations

import importlib
import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

# Ensure src/ordivon_verify is importable — scripts/ordivon_verify.py
# shadows the package in the scripts directory.
_src = ROOT / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

logger = logging.getLogger(__name__)


# ── Gate result (unchanged from original baseline) ──────────────────

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


# ── Discovery ───────────────────────────────────────────────────────

def _discover_checker_modules() -> list[str]:
    """Find all .py files in scripts/ that contain @register_checker.

    Uses the same AST-scan approach as Hermes Agent's _module_registers_tools().
    Scans for top-level ``@register_checker(...)`` decorator calls without
    executing any code.
    """
    import ast

    modules = []
    for path in sorted(SCRIPTS.glob("check_*.py")):
        if path.name in ("__init__.py",):
            continue
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, SyntaxError):
            continue

        # Look for @register_checker at module level
        has_decorator = False
        for stmt in tree.body:
            if isinstance(stmt, ast.FunctionDef):
                for dec in stmt.decorator_list:
                    if isinstance(dec, ast.Call) and hasattr(dec.func, 'id'):
                        if dec.func.id == 'register_checker':
                            has_decorator = True
                            break
                    elif isinstance(dec, ast.Name) and dec.id == 'register_checker':
                        has_decorator = True
                        break
            if has_decorator:
                break

        if has_decorator:
            modules.append(f"scripts.{path.stem}")

    return modules


def _import_and_collect() -> tuple[list, list]:
    """Import all checker modules and collect registered entries.

    Returns (hard_gates, other_gates) where each entry is a CheckerEntry
    from the registry.
    """
    import importlib.util
    from ordivon_verify.registry import registry

    modules = _discover_checker_modules()
    for mod_name in modules:
        try:
            # Modules are discovered as "scripts.check_xxx" — strip the prefix
            stem = mod_name.split(".")[-1] if "." in mod_name else mod_name
            path = SCRIPTS / f"{stem}.py"
            spec = importlib.util.spec_from_file_location(mod_name, path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
        except Exception as exc:
            logger.warning("Could not import checker module %s: %s", mod_name, exc)

    all_entries = registry.get_all()
    hard = [e for e in all_entries if e.hardness == "hard"]
    other = [e for e in all_entries if e.hardness != "hard"]
    return hard, other


# ── Runner ──────────────────────────────────────────────────────────

def _run_checker_subprocess(entry, python: str) -> GateResult:
    """Run a checker as a subprocess by its file path."""
    try:
        result = subprocess.run(
            [python, str(entry.file_path)],
            capture_output=True,
            text=True,
            timeout=entry.timeout,
            cwd=str(ROOT),
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


def run_all(profile: str = "full") -> BaselineSummary:
    """Auto-discover and run all registered checkers for a profile."""
    summary = BaselineSummary()
    python = sys.executable
    hard_gates, other_gates = _import_and_collect()

    entries = hard_gates + other_gates
    if profile == "pr-fast":
        entries = [e for e in entries if "pr-fast" in e.profiles]

    for entry in sorted(entries, key=lambda e: e.layer):
        result = _run_checker_subprocess(entry, python)
        summary.results.append(result)

    return summary


# ── Output ──────────────────────────────────────────────────────────

def print_summary(summary: BaselineSummary) -> None:
    print("\n" + "=" * 60)
    print("ORDIVON VERIFICATION BASELINE (auto-discovered)")
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


def print_manifest() -> None:
    """Print auto-generated manifest JSON from the registry."""
    from ordivon_verify.registry import registry
    manifest = registry.generate_manifest()
    # Add external gates (ruff, pytest, eval corpus) that aren't checkers
    manifest["auto_generated"] = True
    manifest["generated_at"] = "auto"
    manifest["_note"] = (
        "This manifest is auto-generated from @register_checker decorators. "
        "External gates (ruff, pytest, eval corpus) must be added manually "
        "or wrapped as checkers."
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


# ── Main ────────────────────────────────────────────────────────────

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Ordivon Verification Baseline (auto-discovery)")
    parser.add_argument("--pr-fast", action="store_true", help="Run PR-fast gates only")
    parser.add_argument("--manifest", action="store_true", help="Dump auto-generated manifest JSON")
    args = parser.parse_args()

    if args.manifest:
        # Import checkers first to populate registry, then dump manifest
        _import_and_collect()
        print_manifest()
        return 0

    profile = "pr-fast" if args.pr_fast else "full"
    summary = run_all(profile)
    print_summary(summary)
    return 0 if summary.overall_ready else 1


if __name__ == "__main__":
    sys.exit(main())
