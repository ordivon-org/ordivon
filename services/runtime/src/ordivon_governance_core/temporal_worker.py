"""Temporal worker and workflow definitions for Ordivon governance.

Replaces hardcoded subprocess DAGs (reconcile.py, verify.py, aos_submit.py)
with durable Temporal workflows + activities.

Architecture:
    Workflow = governance process (reconciliation, AOS submission, verification)
    Activity  = individual step (validate registry, update coverage, run checker)
    Signal    = external trigger (registry changed, phase boundary updated)

Usage:
    # Start worker
    python -m ordivon_governance_core.temporal_worker

    # Trigger a workflow from code
    from ordivon_governance_core.temporal_worker import trigger_reconciliation
    await trigger_reconciliation("registry_changed")
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ── Activity definitions ────────────────────────────────────────────────────


@dataclass
class ActivityResult:
    step_id: str
    status: str  # completed, failed, completed_with_findings, skipped
    exit_code: Optional[int] = None
    stdout_summary: str = ""
    duration_ms: int = 0
    error: Optional[str] = None


def _get_root() -> Path:
    return Path(__file__).resolve().parents[2]


# ── Reconciliation Activities (from reconcile.py) ──────────────────────────


def activity_validate_registry() -> ActivityResult:
    """Validate document registry consistency."""
    return _run_script_activity(
        "validate_registry",
        [sys.executable, "scripts/check_document_registry.py"],
        "Validate document registry consistency",
    )


def activity_update_coverage_boundary() -> ActivityResult:
    """Update coverage boundary from registry + git state."""
    return _run_script_activity(
        "update_coverage_boundary",
        [sys.executable, "scripts/update-coverage-boundary.py"],
        "Update coverage boundary from registry + git state",
    )


def activity_update_path_map() -> ActivityResult:
    """Update path map from coverage boundary."""
    return _run_script_activity(
        "update_path_map",
        [sys.executable, "scripts/update-path-map.py"],
        "Update path map from coverage boundary",
    )


def activity_reconcile_registry_path() -> ActivityResult:
    """Reconcile registry claims vs path map observations."""
    return _run_script_activity(
        "reconcile_registry_path",
        [sys.executable, "scripts/reconcile-registry-path.py"],
        "Reconcile registry claims vs path map observations",
        can_fail=True,
    )


def activity_generate_wiki() -> ActivityResult:
    """Regenerate wiki index from registry."""
    return _run_script_activity(
        "generate_wiki",
        [sys.executable, "scripts/generate_document_wiki.py"],
        "Regenerate wiki index from registry",
    )


def activity_ordivon_verify() -> ActivityResult:
    """Run full governance verification."""
    return _run_script_activity(
        "ordivon_verify",
        [sys.executable, "-m", "ordivon_verify", "all"],
        "Run full governance verification",
        can_fail=True,
    )


def activity_detect_overclaim() -> ActivityResult:
    """Check for overclaim language in receipts."""
    return _run_script_activity(
        "detect_overclaim",
        [sys.executable, "scripts/detect_overclaim.py", str(_get_root() / "receipts/governance")],
        "Check for overclaim language in receipts",
        can_fail=True,
    )


# ── Evidence Activities (from aos_submit.py) ────────────────────────────────


def activity_collect_evidence(
    evidence_dir: str,
    commands: list[dict],
) -> list[ActivityResult]:
    """Collect evidence by running commands and capturing output."""
    results = []
    evidence_path = _get_root() / evidence_dir
    evidence_path.mkdir(parents=True, exist_ok=True)

    for cmd_spec in commands:
        name = cmd_spec.get("name", "unknown")
        cmd = cmd_spec.get("command", "")
        result = _run_shell_activity(
            f"evidence_{name}",
            cmd,
            f"Collect evidence: {name}",
        )
        results.append(result)

    return results


def activity_write_receipt(
    receipt_id: str,
    receipt_path: str,
    receipt_data: dict,
) -> ActivityResult:
    """Write a governance receipt to disk and register in PG."""
    start = time.time()
    try:
        import json

        full_path = _get_root() / receipt_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(json.dumps(receipt_data, indent=2))

        # Also write to PG
        try:
            from state.db.session import SessionLocal
            from state.db.governance_schema import Receipt

            db = SessionLocal()
            rec = Receipt(
                receipt_id=receipt_id,
                receipt_type=receipt_data.get("receipt_type", "governance"),
                phase=receipt_data.get("phase", ""),
                status=receipt_data.get("status", "DRAFT"),
                summary=receipt_data.get("summary", ""),
                claims=receipt_data.get("claims", []),
                evidence_refs=receipt_data.get("evidence_refs", []),
                author=receipt_data.get("author", "ordivon-core"),
                extra=receipt_data.get("extra"),
            )
            db.add(rec)
            db.commit()
            db.close()
        except Exception:
            pass  # PG not available — receipt is still on disk

        return ActivityResult(
            step_id="write_receipt",
            status="completed",
            duration_ms=int((time.time() - start) * 1000),
        )
    except Exception as e:
        return ActivityResult(
            step_id="write_receipt",
            status="error",
            error=str(e),
            duration_ms=int((time.time() - start) * 1000),
        )


# ── Event Publishing Activity ───────────────────────────────────────────────


async def activity_publish_governance_event(
    subject: str,
    payload: dict,
    event_type: str = "",
    event_class: str = "",
) -> bool:
    """Publish a governance event to NATS JetStream."""
    try:
        from ordivon_governance_core.nats_client import publish_event

        return await publish_event(
            subject,
            payload,
            event_type=event_type,
            event_class=event_class,
        )
    except ImportError:
        # Fall back to in-process event dispatch
        try:
            from ordivon_governance_core.events import dispatch

            dispatch(event_class, {**payload, "event_type": event_type, "event_class": event_class})
            return True
        except Exception:
            return False


# ── Helpers ─────────────────────────────────────────────────────────────────


def _run_script_activity(
    step_id: str,
    cmd: list[str],
    description: str = "",
    can_fail: bool = False,
    timeout: int = 120,
) -> ActivityResult:
    """Run a Python script as an activity, capturing output."""
    import subprocess

    start = time.time()

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(_get_root()),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration_ms = int((time.time() - start) * 1000)
        stdout = proc.stdout.strip()[-500:] if proc.stdout else ""

        if proc.returncode != 0 and not can_fail:
            return ActivityResult(
                step_id=step_id,
                status="failed",
                exit_code=proc.returncode,
                stdout_summary=stdout,
                duration_ms=duration_ms,
                error=proc.stderr.strip()[:500] if proc.stderr else f"Exit code {proc.returncode}",
            )
        elif proc.returncode != 0 and can_fail:
            return ActivityResult(
                step_id=step_id,
                status="completed_with_findings",
                exit_code=proc.returncode,
                stdout_summary=stdout,
                duration_ms=duration_ms,
            )
        else:
            return ActivityResult(
                step_id=step_id,
                status="completed",
                exit_code=0,
                stdout_summary=stdout,
                duration_ms=duration_ms,
            )
    except subprocess.TimeoutExpired:
        return ActivityResult(
            step_id=step_id,
            status="timeout",
            error=f"Timed out after {timeout}s",
            duration_ms=int((time.time() - start) * 1000),
        )
    except Exception as e:
        return ActivityResult(
            step_id=step_id,
            status="error",
            error=str(e),
            duration_ms=int((time.time() - start) * 1000),
        )


def _run_shell_activity(
    step_id: str,
    cmd: str,
    description: str = "",
    timeout: int = 60,
) -> ActivityResult:
    """Run a shell command as an activity."""
    import subprocess

    start = time.time()

    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=str(_get_root()),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration_ms = int((time.time() - start) * 1000)
        return ActivityResult(
            step_id=step_id,
            status="completed" if proc.returncode == 0 else "failed",
            exit_code=proc.returncode,
            stdout_summary=proc.stdout.strip()[-300:] if proc.stdout else "",
            duration_ms=duration_ms,
            error=proc.stderr.strip()[:300] if proc.returncode != 0 else None,
        )
    except subprocess.TimeoutExpired:
        return ActivityResult(
            step_id=step_id,
            status="timeout",
            error=f"Timed out after {timeout}s",
            duration_ms=int((time.time() - start) * 1000),
        )
    except Exception as e:
        return ActivityResult(
            step_id=step_id,
            status="error",
            error=str(e),
            duration_ms=int((time.time() - start) * 1000),
        )


# ── Workflow definitions (Temporal) ─────────────────────────────────────────
# These are defined conditionally — Temporal SDK is imported only when the
# worker starts. The definitions below are the canonical workflow structure.


RECONCILIATION_WORKFLOW_STEPS = [
    {
        "id": "validate_registry",
        "activity": "activity_validate_registry",
        "depends_on": [],
        "can_fail": False,
    },
    {
        "id": "update_coverage_boundary",
        "activity": "activity_update_coverage_boundary",
        "depends_on": ["validate_registry"],
        "can_fail": False,
    },
    {
        "id": "update_path_map",
        "activity": "activity_update_path_map",
        "depends_on": ["update_coverage_boundary"],
        "can_fail": False,
    },
    {
        "id": "reconcile_registry_path",
        "activity": "activity_reconcile_registry_path",
        "depends_on": ["update_path_map"],
        "can_fail": True,
    },
    {
        "id": "generate_wiki",
        "activity": "activity_generate_wiki",
        "depends_on": ["reconcile_registry_path"],
        "can_fail": False,
    },
    {
        "id": "ordivon_verify",
        "activity": "activity_ordivon_verify",
        "depends_on": ["generate_wiki"],
        "can_fail": True,
    },
    {
        "id": "detect_overclaim",
        "activity": "activity_detect_overclaim",
        "depends_on": [],
        "can_fail": True,
    },
]


AOS_SUBMIT_WORKFLOW_STEPS = [
    {"id": "identity_validation", "depends_on": [], "can_fail": False},
    {"id": "admission", "depends_on": ["identity_validation"], "can_fail": False},
    {"id": "registry_entry", "depends_on": ["admission"], "can_fail": False},
    {"id": "evidence_collection", "depends_on": ["registry_entry"], "can_fail": False},
    {"id": "reconciliation_check", "depends_on": ["evidence_collection"], "can_fail": True},
    {"id": "governance_verify", "depends_on": ["reconciliation_check"], "can_fail": True},
    {"id": "receipt", "depends_on": ["governance_verify"], "can_fail": False},
    {"id": "publish_events", "depends_on": ["receipt"], "can_fail": True},
]


# ── Worker entry point ──────────────────────────────────────────────────────


def start_worker():
    """Start a Temporal worker for Ordivon governance workflows.

    Requires Temporal server running (see docker-compose.nats-temporal.yml).
    Uses environment variables:
        TEMPORAL_HOST: Temporal server host (default: localhost:7233)
        TEMPORAL_NAMESPACE: Temporal namespace (default: ordivon)
        TEMPORAL_TASK_QUEUE: Task queue name (default: ordivon-governance)
    """
    host = os.environ.get("TEMPORAL_HOST", "localhost:7233")
    namespace = os.environ.get("TEMPORAL_NAMESPACE", "ordivon")
    task_queue = os.environ.get("TEMPORAL_TASK_QUEUE", "ordivon-governance")

    print("=== Ordivon Temporal Worker ===")
    print(f"Host: {host}")
    print(f"Namespace: {namespace}")
    print(f"Task Queue: {task_queue}")
    print()

    try:
        import asyncio
        from temporalio.client import Client
        from temporalio.worker import Worker

        ACTIVITIES = [
            activity_validate_registry,
            activity_update_coverage_boundary,
            activity_update_path_map,
            activity_reconcile_registry_path,
            activity_generate_wiki,
            activity_ordivon_verify,
            activity_detect_overclaim,
            activity_collect_evidence,
            activity_write_receipt,
            activity_publish_governance_event,
        ]

        async def _run():
            client = await Client.connect(host, namespace=namespace)
            worker = Worker(
                client,
                task_queue=task_queue,
                activities=ACTIVITIES,
                workflows=[],  # Workflows registered below if available
            )
            print(f"Worker started. Listening on task queue: {task_queue}")
            print(f"Activities registered: {len(ACTIVITIES)}")
            await worker.run()

        asyncio.run(_run())
    except ImportError as e:
        print(f"ERROR: Temporal SDK not installed — {e}")
        print("Install with: pip install temporalio")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Cannot connect to Temporal server — {e}")
        print("Start Temporal with: docker compose -f docker-compose.nats-temporal.yml up -d")
        sys.exit(1)


# ── Trigger helpers ─────────────────────────────────────────────────────────


async def trigger_reconciliation(trigger: str = "full") -> dict:
    """Trigger a reconciliation workflow.

    When Temporal is available, starts a workflow. Otherwise runs locally.
    Returns workflow result dict.
    """
    try:
        from temporalio.client import Client

        host = os.environ.get("TEMPORAL_HOST", "localhost:7233")
        namespace = os.environ.get("TEMPORAL_NAMESPACE", "ordivon")
        os.environ.get("TEMPORAL_TASK_QUEUE", "ordivon-governance")

        await Client.connect(host, namespace=namespace)
        # Workflow start would go here once workflows are registered
        # For now, run activities locally
        return await _run_reconciliation_locally(trigger)
    except (ImportError, Exception):
        return await _run_reconciliation_locally(trigger)


async def _run_reconciliation_locally(trigger: str = "full") -> dict:
    """Run reconciliation activities locally (no Temporal dependency)."""

    activity_map = {
        "validate_registry": activity_validate_registry,
        "update_coverage_boundary": activity_update_coverage_boundary,
        "update_path_map": activity_update_path_map,
        "reconcile_registry_path": activity_reconcile_registry_path,
        "generate_wiki": activity_generate_wiki,
        "ordivon_verify": activity_ordivon_verify,
        "detect_overclaim": activity_detect_overclaim,
    }

    results = {}
    for step in RECONCILIATION_WORKFLOW_STEPS:
        step_id = step["id"]
        activity_fn = activity_map.get(step_id)
        if not activity_fn:
            continue

        # Check deps
        dep_failed = False
        for dep_id in step["depends_on"]:
            if results.get(dep_id, {}).get("status") in ("failed", "error", "timeout"):
                dep_failed = True
                break

        if dep_failed:
            results[step_id] = {"status": "skipped_dependency_failed"}
            continue

        result = activity_fn()
        results[step_id] = {
            "status": result.status,
            "exit_code": result.exit_code,
            "duration_ms": result.duration_ms,
            "error": result.error,
        }

    # Publish completion event
    overall = "completed" if all(r.get("status") not in ("failed", "error") for r in results.values()) else "failed"

    # Capture trace
    try:
        from scripts.capture_trace import capture_trace
        capture_trace("reconciliation", {"trigger": trigger, "overall_status": overall, "steps": results})
    except Exception:
        pass

    await activity_publish_governance_event(
        "ordivon.observation.reconcile_executed",
        {"trigger": trigger, "overall_status": overall, "results": results},
        event_type="reconcile_executed",
        event_class="E5_checker_gate",
    )

    return {"overall_status": overall, "steps": results}
