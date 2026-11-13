#!/usr/bin/env python3
"""Frozen-seed differential cases from real production Runtime delivery logic.
No Runtime Tool call or synthetic expected status."""
from __future__ import annotations

from copy import deepcopy
import random

from anc_canonical import canonical_bytes
from ordivon_harness.ordivon.runtime_bridge import _runtime_delivery_state
from ordivon_harness.runtime_port import HarnessRuntimeClientError

rng = random.Random(20261111)
base = [
    {"executionTerminal": True, "executionDisposition": "succeeded", "deliveryDisposition": "committed", "recoveryRequired": False, "resultAvailable": True, "semanticCompletionEvaluated": False},
    {"executionTerminal": True, "executionDisposition": "failed", "deliveryDisposition": "committed", "recoveryRequired": False, "resultAvailable": True, "semanticCompletionEvaluated": False},
    {"executionTerminal": True, "executionDisposition": "timed_out", "deliveryDisposition": "committed", "recoveryRequired": False, "resultAvailable": True, "semanticCompletionEvaluated": False},
    {"executionTerminal": True, "executionDisposition": "cancelled", "deliveryDisposition": "committed", "recoveryRequired": False, "resultAvailable": True, "semanticCompletionEvaluated": False},
    {"executionTerminal": True, "executionDisposition": "lost", "deliveryDisposition": "unknown", "recoveryRequired": False, "resultAvailable": True, "semanticCompletionEvaluated": False},
    {"executionTerminal": False, "executionDisposition": None, "deliveryDisposition": "in_progress", "recoveryRequired": False, "resultAvailable": False, "semanticCompletionEvaluated": False},
    {"executionTerminal": True, "executionDisposition": "succeeded", "deliveryDisposition": "reconciliation_required", "recoveryRequired": False, "resultAvailable": True, "semanticCompletionEvaluated": False},
    {"executionTerminal": True, "executionDisposition": "succeeded", "deliveryDisposition": "committed", "recoveryRequired": True, "resultAvailable": True, "semanticCompletionEvaluated": False},
]
fields = {
    "executionTerminal": [None, True, False, 0, 1, "true", [], {}],
    "executionDisposition": [None, "succeeded", "failed", "timed_out", "cancelled", "lost", "orphaned", "invalid", True, [], {}],
    "deliveryDisposition": [None, "committed", "reconciliation_required", "in_progress", "unknown", "bad", 0, False, []],
    "recoveryRequired": [None, True, False, 0, "false", {}, []],
    "resultAvailable": [None, True, False, 1, "false", {}, []],
    "semanticCompletionEvaluated": [None, False, True, 0, 1, "false", [], {}],
}
cases = []
for baseline in base:
    for legacy in [None, "succeeded", "failed", "cancelled", "unknown", 123, False, {"status": "succeeded"}]:
        data = deepcopy(baseline)
        data["status"] = legacy
        cases.append(data)
for baseline in base:
    for name, variants in fields.items():
        for replacement in variants:
            data = deepcopy(baseline)
            data[name] = replacement
            cases.append(data)
        data = deepcopy(baseline)
        del data[name]
        cases.append(data)
for _ in range(850):
    data = deepcopy(rng.choice(base))
    for name in rng.sample(list(fields), rng.randint(1, 4)):
        data[name] = rng.choice(fields[name])
    if rng.randrange(7) == 0:
        data["status"] = rng.choice(["succeeded", "failed", "running", "lost"])
    cases.append(data)
for value in cases:
    try:
        outcome = _runtime_delivery_state(value)
    except HarnessRuntimeClientError:
        outcome = "invalid"
    print("R\t" + outcome + "\t" + canonical_bytes(value).hex())
