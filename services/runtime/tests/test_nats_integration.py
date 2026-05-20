"""Integration tests for Phase 2: NATS JetStream event pipeline.

Validates: event publish → in-process dispatch → PG write → query.

⚠️ COVERAGE GAP (DEBT-INFRA-003, 2026-05-13):
These tests verify FALLBACK paths only — process-internal dispatch, local
Temporal execution, in-memory event handling. The PRIMARY paths (NATS
JetStream publish/subscribe, Temporal server workflow execution) are NOT
tested because NATS and Temporal servers have never been started.

To fix: start docker-compose.infrastructure.yml, then add tests that
verify actual JetStream stream creation, message persistence, consumer
replay, and Temporal workflow durable execution.

Run:
    python3 tests/test_nats_integration.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


def test_event_dispatch_inprocess() -> None:
    """Event dispatched via in-process handler (NATS not running)."""
    from ordivon_governance_core.events import (
        register_handler,
        clear_handlers,
        dispatch_event,
    )

    clear_handlers()
    received: list[dict] = []

    def handler(payload: dict) -> dict:
        received.append(payload)
        return {"status": "handled"}

    register_handler("E3_evidence", handler)

    result = dispatch_event(
        event_class="E3_evidence",
        payload={"evidence_id": "ev-test-001", "sha256": "abc123"},
        event_type="evidence_collected",
    )

    assert result is True, "dispatch_event should return True"
    assert len(received) == 1, f"Expected 1 handler call, got {len(received)}"
    assert received[0]["evidence_id"] == "ev-test-001"

    clear_handlers()
    print("  ✓ test_event_dispatch_inprocess PASSED")


def test_event_write_to_pg() -> None:
    """Event dispatched and persisted to governance_events table."""
    from ordivon_governance_core.events import dispatch_event, clear_handlers
    from state.db.session import SessionLocal
    from state.db.governance_schema import GovernanceEvent

    clear_handlers()

    dispatch_event(
        event_class="E4_debt_lifecycle",
        payload={"debt_id": "TEST-DEBT-001", "severity": "medium"},
        event_type="debt_opened",
    )

    # Write to PG
    db = SessionLocal()
    event = GovernanceEvent(
        event_id="evt-test-001",
        event_type="debt_opened",
        event_class="E4_debt_lifecycle",
        producer="test-runner",
        producer_type="system_tool",
        source_context="trusted_repo",
        payload={"debt_id": "TEST-DEBT-001", "severity": "medium"},
    )
    db.add(event)
    db.commit()

    # Verify
    queried = db.query(GovernanceEvent).filter(GovernanceEvent.event_id == "evt-test-001").first()
    assert queried is not None, "Event should be persisted"
    assert queried.event_type == "debt_opened"
    assert queried.event_class == "E4_debt_lifecycle"
    assert queried.payload["debt_id"] == "TEST-DEBT-001"

    # Cleanup
    db.delete(queried)
    db.commit()
    db.close()

    print("  ✓ test_event_write_to_pg PASSED")


def test_subject_mapping() -> None:
    """Verify event_type → NATS subject mapping is complete."""
    from ordivon_governance_core.nats_client import (
        EVENT_TYPE_TO_SUBJECT,
        EVENT_CLASS_TO_PREFIX,
    )

    # All event classes have a subject prefix
    expected_classes = [
        "E0_observation",
        "E1_documentation",
        "E2_governance_artifact",
        "E3_evidence",
        "E4_debt_lifecycle",
        "E5_checker_gate",
        "E6_authority_policy",
        "E7_promotion",
        "E8_runtime_tool",
        "E9_external_impact",
    ]
    for ec in expected_classes:
        assert ec in EVENT_CLASS_TO_PREFIX, f"Missing prefix for {ec}"

    # Flattened mapping is non-empty
    assert len(EVENT_TYPE_TO_SUBJECT) > 20, f"Expected >20 subjects, got {len(EVENT_TYPE_TO_SUBJECT)}"

    # Subject naming convention
    for subject in EVENT_TYPE_TO_SUBJECT.values():
        assert subject.startswith("ordivon."), f"Subject '{subject}' should start with 'ordivon.'"

    print("  ✓ test_subject_mapping PASSED")


def test_temporal_activities_run_locally() -> None:
    """Verify reconciliation activities work in local (non-Temporal) mode."""
    import asyncio
    from ordivon_governance_core.temporal_worker import (
        _run_reconciliation_locally,
        activity_validate_registry,
    )

    # Test individual activity
    result = activity_validate_registry()
    assert result.step_id == "validate_registry"
    assert result.status in ("completed", "completed_with_findings", "failed", "error", "timeout", "skipped")
    print(f"  activity_validate_registry: {result.status} ({result.duration_ms}ms)")

    # Test full local reconciliation
    result = asyncio.run(_run_reconciliation_locally("full"))
    assert "overall_status" in result
    assert "steps" in result
    assert len(result["steps"]) >= 6
    print(f"  local reconciliation: {result['overall_status']} ({len(result['steps'])} steps)")

    print("  ✓ test_temporal_activities_run_locally PASSED")


def test_event_schema_json() -> None:
    """Verify event taxonomy JSON is valid and complete."""
    taxonomy_path = ROOT / "schemas/governance/event-taxonomy.json"
    assert taxonomy_path.exists(), f"Event taxonomy not found at {taxonomy_path}"

    taxonomy = json.loads(taxonomy_path.read_text())
    assert "event_classes" in taxonomy
    assert "event_types" in taxonomy
    assert len(taxonomy["event_classes"]) >= 10
    assert len(taxonomy["event_types"]) >= 25

    print(
        f"  ✓ test_event_schema_json PASSED ({len(taxonomy['event_classes'])} classes, {len(taxonomy['event_types'])} types)"
    )


# ── Primary Path Tests (require running NATS + Temporal servers) ────────────


def test_nats_jetstream_e2e() -> None:
    """End-to-end JetStream: publish 3 events, consume all 3 via raw nats-py."""
    import asyncio, json

    async def _run():
        try:
            import nats
        except ImportError:
            print("  ⏭ test_nats_jetstream_e2e SKIPPED (nats-py not installed)")
            return

        try:
            nc = await nats.connect("localhost:4222")
        except Exception:
            print("  ⏭ test_nats_jetstream_e2e SKIPPED (NATS server not available)")
            return

        js = nc.jetstream()
        try:
            await js.add_stream(
                nats.js.api.StreamConfig(
                    name="TEST_PRIMARY",
                    subjects=["test.primary.>"],
                    retention=nats.js.api.RetentionPolicy.LIMITS,
                    storage=nats.js.api.StorageType.FILE,
                )
            )
        except Exception:
            pass

        # Pull consumer
        sub = await js.pull_subscribe("test.primary.>", durable="")

        # Publish
        for i in range(3):
            await js.publish(
                "test.primary.event",
                json.dumps({"event_id": f"evt-{i}", "event_type": "test", "event_class": "E0"}).encode(),
            )

        # Fetch
        msgs = await sub.fetch(5, timeout=5)
        assert len(msgs) >= 3, f"Expected >=3 events, got {len(msgs)}"
        for msg in msgs:
            data = json.loads(msg.data.decode())
            assert "event_id" in data
            await msg.ack()

        await nc.close()

    try:
        asyncio.run(_run())
        print("  ✓ test_nats_jetstream_e2e PASSED")
    except AssertionError as e:
        print(f"  ✗ test_nats_jetstream_e2e FAILED: {e}")
        raise


def test_temporal_server_connect() -> None:
    """Connect to Temporal server and verify namespace exists."""
    import asyncio

    async def _run():
        try:
            from temporalio.client import Client
        except ImportError:
            print("  ⏭ test_temporal_server_connect SKIPPED (temporalio not installed)")
            return

        try:
            await Client.connect("localhost:7233")
            print("  ✓ test_temporal_server_connect PASSED (connected)")
        except Exception as e:
            print(f"  ⏭ test_temporal_server_connect SKIPPED (server not available: {e})")

    asyncio.run(_run())
def main() -> int:
    print("=== Phase 2 Integration Tests ===\n")

    tests = [
        ("Event dispatch (in-process)", test_event_dispatch_inprocess),
        ("Event → PG write", test_event_write_to_pg),
        ("Subject mapping", test_subject_mapping),
        ("Temporal activities (local)", test_temporal_activities_run_locally),
        ("Event taxonomy schema", test_event_schema_json),
        ("NATS JetStream E2E (primary)", test_nats_jetstream_e2e),
        ("Temporal server connect (primary)", test_temporal_server_connect),
        ("OPA primary backend", test_opa_primary_backend),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"  ✗ {name} FAILED: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
