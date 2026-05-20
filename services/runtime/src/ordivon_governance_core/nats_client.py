"""NATS JetStream client for Ordivon governance events.

Replaces in-process event dispatch (events.py) with durable JetStream
publish/subscribe. Falls back to in-process dispatch when NATS is not available.

Subject naming: ordivon.{domain}.{action}

Domains: object, observation, claim, evidence, authority, transition, receipt, debt

Usage:
    from ordivon_governance_core.nats_client import (
        publish_event, subscribe_to_events, jetstream_available,
        GOVERNANCE_SUBJECTS,
    )

    # Publish an event
    await publish_event("ordivon.object.registered", payload)

    # Subscribe to governance events
    sub = await subscribe_to_events("ordivon.object.>", handle_event)
"""

from __future__ import annotations

import inspect
import json
import os
from datetime import datetime, timezone
from typing import Callable, Optional

# Subject naming conventions — derived from event-taxonomy.json
GOVERNANCE_SUBJECTS = {
    # E0 — Observation
    "observation": {
        "created": "ordivon.observation.created",
        "inventory_executed": "ordivon.observation.inventory_executed",
    },
    # E1 — Documentation
    "documentation": {
        "submitted": "ordivon.object.declared",
        "modified": "ordivon.object.registered",
    },
    # E2 — Governance Artifact
    "governance_artifact": {
        "registry_created": "ordivon.object.registry_created",
        "registry_modified": "ordivon.object.registry_modified",
        "receipt_written": "ordivon.receipt.created",
        "finding_recorded": "ordivon.observation.finding_recorded",
        "lesson_extracted": "ordivon.receipt.lesson_extracted",
    },
    # E3 — Evidence
    "evidence": {
        "collected": "ordivon.evidence.attached",
        "claim_replayed": "ordivon.claim.checked",
        "test_suite_run": "ordivon.evidence.test_run",
        "verify_executed": "ordivon.evidence.verify_executed",
    },
    # E4 — Debt Lifecycle
    "debt_lifecycle": {
        "opened": "ordivon.debt.opened",
        "renewed": "ordivon.debt.transitioned",
        "closed": "ordivon.debt.closed",
        "severity_changed": "ordivon.debt.severity_changed",
    },
    # E5 — Checker Gate
    "checker_gate": {
        "registered": "ordivon.object.checker_registered",
        "modified": "ordivon.object.checker_modified",
        "severity_changed": "ordivon.object.gate_severity_changed",
        "reconcile_executed": "ordivon.observation.reconcile_executed",
    },
    # E6 — Authority / Policy
    "authority_policy": {
        "candidate_proposed": "ordivon.claim.candidate_proposed",
        "candidate_evaluated": "ordivon.claim.candidate_evaluated",
        "policy_activated": "ordivon.claim.policy_activated",
        "authority_changed": "ordivon.authority.required",
    },
    # E7 — Promotion
    "promotion": {
        "requested": "ordivon.transition.requested",
        "granted": "ordivon.transition.accepted",
        "deferred_gap_accepted": "ordivon.transition.blocked",
    },
    # E8 — Runtime Tool
    "runtime_tool": {
        "invoked": "ordivon.object.tool_invoked",
        "file_modified": "ordivon.object.file_modified",
        "external_api_called": "ordivon.object.external_api_called",
    },
    # E9 — External Impact
    "external_impact": {
        "release_published": "ordivon.object.release_published",
        "external_deployment": "ordivon.object.external_deployment",
        "compliance_submission": "ordivon.object.compliance_submission",
    },
}

# Flattened mapping: event_type → subject
EVENT_TYPE_TO_SUBJECT: dict[str, str] = {}
for _class_subjects in GOVERNANCE_SUBJECTS.values():
    for _type, _subject in _class_subjects.items():
        EVENT_TYPE_TO_SUBJECT[_type] = _subject

# Event class → subject prefix
EVENT_CLASS_TO_PREFIX: dict[str, str] = {
    "E0_observation": "ordivon.observation",
    "E1_documentation": "ordivon.object",
    "E2_governance_artifact": "ordivon.object",
    "E3_evidence": "ordivon.evidence",
    "E4_debt_lifecycle": "ordivon.debt",
    "E5_checker_gate": "ordivon.object",
    "E6_authority_policy": "ordivon.claim",
    "E7_promotion": "ordivon.transition",
    "E8_runtime_tool": "ordivon.object",
    "E9_external_impact": "ordivon.object",
}

# JetStream stream configuration
STREAM_NAME = "ORDIVON_EVENTS"
STREAM_SUBJECTS = [
    "ordivon.object.>",
    "ordivon.observation.>",
    "ordivon.claim.>",
    "ordivon.evidence.>",
    "ordivon.authority.>",
    "ordivon.transition.>",
    "ordivon.receipt.>",
    "ordivon.debt.>",
]

# ── NATS client (lazy) ─────────────────────────────────────────────────────

_nc = None
_js = None
_nats_available: Optional[bool] = None


def _get_nats_url() -> str:
    return os.environ.get("ORDIVON_NATS_URL", "nats://localhost:4222")


def _get_creds_file() -> Optional[str]:
    return os.environ.get("ORDIVON_NATS_CREDS") or None


async def _get_js():
    """Lazy-initialize JetStream context."""
    global _nc, _js, _nats_available
    if _js is not None:
        return _js
    try:
        import nats
        from nats.js.api import StreamConfig, RetentionPolicy, StorageType

        _nc = await nats.connect(
            _get_nats_url(),
            user_credentials=_get_creds_file(),
        )
        _js = _nc.jetstream()

        # Ensure stream exists
        try:
            await _js.stream_info(STREAM_NAME)
        except Exception:
            await _js.add_stream(
                StreamConfig(
                    name=STREAM_NAME,
                    subjects=STREAM_SUBJECTS,
                    retention=RetentionPolicy.LIMITS,
                    max_msgs=100_000,
                    max_bytes=1024 * 1024 * 512,  # 512 MB
                    storage=StorageType.FILE,
                )
            )

        _nats_available = True
        return _js
    except ImportError:
        _nats_available = False
        return None
    except Exception:
        _nats_available = False
        return None


def jetstream_available() -> bool:
    """Check if NATS JetStream is available (sync check, returns cached result)."""
    return _nats_available is True


async def ensure_stream() -> bool:
    """Ensure the JetStream stream exists. Returns True if successful."""
    js = await _get_js()
    return js is not None


# ── Publish ─────────────────────────────────────────────────────────────────


async def publish_event(
    subject: str,
    payload: dict,
    event_type: str = "",
    event_class: str = "",
    producer: str = "ordivon-core",
    producer_type: str = "system_tool",
    source_context: str = "trusted_repo",
) -> bool:
    """Publish a governance event to NATS JetStream.

    Returns True if published (or fallback dispatched), False on failure.

    When NATS is not available, falls back to in-process dispatch via events.py.
    """
    # Enrich payload with standard event metadata
    event = {
        "event_id": payload.pop("event_id", _generate_event_id()),
        "event_type": event_type or payload.get("event_type", "unknown"),
        "event_class": event_class or payload.get("event_class", ""),
        "producer": producer,
        "producer_type": producer_type,
        "source_context": source_context,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }

    js = await _get_js()
    if js is not None:
        try:
            await js.publish(
                subject,
                json.dumps(event).encode(),
            )
            return True
        except Exception:
            pass

    # Fallback: in-process dispatch
    try:
        from ordivon_governance_core.events import dispatch

        dispatch(event.get("event_class", ""), event)
        return True
    except Exception:
        return False


def _generate_event_id() -> str:
    import uuid

    return f"evt-{uuid.uuid4().hex[:16]}"


# ── Subscribe ───────────────────────────────────────────────────────────────


async def subscribe_to_events(
    subject: str,
    handler: Callable[[dict], None],
    durable_name: str = "",
    deliver_group: str = "",
) -> bool:
    """Subscribe to governance events on a NATS subject.

    Uses pull-based consumer by default (ephemeral if no durable_name).
    Handles both sync and async handlers.

    Returns True if subscription established.
    """
    js = await _get_js()
    if js is None:
        return False

    try:
        # Use pull-based consumer. Ephemeral by default (no durable name = starts fresh).
        sub = await js.pull_subscribe(subject, durable=durable_name or "")
        import asyncio

        asyncio.create_task(_pull_loop(sub, handler))
        return True
    except Exception:
        return False


async def _pull_loop(sub, handler: Callable[[dict], None]) -> None:
    """Background pull loop for pull-based consumer."""
    import asyncio

    while True:
        try:
            msgs = await sub.fetch(10, timeout=1)
            for msg in msgs:
                try:
                    data = json.loads(msg.data.decode())
                    result = handler(data)
                    if inspect.iscoroutine(result):
                        await result
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
                await msg.ack()
        except asyncio.TimeoutError:
            pass
        except TimeoutError:
            pass  # nats-py may raise builtin TimeoutError or its own
        except Exception:
            await asyncio.sleep(1)


def _handle_msg(msg, handler: Callable[[dict], None]) -> None:
    """Parse NATS message and call handler. Returns None (nats-py awaits the callback)."""
    try:
        data = json.loads(msg.data.decode())
        result = handler(data)
        if inspect.iscoroutine(result):
            import asyncio

            asyncio.ensure_future(result)
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass


async def _async_handle_msg(msg, handler: Callable[[dict], None]) -> None:
    """Async wrapper for NATS callback. nats-py expects an awaitable."""
    try:
        data = json.loads(msg.data.decode())
        result = handler(data)
        if inspect.iscoroutine(result):
            await result
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass


# ── Convenience publishers ──────────────────────────────────────────────────


async def publish_object_event(
    action: str,
    object_id: str,
    object_type: str = "",
    extra: dict | None = None,
) -> bool:
    """Publish an object lifecycle event."""
    return await publish_event(
        f"ordivon.object.{action}",
        {"object_id": object_id, "object_type": object_type, **(extra or {})},
        event_type=f"object_{action}",
        event_class=_class_for_action(action),
    )


async def publish_debt_event(
    action: str,
    debt_id: str,
    severity: str = "medium",
    extra: dict | None = None,
) -> bool:
    """Publish a debt lifecycle event."""
    return await publish_event(
        f"ordivon.debt.{action}",
        {"debt_id": debt_id, "severity": severity, **(extra or {})},
        event_type=f"debt_{action}",
        event_class="E4_debt_lifecycle",
    )


async def publish_receipt_event(
    receipt_id: str,
    status: str = "DRAFT",
    extra: dict | None = None,
) -> bool:
    """Publish a receipt creation event."""
    return await publish_event(
        "ordivon.receipt.created",
        {"receipt_id": receipt_id, "status": status, **(extra or {})},
        event_type="receipt_created",
        event_class="E2_governance_artifact",
    )


async def publish_evidence_event(
    evidence_id: str,
    action: str = "attached",
    extra: dict | None = None,
) -> bool:
    """Publish an evidence event."""
    return await publish_event(
        f"ordivon.evidence.{action}",
        {"evidence_id": evidence_id, **(extra or {})},
        event_type=f"evidence_{action}",
        event_class="E3_evidence",
    )


async def publish_claim_event(
    claim_id: str,
    action: str = "checked",
    extra: dict | None = None,
) -> bool:
    """Publish a claim event."""
    return await publish_event(
        f"ordivon.claim.{action}",
        {"claim_id": claim_id, **(extra or {})},
        event_type=f"claim_{action}",
        event_class="E6_authority_policy",
    )


async def publish_transition_event(
    object_id: str,
    from_status: str,
    to_status: str,
    action: str = "requested",
    extra: dict | None = None,
) -> bool:
    """Publish a state transition event."""
    return await publish_event(
        f"ordivon.transition.{action}",
        {"object_id": object_id, "from_status": from_status, "to_status": to_status, **(extra or {})},
        event_type=f"transition_{action}",
        event_class="E7_promotion",
    )


def _class_for_action(action: str) -> str:
    """Map action name to event class."""
    action_class_map = {
        "declared": "E1_documentation",
        "registered": "E2_governance_artifact",
        "observed": "E0_observation",
        "verified": "E3_evidence",
        "checker_registered": "E5_checker_gate",
        "tool_invoked": "E8_runtime_tool",
        "release_published": "E9_external_impact",
    }
    return action_class_map.get(action, "E2_governance_artifact")


# ── Cleanup ─────────────────────────────────────────────────────────────────


async def close() -> None:
    """Close NATS connection."""
    global _nc, _js, _nats_available
    if _nc is not None:
        try:
            await _nc.close()
        except Exception:
            pass
    _nc = None
    _js = None
    _nats_available = None
