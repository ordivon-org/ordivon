"""Stateful qualification of the archived v1 receipt, not the live Runtime."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from ordivon_studio.models import _validator
from ordivon_studio.runtime_receipt_validation import _validate_runtime_receipt

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = json.loads(
    (ROOT / "productions/runtime-introduction/evidence/runtime-demo.receipt.json").read_bytes()
)
SCHEMA = _validator("runtime-demo-receipt.schema.json")


class ArchivedReceiptMachine(RuleBasedStateMachine):
    """The model owns valid observations and an independent set of corrupt rows.

    Each generated operation changes a physical receipt candidate. The terminal
    snapshot is derived from the model clock, not from corrupted observations.
    A selected corrupted row is invalid by construction; repairing all rows
    must recover acceptance. Duplicate historical observations are legal.
    """

    def __init__(self):
        super().__init__()
        self.attempt = RECEIPT["execution"]["attemptId"]
        self.total = 3
        self.clock = self.revision = self.completed = 0
        self.good = []
        self.observed = []
        self.corrupt = set()
        self.append_observation(0, 0, 0)

    def append_observation(self, dt, dr, ds):
        self.clock += dt
        self.revision += dr
        self.completed = min(self.total, self.completed + ds)
        row = {
            "status": "working", "attemptId": self.attempt,
            "elapsedMs": self.clock, "progressRevision": self.revision,
            "completedSteps": self.completed, "totalSteps": self.total,
        }
        if self.completed < self.total:
            row.update(currentStepIndex=self.completed, currentStepId=f"step-{self.completed}")
        self.good.append(row)
        self.observed.append(dict(row))

    @rule(dt=st.integers(0, 20), dr=st.integers(0, 3), ds=st.integers(0, 2))
    def advance(self, dt, dr, ds):
        self.append_observation(dt, dr, ds)

    @rule()
    def replay(self):
        index = len(self.observed) - 1
        self.good.append(dict(self.good[index]))
        self.observed.append(dict(self.observed[index]))
        if index in self.corrupt:
            self.corrupt.add(index + 1)

    @rule(data=st.data(), fault=st.sampled_from(
        ("foreign", "total", "premature", "step-index", "future-clock", "future-revision", "steps")
    ))
    def damage(self, data, fault):
        index = data.draw(st.integers(0, len(self.observed) - 1), label="observation")
        row = dict(self.good[index])
        changes = {
            "foreign": {"attemptId": "attempt-foreign"},
            "total": {"totalSteps": self.total + 1},
            "premature": {"status": "succeeded"},
            "step-index": {"currentStepIndex": self.total},
            "future-clock": {"elapsedMs": 1_000_000},
            "future-revision": {"progressRevision": 1_000_000},
            "steps": {"completedSteps": self.total + 1},
        }
        row.update(changes[fault])
        self.observed[index] = row
        self.corrupt.add(index)

    @rule(data=st.data())
    def repair(self, data):
        index = data.draw(st.integers(0, len(self.observed) - 1), label="repair")
        self.observed[index] = dict(self.good[index])
        self.corrupt.discard(index)

    @rule()
    def repair_all(self):
        self.observed = copy.deepcopy(self.good)
        self.corrupt.clear()

    @invariant()
    def actual_receipt_consumer_matches_model(self):
        receipt = copy.deepcopy(RECEIPT)
        terminal = {
            "status": "succeeded", "attemptId": self.attempt,
            "elapsedMs": self.clock + 1, "progressRevision": self.revision + 1,
            "completedSteps": self.total, "totalSteps": self.total, "exitCode": 0,
        }
        receipt["execution"]["elapsedMs"] = terminal["elapsedMs"]
        receipt["execution"]["observations"] = [*copy.deepcopy(self.observed), terminal]
        # Every generated corruption remains shape-valid: semantic rejection
        # cannot be attributed to collection/import or schema failure.
        assert SCHEMA.is_valid(receipt)
        errors = _validate_runtime_receipt(Path("generated-receipt.json"), receipt)
        assert bool(errors) == bool(self.corrupt), (self.corrupt, errors)


TestArchivedReceipt = ArchivedReceiptMachine.TestCase
TestArchivedReceipt.settings = settings(
    max_examples=80, stateful_step_count=20, deadline=None, derandomize=True, database=None,
)
