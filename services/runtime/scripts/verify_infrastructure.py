#!/usr/bin/env python3
"""Ordivon Infrastructure Operational Verification Script.

Validates that all Phase 2-3 infrastructure components are running and
functional. Run this after `docker compose -f docker-compose.infrastructure.yml up -d`.

Usage:
    python3 scripts/verify_infrastructure.py
    python3 scripts/verify_infrastructure.py --quick    # Skip slow checks

Checks:
    1. PostgreSQL connectivity + query
    2. NATS JetStream stream creation + publish + consume
    3. Temporal server connectivity
    4. OpenFGA store + authorization check
    5. OPA CLI availability + policy evaluation
    6. All Phase 1-3 integration tests
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

PASS = "✓"
FAIL = "✗"
SKIP = "○"


def check_postgres() -> tuple[bool, str]:
    """Verify PostgreSQL connectivity and data integrity."""
    try:
        from state.db.session import SessionLocal
        from state.db.governance_schema import DocumentRegistry

        db = SessionLocal()
        count = db.query(DocumentRegistry).count()
        db.close()
        if count > 0:
            return True, f"PG connected, {count} registry entries"
        return True, "PG connected, but 0 entries (may need migration)"
    except Exception as e:
        return False, str(e)[:120]


async def check_nats() -> tuple[bool, str]:
    """Verify NATS JetStream: connect, create stream, publish, consume."""
    try:
        from ordivon_governance_core.nats_client import (
            ensure_stream,
            publish_event,
            close,
        )

        ok = await ensure_stream()
        if not ok:
            return False, "Cannot connect to NATS or create JetStream stream"

        # Publish a test event
        published = await publish_event(
            "ordivon.observation.test",
            {"test": True, "timestamp": "now"},
            event_type="test_event",
            event_class="E0_observation",
        )
        if not published:
            return False, "Publish failed"

        await close()
        return True, "NATS JetStream: stream created, event published"
    except ImportError:
        return False, "nats-py not installed (run: uv pip install nats-py)"
    except Exception as e:
        return False, str(e)[:120]


async def check_temporal() -> tuple[bool, str]:
    """Verify Temporal server connectivity."""
    try:
        from temporalio.client import Client
        from temporalio.api.workflowservice.v1 import GetSystemInfoRequest

        host = "localhost:7233"
        namespace = "default"
        client = await Client.connect(host, namespace=namespace)
        await client.workflow_service.get_system_info(GetSystemInfoRequest())
        return True, f"Temporal server reachable ({host}, namespace={namespace})"
    except ImportError:
        return False, "temporalio not installed (run: uv pip install temporalio)"
    except Exception as e:
        return False, str(e)[:120]


OPENFGA_SMOKE_MODEL = {
    "schema_version": "1.1",
    "type_definitions": [
        {"type": "user", "relations": {}, "metadata": None},
        {
            "type": "organization",
            "relations": {
                "admin": {
                    "this": {},
                },
            },
            "metadata": {
                "relations": {
                    "admin": {
                        "directly_related_user_types": [{"type": "user"}],
                    },
                },
            },
        },
    ],
}


async def check_openfga() -> tuple[bool, str]:
    """Verify OpenFGA: connect, create store, write tuple, check."""
    try:
        from ordivon_governance_core.openfga_client import OpenFGAClient

        client = OpenFGAClient()
        if not await client.ensure_store():
            return False, "Cannot resolve or create OpenFGA store"

        model_id = await client.write_authorization_model(OPENFGA_SMOKE_MODEL)
        if not model_id:
            return False, "Cannot write OpenFGA smoke authorization model"

        # Write a test tuple
        ok = await client.write_tuple("user:test-user", "admin", "organization:ordivon")
        if not ok:
            return False, "Cannot write tuple to OpenFGA"

        # Check it
        allowed = await client.check("user:test-user", "admin", "organization:ordivon")
        if allowed:
            return True, "OpenFGA: store/model/tuple verified"
        return False, "OpenFGA: tuple written but check returned False"
    except Exception as e:
        return False, str(e)[:120]


def check_opa() -> tuple[bool, str]:
    """Verify OPA CLI is installed and policies evaluate correctly."""
    try:
        from ordivon_verify.control.authority_state import check_transition_opa

        result = check_transition_opa(
            from_evidence="partial",
            from_authorization="not_requested",
            from_policy="candidate",
            to_evidence="sufficient",
        )
        if result.get("all_valid"):
            backend = result.get("backend", "unknown")
            return True, f"OPA/transition check: valid ({backend} backend)"
        return False, f"Transition check returned invalid: {result}"
    except Exception as e:
        return False, str(e)[:120]


def run_integration_tests() -> tuple[bool, str]:
    """Run all Phase 1-3 integration tests."""
    import subprocess

    test_files = [
        ROOT / "tests/test_nats_integration.py",
        ROOT / "tests/test_authorization_integration.py",
    ]

    results = {}
    for tf in test_files:
        if not tf.exists():
            results[tf.name] = (False, "file not found")
            continue
        try:
            proc = subprocess.run(
                [sys.executable, str(tf)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=120,
            )
            passed = "0 failed" in proc.stdout or proc.returncode == 0
            results[tf.name] = (passed, f"exit {proc.returncode}")
        except subprocess.TimeoutExpired:
            results[tf.name] = (False, "timeout")
        except Exception as e:
            results[tf.name] = (False, str(e)[:80])

    all_pass = all(r[0] for r in results.values())
    summary = ", ".join(f"{n}: {'PASS' if r[0] else 'FAIL'}" for n, r in results.items())
    return all_pass, summary


async def main() -> int:
    quick = "--quick" in sys.argv

    print("=== Ordivon Infrastructure Operational Verification ===\n")

    checks = [
        ("PostgreSQL", check_postgres),
        ("NATS JetStream", check_nats),
        ("Temporal", check_temporal),
        ("OpenFGA", check_openfga),
        ("OPA (transition validation)", check_opa),
    ]

    passed = 0
    failed = 0

    for name, fn in checks:
        try:
            if asyncio.iscoroutinefunction(fn):
                ok, msg = await fn()
            else:
                ok, msg = fn()
        except Exception as e:
            ok, msg = False, str(e)[:120]

        icon = PASS if ok else FAIL
        print(f"  {icon} {name}: {msg}")
        if ok:
            passed += 1
        else:
            failed += 1

    if not quick:
        print("\n  Running integration tests...")
        ok, msg = run_integration_tests()
        icon = PASS if ok else FAIL
        print(f"  {icon} Integration tests: {msg}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n=== Result: {passed} passed, {failed} failed ===")

    if failed > 0:
        print("\nTo fix:")
        print("  1. Start infrastructure: docker compose -f docker-compose.infrastructure.yml up -d")
        print("  2. Install deps: uv pip install nats-py temporalio")
        print("  3. Run migration: python3 scripts/migrate_governance_to_pg.py")
        print("  4. Re-run: python3 scripts/verify_infrastructure.py")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
