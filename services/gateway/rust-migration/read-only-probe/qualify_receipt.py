"""Source-derived receipt oracle, keeping producer dimensions independent."""

from __future__ import annotations

import random

from qualify_semantics import descriptor, independent_descriptor

from ordivon_gateway.logic.execution_refs import GatewayError, parse_execution_ref
from ordivon_gateway.logic.owner_protocol import (
    _owner_optional_disposition,
    _owner_receipt_state,
    _required_bool,
)


def oracle(ref, observation, inspection):
    def unknown(reason):
        return {"standing": "unobserved", "reason": reason}

    try:
        owner, native_id = parse_execution_ref(ref)
    except GatewayError:
        return unknown("invalid_operation_ref")
    if observation.get("jobId") != native_id:
        return unknown("mismatched_job_identity")
    try:
        state = _owner_receipt_state(observation)
    except GatewayError:
        return unknown("invalid_state")
    try:
        terminal = _required_bool(observation, "executionTerminal")
    except GatewayError:
        return unknown("invalid_terminality")
    try:
        delivery = _owner_optional_disposition(observation, "deliveryDisposition")
        execution = _owner_optional_disposition(observation, "executionDisposition")
    except GatewayError:
        return unknown("invalid_disposition")
    exit_code = observation.get("exitCode")
    if exit_code is not None and (type(exit_code) is not int or not -(2**31) <= exit_code < 2**31):
        return unknown("invalid_exit_code")
    count = None
    if inspection is not None:
        if inspection.get("job", {}).get("jobId") != native_id:
            return unknown("mismatched_inspection_identity")
        count = inspection.get("artifacts", {}).get("count")

    def optional_bool(key):
        v = observation.get(key)
        return v if type(v) is bool else None

    return {
        "standing": "reported",
        "owner": owner,
        "native_id": native_id,
        "state": state,
        "attempt_state": observation.get("attemptState"),
        "terminal": terminal,
        "delivery_disposition": delivery,
        "execution_disposition": execution,
        "exit_code": exit_code,
        "result_available": optional_bool("resultAvailable"),
        "recovery_required": optional_bool("recoveryRequired"),
        "semantic_completion_evaluated": optional_bool("semanticCompletionEvaluated"),
        "artifacts_available": optional_bool("artifactsAvailable"),
        "artifacts": independent_descriptor(observation, count),
    }


def add_receipt_cases(add):
    ref = "ordivon-exec:v1:runtime.linux:job-a"
    base = {
        "jobId": "job-a",
        "status": "working",
        "attemptState": "running",
        "executionTerminal": False,
        "artifacts": [descriptor(1)],
    }
    summary = {"job": {"jobId": "job-a"}, "artifacts": {"count": 1}}

    def case(obs, inspection, reference=ref):
        add(
            "owner_receipt",
            {"operationRef": reference, "observation": obs, "inspection": inspection},
            oracle(reference, obs, inspection),
        )

    for key in (
        "jobId",
        "status",
        "attemptState",
        "executionTerminal",
        "deliveryDisposition",
        "executionDisposition",
        "exitCode",
        "resultAvailable",
        "semanticCompletionEvaluated",
        "recoveryRequired",
        "artifactsAvailable",
    ):
        for value in (None, "", True, False, 1, 1.0, -1, 2**32, [], {}, "future-state"):
            case({**base, key: value}, summary)
    for reference in ("", "ordivon-exec:v2:runtime.linux:job-a", "ordivon-exec:v1:host:job-a"):
        case(base, summary, reference)
    for inspection in (None, {}, {"job": {"jobId": "other"}}, summary):
        case(base, inspection)
    rng = random.Random(20261127)
    for _ in range(512):
        obs = {
            **base,
            "status": rng.choice(("queued", "working", "succeeded", "lost", "future")),
            "attemptState": rng.choice(("accepted", "starting", "running", "lost", "future")),
            "executionTerminal": rng.choice((True, False)),
            "resultAvailable": rng.choice((True, False, None)),
            "semanticCompletionEvaluated": rng.choice((True, False, None)),
            "recoveryRequired": rng.choice((True, False, None)),
            "deliveryDisposition": rng.choice(("committed", "unknown", "in_progress", None)),
            "exitCode": rng.choice((0, 1, -1, None)),
        }
        case(obs, rng.choice((summary, None, {"job": {"jobId": "other"}})))
