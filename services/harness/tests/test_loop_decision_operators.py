"""Pure decision operators extracted from the real Harness Agent loop.

Finite differential exploration checks branch ordering against the original
loop formulas. It does not substitute for Provider/Runtime effect verification.
"""
from __future__ import annotations

from itertools import product
import unittest

from ordivon_harness.ordivon.model import AgentTurnDispatchSafety, AgentTurnFailureCode
from ordivon_harness.ordivon.provider_retry_policy import (
    bounded_retry_delay_ms,
    pre_dispatch_retry_permitted,
)
from ordivon_harness.ordivon.run_deadline_selection import select_run_deadline


class RunDeadlineDecisionTests(unittest.TestCase):
    def test_finite_arbitration_matches_original_loop(self) -> None:
        checked = 0
        for remaining, prior, wall, assignment, start, external_delta in product(
            (0, 1, 9, 500),
            (0, 27),
            (0, 60),
            (None, 0, 30, 120),
            (0, 500),
            (None, -20, 0, 1, 200, 600),
        ):
            # Independent verbatim oracle for the previous _run deadline rules.
            ar = None if assignment is None else max(0, assignment - wall)
            rr = remaining
            src = "active_wall_time"
            if ar is not None and ar <= rr:
                rr, src = ar, "assignment_deadline"
            expiration = start + rr
            external = None if external_delta is None else start + external_delta
            if external is not None and external <= expiration:
                expiration = external
                rr, src = max(0, expiration - start), "external_deadline"
            actual = select_run_deadline(
                active_remaining_ms=remaining,
                prior_elapsed_ms=prior,
                observed_wall_time_ms=wall,
                assignment_deadline_ms=assignment,
                started_at_ms=start,
                external_deadline_expires_at_ms=external,
            )
            self.assertEqual(
                (
                    actual.expires_at_ms,
                    actual.remaining_ms,
                    actual.total_wall_budget_ms,
                    actual.source,
                    actual.assignment_remaining_ms,
                ),
                (expiration, rr, prior + rr, src, ar),
            )
            checked += 1
        self.assertEqual(checked, 768)
        with self.assertRaisesRegex(ValueError, "negative time"):
            select_run_deadline(
                active_remaining_ms=1,
                prior_elapsed_ms=0,
                observed_wall_time_ms=-1,
                assignment_deadline_ms=None,
                started_at_ms=0,
                external_deadline_expires_at_ms=None,
            )


class ProviderRetryDecisionTests(unittest.TestCase):
    def test_retry_gate_matches_original_failure_and_dispatch_policy(self) -> None:
        checked = 0
        for safety, failure, retries, limit, cancelled, remaining in product(
            tuple(AgentTurnDispatchSafety),
            tuple(AgentTurnFailureCode),
            (0, 1, 4),
            (0, 2, 5),
            (False, True),
            (0, 1, 2, 9, 2000),
        ):
            previous = (
                safety is AgentTurnDispatchSafety.PRE_DISPATCH_SAFE
                and failure in {
                    AgentTurnFailureCode.TRANSPORT_FAILED,
                    AgentTurnFailureCode.UNAVAILABLE,
                }
                and retries < limit
                and not cancelled
                and remaining > 1
            )
            actual = pre_dispatch_retry_permitted(
                dispatch_safety=safety,
                failure_code=failure,
                retries_used=retries,
                retry_limit=limit,
                cancelled=cancelled,
            ) and remaining > 1
            self.assertEqual(previous, actual)
            checked += 1
        self.assertGreaterEqual(checked, 200)
        for index, remaining in product((1, 2, 3, 4, 8, 30), (2, 10, 250, 1000, 9999)):
            self.assertEqual(
                bounded_retry_delay_ms(retry_index=index, remaining_ms=remaining),
                min(2000, 250 * (2 ** min(index - 1, 3)), max(0, remaining - 1)),
            )
        with self.assertRaises(ValueError):
            bounded_retry_delay_ms(retry_index=0, remaining_ms=1000)
        with self.assertRaises(ValueError):
            bounded_retry_delay_ms(retry_index=1, remaining_ms=1)


if __name__ == "__main__":
    unittest.main()
