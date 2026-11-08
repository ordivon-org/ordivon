"""Pure admission and bounded backoff policy for retry-safe Provider failures.

No clocks, network, Tools, storage, or mutation. The caller retains authority
over the current assignment deadline, and rechecks it only after this gate.
"""
from __future__ import annotations

from .model import AgentTurnDispatchSafety, AgentTurnFailureCode


def pre_dispatch_retry_permitted(
    *,
    dispatch_safety: AgentTurnDispatchSafety,
    failure_code: AgentTurnFailureCode,
    retries_used: int,
    retry_limit: int,
    cancelled: bool,
) -> bool:
    return (
        dispatch_safety is AgentTurnDispatchSafety.PRE_DISPATCH_SAFE
        and failure_code in {
            AgentTurnFailureCode.TRANSPORT_FAILED,
            AgentTurnFailureCode.UNAVAILABLE,
        }
        and retries_used < retry_limit
        and not cancelled
    )


def bounded_retry_delay_ms(*, retry_index: int, remaining_ms: int) -> int:
    """Return the existing capped exponential backoff for an admitted retry.

    retry_index is one-based and already consumes the Run's retry budget.
    """
    if type(retry_index) is not int or retry_index < 1:
        raise ValueError("Provider retry index must be positive")
    if type(remaining_ms) is not int or remaining_ms <= 1:
        raise ValueError("Provider retry requires remaining wall time above one millisecond")
    return min(2_000, 250 * (2 ** min(retry_index - 1, 3)), max(0, remaining_ms - 1))
