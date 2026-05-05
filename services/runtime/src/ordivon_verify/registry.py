"""
DEPRECATED — This module is the legacy checker registry. It is no longer the
primary registration mechanism and is kept only for backward compatibility with
tests that import the ``register_checker`` symbol.

The canonical registry is now ``ordivon_verify.checker_registry``, which
auto-discovers checkers from the ``checkers/<name>/`` directory structure
(CHECKER.md + run.py). New checkers MUST be created as directories under
``checkers/``, NOT as scripts in ``scripts/`` decorated with @register_checker.

See ``src/ordivon_verify/checker_registry.py`` and ``scripts/run_baseline.py``
for the current discovery and execution pipeline.

Legacy docstring preserved below for historical reference.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Checker Registry — Hermes Agent style self-registration for governance checkers.

Each checker script calls ``@register_checker(...)`` on its entry function.
The registry collects all registrations at import time and provides:

- ``get_all()``: all registered checkers with metadata
- ``get_for_profile(name)``: checkers for "pr-fast" or "full"
- ``generate_manifest()``: auto-generate verification-gate-manifest.json
- ``run_all(profile)``: execute all checkers, return summary

Adding a checker: create a new file in scripts/, decorate with @register_checker.
That's it. No manifest edit. No baseline edit. No runner dict edit.

Import chain (same direction as Hermes tools/registry.py):
    ordivon_verify/registry.py      (no imports from checker scripts)
              ^
    scripts/check_*.py              (import from ordivon_verify.registry)
              ^
    scripts/run_verification_baseline.py  (imports registry + triggers discovery)
              ^
    src/ordivon_verify/runner.py    (imports registry for Verify CLI)
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parents[1]  # Ordivon root


# ── Data types ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class CheckerResult:
    """Structured result from a checker run."""
    status: str                      # "pass" | "fail" | "warn"
    exit_code: int
    findings: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    output: str = ""


@dataclass(frozen=True)
class CheckerEntry:
    """Metadata for a registered checker. Lives in the checker file, not the manifest."""
    gate_id: str
    display_name: str
    layer: str
    hardness: str                    # "hard" | "escalation" | "advisory"
    purpose: str
    protects_against: str
    profiles: tuple[str, ...]        # ("pr-fast", "full")
    entry: Callable[..., CheckerResult]
    timeout: int = 120
    file_path: str = ""              # set by registry at registration time


# ── Registry ────────────────────────────────────────────────────────

class CheckerRegistry:
    """Singleton. Checkers self-register via the @register_checker decorator."""

    def __init__(self):
        self._entries: dict[str, CheckerEntry] = {}

    def register(self, **kwargs) -> Callable:
        """Decorator: @register_checker(gate_id=..., display_name=..., ...)."""
        def decorator(fn: Callable[..., CheckerResult]) -> Callable[..., CheckerResult]:
            # Capture the file path of the checker for subprocess spawning
            import inspect
            file_path = inspect.getfile(fn)
            entry = CheckerEntry(
                entry=fn,
                file_path=file_path,
                **kwargs,
            )
            self._entries[entry.gate_id] = entry
            return fn
        return decorator

    def get_all(self) -> list[CheckerEntry]:
        return list(self._entries.values())

    def get_for_profile(self, profile: str) -> list[CheckerEntry]:
        return [e for e in self._entries.values() if profile in e.profiles]

    def get_hard(self) -> list[CheckerEntry]:
        return [e for e in self._entries.values() if e.hardness == "hard"]

    def run(self, entry: CheckerEntry) -> CheckerResult:
        """Run a checker by calling its entry function directly."""
        try:
            result = entry.entry()
            return result
        except Exception as exc:
            return CheckerResult(
                status="fail",
                exit_code=-1,
                findings=[f"Checker crashed: {exc}"],
            )

    def run_as_subprocess(self, entry: CheckerEntry) -> CheckerResult:
        """Run a checker as a subprocess (for isolation)."""
        script = entry.file_path
        cmd = [sys.executable, str(script)]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=entry.timeout,
                cwd=str(ROOT),
            )
            return CheckerResult(
                status="pass" if proc.returncode == 0 else "fail",
                exit_code=proc.returncode,
                output=(proc.stdout + proc.stderr).strip()[:1000],
            )
        except subprocess.TimeoutExpired:
            return CheckerResult(
                status="fail",
                exit_code=-1,
                findings=[f"Checker timed out ({entry.timeout}s)"],
            )
        except Exception as exc:
            return CheckerResult(
                status="fail",
                exit_code=-1,
                findings=[f"Checker execution error: {exc}"],
            )

    def generate_manifest(self) -> dict:
        """Generate verification-gate-manifest.json from registered checkers."""
        gates = []
        for entry in sorted(self._entries.values(), key=lambda e: e.layer):
            gates.append({
                "gate_id": entry.gate_id,
                "display_name": entry.display_name,
                "layer": entry.layer,
                "hardness": entry.hardness,
                "purpose": entry.purpose,
                "protects_against": entry.protects_against,
                "may_be_removed_only_by": "Stage Summit with documented reason",
            })
        return {
            "manifest_id": "auto-generated-v1",
            "profile": "auto",
            "version": "generated",
            "status": "current",
            "authority": "derived_from_registry",
            "last_verified": "auto",
            "gate_count": len(gates),
            "gates": gates,
        }


# Module-level singleton
registry = CheckerRegistry()

# Public decorator
register_checker = registry.register
