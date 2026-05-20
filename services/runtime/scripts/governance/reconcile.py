#!/usr/bin/env python3
"""Governance Reconciliation DAG Runner — run governance reconciliation steps in order.

Usage:
    python3 scripts/governance/reconcile.py --dry-run           # Show what would run
    python3 scripts/governance/reconcile.py --changed registry  # Registry change pipeline
    python3 scripts/governance/reconcile.py --full              # Full reconciliation

Reconciliation DAG:
    registry_changed:
        validate_registry → update_coverage_boundary → update_path_map
        → reconcile_registry_path → generate_wiki → ordivon_verify
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from ordivon_governance_core.trace import GovernanceTrace, new_trace_id

    _HAS_CORE = True
except ImportError:
    _HAS_CORE = False

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "docs/governance/config/reconciliation-dags.json"


def _load_dag_config() -> dict:
    """Load reconciliation DAG from config file. Falls back to built-in on failure."""
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except (json.JSONDecodeError, KeyError):
            pass
    return {}


def _build_steps_from_config(dag_name: str = "registry_changed") -> dict:
    """Build STEPS dict from config DAG."""
    config = _load_dag_config()
    dag = config.get("dags", {}).get(dag_name, {})
    steps = {}
    for step in dag.get("steps", []):
        sid = step["id"]
        cmd_str = step.get("command", "")
        # Split command string into list for subprocess
        cmd_parts = cmd_str.split()
        steps[sid] = {
            "command": cmd_parts,
            "description": step.get("description", sid),
            "depends_on": step.get("depends_on", []),
            "can_fail": step.get("can_fail", False),
        }
    return steps


def _load_steps() -> dict:
    """Load steps from config, with fallback to hardcoded for backward compat."""
    steps = _build_steps_from_config("registry_changed")
    if not steps:
        # Fallback for environments without config
        steps = {
            "validate_registry": {
                "command": ["python3", "scripts/check_document_registry.py"],
                "description": "Validate document registry consistency",
                "depends_on": [],
                "can_fail": False,
            },
            "update_coverage_boundary": {
                "command": ["python3", "scripts/update-coverage-boundary.py"],
                "description": "Update coverage boundary from registry + git state",
                "depends_on": ["validate_registry"],
                "can_fail": False,
            },
            "update_path_map": {
                "command": ["python3", "scripts/update-path-map.py"],
                "description": "Update path map from coverage boundary",
                "depends_on": ["update_coverage_boundary"],
                "can_fail": False,
            },
            "reconcile_registry_path": {
                "command": ["python3", "scripts/reconcile-registry-path.py"],
                "description": "Reconcile registry claims vs path map observations",
                "depends_on": ["update_path_map"],
                "can_fail": True,
            },
            "generate_wiki": {
                "command": ["python3", "scripts/generate_document_wiki.py"],
                "description": "Regenerate wiki index from registry",
                "depends_on": ["reconcile_registry_path"],
                "can_fail": False,
            },
            "ordivon_verify": {
                "command": ["python3", "-m", "ordivon_verify", "all"],
                "description": "Run full governance verification",
                "depends_on": ["generate_wiki"],
                "can_fail": True,
            },
            "detect_overclaim": {
                "command": ["python3", "scripts/detect_overclaim.py", str(ROOT / "receipts/governance")],
                "description": "Check for overclaim language in receipts",
                "depends_on": [],
                "can_fail": True,
            },
        }
    return steps


# Lazy-loaded STEPS — call _load_steps() to get current config
STEPS = None


def _get_steps() -> dict:
    global STEPS
    if STEPS is None:
        STEPS = _load_steps()
    return STEPS


def resolve_dag(trigger: str = "full") -> list[str]:
    """Resolve which steps to run based on trigger."""
    steps = _get_steps()
    if trigger == "full" or trigger == "registry":
        return list(steps.keys())
    elif trigger == "phase-boundary":
        return ["detect_overclaim"]
    else:
        return list(steps.keys())


def topological_order(steps_to_run: list[str]) -> list[str]:
    """Order steps by dependencies (topological sort)."""
    # Simple approach: use predefined order
    order = list(_get_steps().keys())
    return [s for s in order if s in steps_to_run]


def run_step(step_id: str, dry_run: bool = False) -> dict:
    """Run a single reconciliation step."""
    step = _get_steps()[step_id]
    result = {
        "step_id": step_id,
        "description": step["description"],
        "command": " ".join(step["command"]),
        "status": "skipped" if dry_run else "pending",
        "exit_code": None,
        "stdout_summary": "",
        "duration_ms": 0,
        "error": None,
    }

    if dry_run:
        return result

    start = time.time()
    try:
        proc = subprocess.run(
            step["command"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        result["exit_code"] = proc.returncode
        result["stdout_summary"] = proc.stdout.strip()[-200:] if proc.stdout else ""
        result["duration_ms"] = int((time.time() - start) * 1000)

        if proc.returncode != 0 and not step["can_fail"]:
            result["status"] = "failed"
            result["error"] = proc.stderr.strip()[:500] if proc.stderr else f"Exit code {proc.returncode}"
        elif proc.returncode != 0 and step["can_fail"]:
            result["status"] = "completed_with_findings"
            result["error"] = f"Expected: step may exit non-zero ({proc.returncode})"
        else:
            result["status"] = "completed"
    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["error"] = "Step timed out after 60s"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    result["duration_ms"] = int((time.time() - start) * 1000)
    return result


def main():
    if "--dry-run" in sys.argv:
        dry_run = True
    else:
        dry_run = False

    trigger = "full"
    for i, arg in enumerate(sys.argv):
        if arg == "--changed" and i + 1 < len(sys.argv):
            trigger = sys.argv[i + 1]
        elif arg == "--full":
            trigger = "full"

    steps_to_run = resolve_dag(trigger)
    ordered = topological_order(steps_to_run)

    if dry_run:
        print("=== RECONCILIATION PLAN (dry-run) ===")
        print(f"Trigger: {trigger}")
        print(f"Steps: {len(ordered)}")
        for step_id in ordered:
            step = _get_steps()[step_id]
            deps = " → ".join(step["depends_on"]) if step["depends_on"] else "none"
            print(f"  [{step_id}] {step['description']}")
            print(f"    Depends on: {deps}")
            print(f"    Command: {' '.join(step['command'])}")
        return 0

    print(f"=== RECONCILIATION ({trigger}) ===")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"Steps: {len(ordered)}")
    print()

    results = []
    overall_status = "completed"

    for step_id in ordered:
        step = _get_steps()[step_id]
        deps = step.get("depends_on", [])

        # Check dependencies
        dep_failed = False
        for dep_id in deps:
            dep_result = next((r for r in results if r["step_id"] == dep_id), None)
            if dep_result and dep_result["status"] in ("failed", "error", "timeout"):
                dep_failed = True
                break

        if dep_failed:
            result = {
                "step_id": step_id,
                "description": step["description"],
                "status": "skipped_dependency_failed",
                "error": "Upstream step failed",
            }
            print(f"  SKIP [{step_id}]: upstream dependency failed")
        else:
            print(f"  RUN  [{step_id}]: {step['description']}...", end=" ", flush=True)
            result = run_step(step_id, dry_run=False)
            status_icon = {"completed": "✓", "completed_with_findings": "⚠", "failed": "✗", "error": "✗"}.get(
                result["status"], "?"
            )
            print(f"{status_icon} ({result['duration_ms']}ms)")
            if result.get("error"):
                print(f"       {result['error'][:120]}")

        results.append(result)
        if result["status"] in ("failed", "error"):
            # Halt downstream for true failures (not expected findings)
            step_def = _get_steps().get(step_id, {})
            if not step_def.get("can_fail", False):
                overall_status = "failed"

    # Summary
    print("\n=== RECONCILIATION SUMMARY ===")
    statuses = {}
    for r in results:
        s = r["status"]
        statuses[s] = statuses.get(s, 0) + 1
    for s, c in sorted(statuses.items()):
        print(f"  {s}: {c}")
    print(f"Overall: {overall_status}")

    # Generate trace — use core library when available, fallback to raw dict
    if _HAS_CORE:
        t = GovernanceTrace(trace_id=new_trace_id(), operation=f"reconciliation-{trigger}")
        for r in results:
            t.add_span(r["step_id"], r["status"], duration_ms=r.get("duration_ms", 0))
        trace = t.to_dict()
    else:
        trace = {
            "reconciliation_type": trigger,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "overall_status": overall_status,
            "steps": [
                {
                    "step_id": r["step_id"],
                    "status": r["status"],
                    "exit_code": r.get("exit_code"),
                    "duration_ms": r.get("duration_ms"),
                    "error": r.get("error"),
                }
                for r in results
            ],
        }

    trace_path = ROOT / "docs/governance/generated/governance-reconciliation-status.json"
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.write_text(json.dumps(trace, indent=2))
    print(f"\nTrace: {trace_path}")

    return 0 if overall_status == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
