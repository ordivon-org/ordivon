#!/usr/bin/env python3
"""Constructive L0->L1 computational-lift witness for a deterministic toggle system."""

from __future__ import annotations

import hashlib
import json
from typing import Any


TRANSITIONS = {
    "OFF": {
        "read": {"next": "OFF", "output": "off"},
        "toggle": {"next": "ON", "output": "toggled"},
    },
    "ON": {
        "read": {"next": "ON", "output": "on"},
        "toggle": {"next": "OFF", "output": "toggled"},
    },
}


def run_history(history: list[str], final_input: str) -> dict[str, Any]:
    state = "OFF"
    trace: list[dict[str, str]] = []
    for action in history + [final_input]:
        step = TRANSITIONS[state][action]
        trace.append({"state": state, "input": action, "output": step["output"], "next": step["next"]})
        state = step["next"]
    return {"history": history, "finalInput": final_input, "finalOutput": trace[-1]["output"], "trace": trace}


def lift_pilot() -> dict[str, Any]:
    left = run_history([], "read")
    right = run_history(["toggle"], "read")
    if left["finalInput"] != right["finalInput"] or left["finalOutput"] == right["finalOutput"]:
        raise AssertionError("history-dependence witness not established")

    witness = {
        "sameExplicitInput": "read",
        "historyA": left,
        "historyB": right,
        "observationA": left["finalOutput"],
        "observationB": right["finalOutput"],
    }
    witness_digest = "sha256:" + hashlib.sha256(
        json.dumps(witness, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    model = {
        "states": ["OFF", "ON"],
        "initialState": "OFF",
        "inputAlphabet": ["read", "toggle"],
        "transitions": TRANSITIONS,
    }
    model_digest = "sha256:" + hashlib.sha256(
        json.dumps(model, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    certificate = {
        "schemaVersion": 1,
        "kind": "ordivon.computational-lift-certificate-v1",
        "certificateId": "lift:l0-to-l1-toggle-r3",
        "subjectRef": "synthetic-system:deterministic-toggle-r3",
        "lowerModelClass": "L0_STATELESS_RELATION",
        "higherModelClass": "L1_FINITE_STATE_TRANSDUCER",
        "standing": "CERTIFIED_LIFT",
        "basis": "DISTINGUISHING_LANGUAGE",
        "witnessRefs": [f"evidence:history-dependence@{witness_digest}", f"evidence:finite-model@{model_digest}"],
        "completenessEvidenceRefs": [],
        "assumptions": [
            "The L0 comparator is deterministic and has no hidden state outside the explicit input.",
            "The observer compares the same explicit input symbol after different replayable histories.",
            "The supplied two-state transition table is the complete synthetic subject definition.",
        ],
        "bounds": {
            "constructedStateCount": 2,
            "inputAlphabet": ["read", "toggle"],
            "distinguishingHistoryDepth": 1,
        },
        "universalDecisionProcedureClaimed": False,
        "nonClaims": [
            "This certificate establishes only the synthetic subject's L0->L1 lift under explicit assumptions.",
            "It does not establish any L2+ data, stack, counter, FIFO, or universal computation capability.",
            "It is not a general computational-power decision procedure.",
        ],
    }
    return {
        "certificate": certificate,
        "historyDependenceWitness": witness,
        "constructedFiniteStateModel": model,
        "historyDependenceWitnessDigest": witness_digest,
        "constructedFiniteStateModelDigest": model_digest,
    }


def lift_certificate() -> dict[str, Any]:
    return lift_pilot()["certificate"]
