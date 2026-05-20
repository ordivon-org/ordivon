"""Event utilities — load event taxonomy and classify governance events."""

from __future__ import annotations

import json
from pathlib import Path


TAXONOMY_PATH = Path(__file__).resolve().parents[2] / "schemas/governance/event-taxonomy.json"

# Object kind → event class mapping for common submissions
KIND_EVENT_MAP = {
    "GovernanceDocument": ("artifact_submitted", "E1_documentation"),
    "CheckerChangeIntent": ("checker_registered", "E5_checker_gate"),
    "DebtTransition": ("debt_severity_changed", "E4_debt_lifecycle"),
    "CandidateRuleRecord": ("candidate_rule_proposed", "E6_authority_policy"),
    "GatePromotionRecord": ("promotion_requested", "E7_promotion"),
    "EvidenceRecord": ("evidence_collected", "E3_evidence"),
    "ReceiptClaim": ("receipt_claim_updated", "E2_governance_artifact"),
}

# Requested action → event class override
ACTION_EVENT_MAP = {
    "admit_only": "E2_governance_artifact",
    "validate_only": "E0_observation",
    "reject": "E2_governance_artifact",
    "quarantine": "E2_governance_artifact",
}


def load_taxonomy() -> dict:
    """Load event taxonomy from schema."""
    if TAXONOMY_PATH.exists():
        return json.loads(TAXONOMY_PATH.read_text())
    return {}


def classify_event(
    object_kind: str,
    requested_action: str = "",
    producer_type: str = "unknown",
    file_count: int = 0,
    target_paths: list[str] = None,
) -> dict:
    """Classify a submission as a governance event type and class.

    Returns dict with event_type, event_class, risk_level.
    """
    taxonomy = load_taxonomy()
    taxonomy.get("event_types", {})

    # Determine event type
    event_type = "artifact_submitted"  # default
    event_class = "E1_documentation"

    if object_kind in KIND_EVENT_MAP:
        etype, eclass = KIND_EVENT_MAP[object_kind]
        event_type = etype
        event_class = eclass

    # Action-based refinement
    if requested_action in ACTION_EVENT_MAP:
        action_class = ACTION_EVENT_MAP[requested_action]
        # Only upgrade, never downgrade
        class_ranks = {f"E{i}": i for i in range(10)}
        if class_ranks.get(action_class, 0) > class_ranks.get(event_class, 0):
            event_class = action_class

    # Risk level from taxonomy
    risk_level = "low"
    classes = taxonomy.get("event_classes", {})
    if event_class in classes:
        risk_level = classes[event_class].get("risk_level", "low")

    return {
        "event_type": event_type,
        "event_class": event_class,
        "risk_level": risk_level,
        "object_kind": object_kind,
        "requested_action": requested_action,
        "producer_type": producer_type,
    }


def get_required_checks(event_class: str) -> list[str]:
    """Get default required checks for an event class."""
    taxonomy = load_taxonomy()
    classes = taxonomy.get("event_classes", {})
    cls = classes.get(event_class, {})
    checks = []
    if cls.get("admission_required"):
        checks.append("admission")
    if cls.get("evidence_required"):
        checks.append("evidence")
    if cls.get("review_required"):
        checks.append("review")
    return checks


# ── Event Handler Registry ──
# In-process dispatch. Not a message queue. Handlers are callables that receive a dict payload.

_HANDLERS: dict[str, list[callable]] = {}


def register_handler(event_class: str, handler_fn):
    """Register a handler function for an event class. Handler receives payload dict."""
    if event_class not in _HANDLERS:
        _HANDLERS[event_class] = []
    _HANDLERS[event_class].append(handler_fn)


def dispatch(event_class: str, payload: dict) -> list[dict]:
    """Call all registered handlers for an event class. Returns list of handler results."""
    results = []
    for handler in _HANDLERS.get(event_class, []):
        try:
            results.append(handler(payload))
        except Exception as e:
            results.append({"handler": handler.__name__, "error": str(e)})
    return results


def list_handlers(event_class: str = "") -> dict:
    """List registered handlers. If event_class is empty, list all."""
    if event_class:
        return {event_class: [h.__name__ for h in _HANDLERS.get(event_class, [])]}
    return {ec: [h.__name__ for h in hs] for ec, hs in _HANDLERS.items()}


def clear_handlers():
    """Clear all registered handlers. Used for testing."""
    _HANDLERS.clear()


# ── NATS-integrated dispatch ────────────────────────────────────────────────
# Tries NATS JetStream publisher first; falls back to in-process handlers.


def dispatch_event(
    event_class: str,
    payload: dict,
    event_type: str = "",
    producer: str = "ordivon-core",
    producer_type: str = "system_tool",
    source_context: str = "trusted_repo",
) -> bool:
    """Dispatch a governance event — NATS first, in-process fallback.

    Returns True if the event was dispatched successfully.
    """
    from ordivon_governance_core.nats_client import (
        EVENT_CLASS_TO_PREFIX,
        publish_event,
        jetstream_available,
    )

    subject = EVENT_CLASS_TO_PREFIX.get(
        event_class,
        f"ordivon.object.{event_type or 'unknown'}",
    )

    if jetstream_available():
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    publish_event(
                        subject,
                        payload,
                        event_type=event_type,
                        event_class=event_class,
                        producer=producer,
                        producer_type=producer_type,
                        source_context=source_context,
                    ),
                    loop,
                )
                return future.result(timeout=10)
            else:
                return asyncio.run(
                    publish_event(
                        subject,
                        payload,
                        event_type=event_type,
                        event_class=event_class,
                        producer=producer,
                        producer_type=producer_type,
                        source_context=source_context,
                    ),
                )
        except Exception:
            pass

    # In-process fallback
    return len(dispatch(event_class, {**payload, "event_type": event_type, "event_class": event_class})) > 0
