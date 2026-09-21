from __future__ import annotations

# The recovered MVP is intentionally an experiment-local package, so the test
# adds that package root before importing it.
# ruff: noqa: E402
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = ROOT / "experiments" / "chaoxing-autosign-mvp"
sys.path.insert(0, str(PKG_ROOT))

from chaoxing_mvp.adapters import (
    DisabledSubmissionAdapter,
    FakeAcceptedSubmission,
    FakeDiscovery,
    FakeSession,
)
from chaoxing_mvp.engine import AutoSignEngine
from chaoxing_mvp.ledger import ActivityLedger
from chaoxing_mvp.models import (
    ActionResult,
    Activity,
    ActivityIdentity,
    ActivityKind,
    ActivityState,
    CourseIdentity,
    ParseOutcome,
    SemanticOutcome,
    TransportOutcome,
)
from chaoxing_mvp.ports import Ports


class CapturingNotifier:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def notify(self, title: str, message: str) -> None:
        self.messages.append((title, message))


class ChaoxingAutoSignMvpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = ActivityLedger(Path(self.tmp.name) / "ledger.sqlite3")
        self.account = "acct-a"
        self.course = CourseIdentity(self.account, "course-1", "class-a", "Course")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def activity(
        self, activity_id: str, kind: ActivityKind, requirements=()
    ) -> Activity:
        return Activity(
            identity=ActivityIdentity(
                self.account,
                self.course.course_id,
                self.course.class_id,
                activity_id,
                "synthetic",
            ),
            kind=kind,
            verification_requirements=tuple(requirements),
        )

    def engine(self, activities, submission=None, notifier=None) -> AutoSignEngine:
        return AutoSignEngine(
            Ports(
                session=FakeSession(self.account),
                discovery=FakeDiscovery(
                    [self.course], {self.course.key: list(activities)}
                ),
                submission=submission or FakeAcceptedSubmission(),
                notifier=notifier or CapturingNotifier(),
            ),
            self.ledger,
        )

    def test_normal_authorized_path_reaches_confirmed_success(self):
        activity = self.activity("a1", ActivityKind.NORMAL)
        stats = self.engine([activity]).scan_once()
        record = self.ledger.get(activity.identity)
        self.assertEqual(ActivityState.CONFIRMED_SUCCESS, record.state)
        self.assertEqual(1, record.attempt_count)
        self.assertEqual(1, stats.confirmed)

    def test_confirmed_activity_is_idempotent_on_next_scan(self):
        activity = self.activity("a1", ActivityKind.NORMAL)
        engine = self.engine([activity])
        first = engine.scan_once()
        second = engine.scan_once()
        self.assertEqual(1, first.confirmed)
        self.assertEqual(0, second.activities_processed)
        self.assertEqual(1, self.ledger.get(activity.identity).attempt_count)

    def test_qr_activity_requires_user_action_and_never_submits(self):
        activity = self.activity("qr1", ActivityKind.QR_REQUIRED, ["qr"])
        submitter = FakeAcceptedSubmission()
        notifier = CapturingNotifier()
        stats = self.engine([activity], submitter, notifier).scan_once()
        record = self.ledger.get(activity.identity)
        self.assertEqual(ActivityState.USER_ACTION_REQUIRED, record.state)
        self.assertEqual(set(), submitter.submitted)
        self.assertEqual(1, stats.user_action_required)
        self.assertEqual(1, len(notifier.messages))

    def test_disabled_submitter_fails_retryably_not_successfully(self):
        activity = self.activity("a1", ActivityKind.NORMAL)
        self.engine([activity], DisabledSubmissionAdapter()).scan_once()
        record = self.ledger.get(activity.identity)
        self.assertEqual(ActivityState.FAILED_RETRYABLE, record.state)
        self.assertEqual(1, record.attempt_count)

    def test_same_course_different_class_produces_distinct_identity(self):
        other = CourseIdentity(self.account, "course-1", "class-b", "Course")
        a = self.activity("a1", ActivityKind.NORMAL)
        b = Activity(
            identity=ActivityIdentity(
                self.account, other.course_id, other.class_id, "a1", "synthetic"
            ),
            kind=ActivityKind.NORMAL,
        )
        self.ledger.observe(a)
        self.ledger.observe(b)
        self.assertNotEqual(a.identity.key, b.identity.key)
        self.assertEqual(ActivityState.DISCOVERED, self.ledger.get(a.identity).state)
        self.assertEqual(ActivityState.DISCOVERED, self.ledger.get(b.identity).state)

    def test_recovery_verifies_submitting_before_resubmit(self):
        activity = self.activity("recover1", ActivityKind.NORMAL)
        self.ledger.observe(activity)
        self.ledger.transition(
            activity.identity,
            ActivityState.SUBMITTING,
            increment_attempt=True,
            detail="synthetic crash after external effect may have committed",
        )

        class RecoverySubmission:
            def __init__(self) -> None:
                self.submit_calls = 0
                self.verify_calls = 0

            def submit(self, activity):
                self.submit_calls += 1
                raise AssertionError("recovery must verify before resubmitting")

            def verify(self, identity):
                self.verify_calls += 1
                return True

        submission = RecoverySubmission()
        stats = self.engine([activity], submission).scan_once()

        self.assertEqual(0, submission.submit_calls)
        self.assertEqual(1, submission.verify_calls)
        self.assertEqual(
            ActivityState.CONFIRMED_SUCCESS, self.ledger.get(activity.identity).state
        )
        self.assertEqual(1, self.ledger.get(activity.identity).attempt_count)
        self.assertEqual(1, stats.confirmed)

    def test_recovery_false_marks_retryable_without_resubmit_in_same_scan(self):
        activity = self.activity("recover-false", ActivityKind.NORMAL)
        self.ledger.observe(activity)
        self.ledger.transition(
            activity.identity, ActivityState.SUBMITTED, increment_attempt=True
        )

        class RecoverySubmission:
            def __init__(self) -> None:
                self.submit_calls = 0
                self.verify_calls = 0

            def submit(self, activity):
                self.submit_calls += 1
                raise AssertionError("recovery scan must not resubmit")

            def verify(self, identity):
                self.verify_calls += 1
                return False

        submission = RecoverySubmission()
        stats = self.engine([activity], submission).scan_once()

        self.assertEqual(0, submission.submit_calls)
        self.assertEqual(1, submission.verify_calls)
        self.assertEqual(
            ActivityState.FAILED_RETRYABLE, self.ledger.get(activity.identity).state
        )
        self.assertEqual(1, self.ledger.get(activity.identity).attempt_count)
        self.assertEqual(1, stats.retryable_failures)

    def test_recovery_unknown_never_resubmits(self):
        activity = self.activity("recover-unknown", ActivityKind.NORMAL)
        self.ledger.observe(activity)
        self.ledger.transition(
            activity.identity, ActivityState.VERIFYING, increment_attempt=True
        )

        class RecoverySubmission:
            def __init__(self) -> None:
                self.submit_calls = 0
                self.verify_calls = 0

            def submit(self, activity):
                self.submit_calls += 1
                raise AssertionError("unknown recovery must not resubmit")

            def verify(self, identity):
                self.verify_calls += 1
                return None

        submission = RecoverySubmission()
        stats = self.engine([activity], submission).scan_once()

        self.assertEqual(0, submission.submit_calls)
        self.assertEqual(1, submission.verify_calls)
        self.assertEqual(
            ActivityState.UNKNOWN, self.ledger.get(activity.identity).state
        )
        self.assertEqual(1, self.ledger.get(activity.identity).attempt_count)
        self.assertEqual(1, stats.retryable_failures)

    def test_parse_failure_cannot_be_treated_as_terminal_semantic_rejection(self):
        activity = self.activity("parse-failed", ActivityKind.NORMAL)

        class InconsistentSubmission:
            def submit(self, activity):
                return ActionResult(
                    transport=TransportOutcome.OK,
                    parse=ParseOutcome.FAILED,
                    semantic=SemanticOutcome.REJECTED,
                    detail="unparseable response carried an untrusted rejection marker",
                )

            def verify(self, identity):
                raise AssertionError(
                    "unparseable submission result must not enter verify"
                )

        stats = self.engine([activity], InconsistentSubmission()).scan_once()
        record = self.ledger.get(activity.identity)

        self.assertEqual(ActivityState.UNKNOWN, record.state)
        self.assertEqual(1, record.attempt_count)
        self.assertEqual(1, stats.retryable_failures)
        self.assertEqual(0, stats.terminal_failures)

    def test_unknown_activity_fails_closed(self):
        activity = self.activity("x1", ActivityKind.UNKNOWN)
        submitter = FakeAcceptedSubmission()
        self.engine([activity], submitter).scan_once()
        self.assertEqual(
            ActivityState.FAILED_TERMINAL, self.ledger.get(activity.identity).state
        )
        self.assertEqual(set(), submitter.submitted)


if __name__ == "__main__":
    unittest.main()


class RunnerTests(unittest.TestCase):
    def test_runner_backoff_resets_after_success(self):
        from chaoxing_mvp.runner import MonitorRunner, RunnerConfig

        class FlakyEngine:
            def __init__(self):
                self.calls = 0
                self.ports = type("P", (), {"notifier": CapturingNotifier()})()

            def scan_once(self):
                self.calls += 1
                if self.calls == 1:
                    raise RuntimeError("synthetic network failure")
                runner.stop()
                return type("Stats", (), {})()

        sleeps = []
        engine = FlakyEngine()
        runner = MonitorRunner(
            engine,
            RunnerConfig(
                poll_seconds=1,
                jitter_seconds=0,
                backoff_initial_seconds=2,
                backoff_max_seconds=8,
            ),
            sleeper=lambda seconds: sleeps.append(seconds),
        )
        runner.run_forever()
        self.assertEqual(2, engine.calls)
        self.assertEqual([1.0, 1.0], sleeps)
        self.assertEqual(1, len(engine.ports.notifier.messages))
