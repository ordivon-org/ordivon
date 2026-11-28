"""Finite differential model for the native historical archive projection.

The oracle operates on declared fixture facts, not SQL or production helpers.
Every single blocker and every unordered pair is covered in each schema era.
The same fixture facts are projected in forward/reverse insertion order.
"""
from collections import Counter
from contextlib import closing
from itertools import combinations
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

import test_archive as fixtures

NOW = 1_000_000_000
CUTOFF = NOW - 3_600_000

# Ordered policy from the archive observation contract, not query-plan order.
BLOCKERS = (
    ("unresolved", "unresolved"),
    ("lost", "repairable_terminal"),
    ("unsupported", "unsupported_resolution"),
    ("cutoff", "younger_than_minimum_age"),
    ("release", "runtime_release_effect"),
    ("foreign_pointer", "current_attempt_invalid"),
    ("missing_pointer", "current_attempt_invalid"),
    ("missing_attempt", "attempt_missing"),
    ("running", "attempt_not_stable_terminal"),
    ("null_state", "attempt_not_stable_terminal"),
    ("recovery", "recovery_required_or_unknown"),
    ("held", "active_or_held_reservation"),
    ("missing_reservation", "reservation_missing_or_unknown"),
    ("unknown_reservation", "reservation_missing_or_unknown"),
    ("duplicate_reservation", "reservation_missing_or_unknown"),
    ("owner", "supervisor_owner_present"),
)
# Conflicting mutations to the same field or mutations of deleted attempts
# cannot be composed as independent facts. Exclude them explicitly.
CONFLICTS = (
    {"unresolved", "lost", "unsupported"},
    {"running", "null_state"},
    {"foreign_pointer", "missing_pointer"},
    {"held", "missing_reservation", "unknown_reservation", "duplicate_reservation"},
)


def cases():
    yield frozenset()
    names = [name for name, _ in BLOCKERS]
    for name in names:
        yield frozenset((name,))
    for pair in combinations(names, 2):
        faults = frozenset(pair)
        if any(faults <= conflict for conflict in CONFLICTS):
            continue
        if "missing_attempt" in faults and faults & {
            "running", "null_state", "recovery", "held", "missing_reservation",
            "unknown_reservation", "duplicate_reservation", "owner",
        }:
            continue
        yield faults


def expected_classification(faults):
    return next((label for name, label in BLOCKERS if name in faults), "eligible")


def populate(connection, migration, reverse):
    rows = [(i, f) for i, f in enumerate(cases())]
    # Extra eligible rows vary fanout, timestamps and pointer representation.
    rows.extend((1000 + i, frozenset()) for i in range(24))
    if reverse:
        rows.reverse()
    expected = Counter()
    sample = []
    closure = dict.fromkeys((
        "jobs", "attempts", "idempotencyKeys", "reservations", "events",
        "artifacts", "conditions", "executionProviders", "hostDependencies",
        "supervisorOwners", "artifactLogicalPayloadBytes", "jobJsonLogicalBytes",
    ), 0)
    markers = []
    for i, faults in rows:
        job = f"job:{i:04}"
        latest = f"attempt:{job}"
        older = f"older:{job}"
        created = CUTOFF if "cutoff" in faults else 1 + i % 5
        resolution = None if "unresolved" in faults else (
            "lost" if "lost" in faults else "future-state" if "unsupported" in faults
            else ("succeeded", "failed", "cancelled", "timed_out")[i % 4]
        )
        fixtures.add_job(connection, job, created_at_ms=created, resolution=resolution,
                         current_pointer=i % 2 == 0, release_effect="release" in faults)
        # Every non-deleted Job has two Attempts and variable relation fanout.
        connection.execute("INSERT INTO attempts VALUES (?,?,?,?,?,?)",
                           (older, job, 0, "succeeded", "/older", created))
        connection.execute("INSERT INTO concurrency_reservations VALUES (?,?,?)",
                           (f"reservation:{older}", older, "released"))
        plan = json.dumps({"args": ["中a文😀", str(i)]}, ensure_ascii=False)
        snapshot = json.dumps({"workspace": "路径"}, ensure_ascii=False)
        connection.execute("UPDATE jobs SET execution_plan_json=?,workspace_snapshot_json=? WHERE job_id=?",
                           (plan, snapshot, job))
        fanout = i % 4
        for k in range(fanout):
            connection.execute("INSERT INTO job_events VALUES (?,?,?,?,?)",
                               (f"extra-event:{job}:{k}", job, older, "{}", "sha256:"+"a"*64))
            connection.execute("INSERT INTO artifacts VALUES (?,?,?,?,?,?,?,?)",
                               (f"extra-artifact:{job}:{k}", job, older, "stderr", "x",
                                "sha256:"+"b"*64, "text/plain", k))
        if "foreign_pointer" in faults or "missing_pointer" in faults:
            pointer = "attempt:job:0000" if "foreign_pointer" in faults else "missing"
            connection.execute("UPDATE jobs SET current_attempt_id=? WHERE job_id=?", (pointer, job))
        if "missing_attempt" in faults:
            # Leave a null pointer so missing-attempt is distinguishable.
            connection.execute("DELETE FROM attempts WHERE job_id=?", (job,))
            if not faults & {"foreign_pointer", "missing_pointer"}:
                connection.execute("UPDATE jobs SET current_attempt_id=NULL WHERE job_id=?", (job,))
        if "running" in faults or "null_state" in faults:
            connection.execute("UPDATE attempts SET state=? WHERE attempt_id=?",
                               (None if "null_state" in faults else "running", older))
        if "recovery" in faults:
            markers.append(older)
            connection.execute("INSERT INTO attempt_conditions VALUES (?,?,?,?,?)",
                               (older, "recovery_required", "true", "fixture", "sha256:"+"c"*64))
        if "held" in faults or "unknown_reservation" in faults:
            connection.execute("UPDATE concurrency_reservations SET state=? WHERE attempt_id=?",
                               ("held_orphaned" if "held" in faults else None, older))
        if "missing_reservation" in faults:
            connection.execute("DELETE FROM concurrency_reservations WHERE attempt_id=?", (older,))
        if "duplicate_reservation" in faults:
            connection.execute("INSERT INTO concurrency_reservations VALUES (?,?,?)",
                               (f"duplicate:{older}", older, "released"))
        if "owner" in faults:
            connection.execute("INSERT INTO attempt_supervisor_owners VALUES (?,?,?)",
                               (older, "{}", "sha256:"+"d"*64))
        label = expected_classification(faults)
        expected[label] += 1
        if label == "eligible":
            sample.append((created, job, latest, latest if i % 2 == 0 else None))
            values = (1, 2, 1, 2, 1+fanout, 1+fanout, int(migration == 4), 1, 1,
                      0, 123+sum(range(fanout)), len(plan.encode())+len(snapshot.encode()))
            for key, value in zip(closure, values, strict=True):
                closure[key] += value
    if migration >= 5:
        fixtures.add_recovery_tuple_columns(connection)
        connection.executemany("UPDATE attempts SET recovery_required=1 WHERE attempt_id=?",
                               [(x,) for x in markers])
        connection.execute("DROP TABLE attempt_conditions")
        connection.execute("UPDATE schema_migrations SET version=?", (migration,))
    connection.commit()
    return dict(expected), closure, sorted(sample), len(rows)


class ArchiveModelTests(unittest.TestCase):
    def test_finite_fault_model_and_insertion_order(self):
        for migration in (4, 5, 6):
            reports = []
            for reverse in (False, True):
                with self.subTest(migration=migration, reverse=reverse), tempfile.TemporaryDirectory() as d:
                    db = Path(d) / "model.sqlite3"
                    fixtures.initialize_registry(db)
                    with closing(sqlite3.connect(db)) as c:
                        expected, closure, sample, count = populate(c, migration, reverse)
                    before = hashlib.sha256(db.read_bytes()).hexdigest()
                    completed = subprocess.run(
                        [sys.executable, str(fixtures.SCRIPT), "--database", str(db),
                         "--now-ms", str(NOW), "--minimum-age-hours", "1", "--sample-limit", "100"],
                        cwd=fixtures.REPO, text=True, capture_output=True, check=False, timeout=30)
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    report = json.loads(completed.stdout)
                    summary = report["summary"]
                    actual = fixtures.RuntimeArchiveInspectTests.classifications(report)
                    self.assertEqual(actual, expected)
                    self.assertEqual(summary["classifiedJobs"], count)
                    self.assertEqual(summary["eligibleClosure"], closure)
                    self.assertEqual(
                        [(x["createdAtMs"], x["jobId"], x["effectiveAttemptId"], x["jobCurrentAttemptId"])
                         for x in report["eligibleSample"]], sample)
                    self.assertEqual(hashlib.sha256(db.read_bytes()).hexdigest(), before)
                    self.assertFalse(report["boundaries"]["deletesHotHistory"])
                    reports.append((actual, summary["eligibleClosure"], report["eligibleSample"]))
            if len(reports) == 2:
                self.assertEqual(reports[0], reports[1])


if __name__ == "__main__":
    unittest.main()
