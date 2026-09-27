#!/usr/bin/env python3
"""Bounded heterogeneous synthetic digital world for Capability Science R2.

The world is deliberately local and deterministic.  Components expose typed affordances;
composition search enumerates legal paths without treating provider names as semantic truth.
No network access, external target, authority grant, or exploit behavior is involved.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from itertools import product
from typing import Any, Iterable

from semantic_novelty_oracle_r1 import novelty_report


PAYLOAD = "Payload"
TARGET = "Target"
HANDLE = "Handle"


@dataclass(frozen=True)
class ActionSpec:
    name: str
    input_type: str
    output_type: str
    persistent_effect: bool = False


ACTIONS: tuple[ActionSpec, ...] = (
    ActionSpec("echo", PAYLOAD, PAYLOAD),
    ActionSpec("encode", PAYLOAD, TARGET),
    ActionSpec("publish", TARGET, HANDLE, persistent_effect=True),
    ActionSpec("resolve", HANDLE, TARGET),
    ActionSpec("render", TARGET, PAYLOAD),
)


class SyntheticWorld:
    """Small deterministic service ecosystem with persistent redirect state."""

    def __init__(self) -> None:
        self._redirects: dict[str, str] = {}
        self._counter = 0

    def reset(self) -> None:
        self._redirects.clear()
        self._counter = 0

    def snapshot(self) -> dict[str, Any]:
        return {"redirectCount": len(self._redirects), "handles": sorted(self._redirects)}

    def execute(self, action: str, value: str) -> str:
        if action == "echo":
            return value
        if action == "encode":
            encoded = base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii")
            return f"data:text/plain;base64,{encoded}"
        if action == "publish":
            self._counter += 1
            handle = f"h{self._counter:04d}"
            self._redirects[handle] = value
            return handle
        if action == "resolve":
            if value not in self._redirects:
                raise KeyError(f"unknown handle: {value}")
            return self._redirects[value]
        if action == "render":
            prefix = "data:text/plain;base64,"
            if not value.startswith(prefix):
                raise ValueError("synthetic renderer only accepts typed data targets")
            return base64.urlsafe_b64decode(value[len(prefix):].encode("ascii")).decode("utf-8")
        raise KeyError(f"unknown action: {action}")


def path_id(path: Iterable[ActionSpec]) -> str:
    names = [item.name for item in path]
    digest = hashlib.sha256("->".join(names).encode("utf-8")).hexdigest()[:16]
    return f"path:{digest}"


def path_names(path: Iterable[ActionSpec]) -> list[str]:
    return [item.name for item in path]


def run_path(world: SyntheticWorld, path: tuple[ActionSpec, ...], value: str) -> tuple[str, list[dict[str, Any]]]:
    current = value
    trace: list[dict[str, Any]] = []
    for spec in path:
        before = current
        before_state = world.snapshot()
        current = world.execute(spec.name, current)
        trace.append(
            {
                "action": spec.name,
                "inputType": spec.input_type,
                "outputType": spec.output_type,
                "persistentEffectDeclared": spec.persistent_effect,
                "input": before,
                "output": current,
                "worldBefore": before_state,
                "worldAfter": world.snapshot(),
            }
        )
    return current, trace


def enumerate_typed_paths(start_type: str, max_len: int = 3) -> list[tuple[ActionSpec, ...]]:
    """Enumerate all non-empty type-correct paths up to max_len."""
    frontier: list[tuple[str, tuple[ActionSpec, ...]]] = [(start_type, tuple())]
    results: list[tuple[ActionSpec, ...]] = []
    for _ in range(max_len):
        next_frontier: list[tuple[str, tuple[ActionSpec, ...]]] = []
        for current_type, path in frontier:
            for action in ACTIONS:
                if action.input_type != current_type:
                    continue
                new_path = path + (action,)
                results.append(new_path)
                next_frontier.append((action.output_type, new_path))
        frontier = next_frontier
    return results


def end_type(path: tuple[ActionSpec, ...]) -> str:
    return path[-1].output_type


def start_type(path: tuple[ActionSpec, ...]) -> str:
    return path[0].input_type


def find_persistent_roundtrips(max_len: int = 3) -> list[dict[str, Any]]:
    """Find typed A->B and B->A path pairs where the outward leg changes persistent state.

    The search is structural and does not name a target capability such as "memory".
    """
    types = sorted({a.input_type for a in ACTIONS} | {a.output_type for a in ACTIONS})
    by_pair: dict[tuple[str, str], list[tuple[ActionSpec, ...]]] = {}
    for source in types:
        for path in enumerate_typed_paths(source, max_len=max_len):
            by_pair.setdefault((source, end_type(path)), []).append(path)

    found: list[dict[str, Any]] = []
    for source, boundary in product(types, repeat=2):
        outward = by_pair.get((source, boundary), [])
        inward = by_pair.get((boundary, source), [])
        for store_path in outward:
            if not any(action.persistent_effect for action in store_path):
                continue
            for recover_path in inward:
                found.append(
                    {
                        "sourceType": source,
                        "boundaryType": boundary,
                        "storePath": store_path,
                        "recoverPath": recover_path,
                        "storePathId": path_id(store_path),
                        "recoverPathId": path_id(recover_path),
                        "totalActions": len(store_path) + len(recover_path),
                    }
                )
    found.sort(
        key=lambda item: (
            item["totalActions"],
            item["sourceType"],
            item["boundaryType"],
            path_names(item["storePath"]),
            path_names(item["recoverPath"]),
        )
    )
    return found


def _selected_payload_roundtrip(roundtrips: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [
        item for item in roundtrips
        if item["sourceType"] == PAYLOAD and item["boundaryType"] == HANDLE
    ]
    if not candidates:
        raise AssertionError("no Payload->Handle->Payload persistent roundtrip discovered")
    return candidates[0]


def evaluate_selected_roundtrip(payload: str = "ordivon-capability-science-r2") -> dict[str, Any]:
    roundtrips = find_persistent_roundtrips(max_len=3)
    selected = _selected_payload_roundtrip(roundtrips)
    store_path: tuple[ActionSpec, ...] = selected["storePath"]
    recover_path: tuple[ActionSpec, ...] = selected["recoverPath"]

    world = SyntheticWorld()
    handle, store_trace = run_path(world, store_path, payload)
    recovered_same_session, recover_trace = run_path(world, recover_path, handle)

    # "fresh session" deliberately discards every local intermediate except the portable
    # boundary handle while preserving external service state.
    recovered_fresh_session, fresh_trace = run_path(world, recover_path, str(handle))

    candidate_id_seed = {
        "store": path_names(store_path),
        "recover": path_names(recover_path),
        "types": [selected["sourceType"], selected["boundaryType"]],
    }
    candidate_digest = hashlib.sha256(
        json.dumps(candidate_id_seed, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:20]
    candidate_id = f"cap:synthetic-roundtrip:{candidate_digest}"

    observation_policy = {
        "policyId": "observation-policy:synthetic-heterogeneous-roundtrip-r2",
        "contexts": ["direct_use", "recover_after_local_forget", "recover_in_fresh_session"],
    }
    library = [
        {
            "capabilityId": "cap:stateless-echo",
            "evidenceRefs": ["evidence:synthetic-world-r2:echo"],
            "observations": {
                "direct_use": {"returnsPayload": True, "returnsHandle": False},
                "recover_after_local_forget": {"payloadRecovered": False},
                "recover_in_fresh_session": {"payloadRecovered": False},
            },
        },
        {
            "capabilityId": "cap:persistent-target-handle-only",
            "evidenceRefs": ["evidence:synthetic-world-r2:publish-resolve"],
            "observations": {
                "direct_use": {"returnsPayload": False, "returnsHandle": True},
                "recover_after_local_forget": {"payloadRecovered": False},
                "recover_in_fresh_session": {"payloadRecovered": False},
            },
        },
    ]
    candidate = {
        "capabilityId": candidate_id,
        "evidenceRefs": ["evidence:synthetic-world-r2:closed-loop"],
        "observations": {
            "direct_use": {"returnsPayload": False, "returnsHandle": isinstance(handle, str)},
            "recover_after_local_forget": {"payloadRecovered": recovered_same_session == payload},
            "recover_in_fresh_session": {"payloadRecovered": recovered_fresh_session == payload},
        },
    }
    novelty_input = {
        "schemaVersion": 1,
        "kind": "ordivon.capability-science-synthetic-novelty-input-r2",
        "observationPolicy": observation_policy,
        "library": library,
        "candidate": candidate,
    }
    novelty = novelty_report(novelty_input)

    return {
        "schemaVersion": 1,
        "kind": "ordivon.capability-science-synthetic-world-r2",
        "standing": "BOUNDED_HETEROGENEOUS_DISCOVERY_LOOP_EXECUTED",
        "components": [
            {
                "action": action.name,
                "inputType": action.input_type,
                "outputType": action.output_type,
                "persistentEffectDeclared": action.persistent_effect,
            }
            for action in ACTIONS
        ],
        "enumeratedRoundtripCount": len(roundtrips),
        "selectedCircuit": {
            "sourceType": selected["sourceType"],
            "boundaryType": selected["boundaryType"],
            "storePath": path_names(store_path),
            "recoverPath": path_names(recover_path),
            "storePathId": selected["storePathId"],
            "recoverPathId": selected["recoverPathId"],
        },
        "observations": candidate["observations"],
        "novelty": novelty,
        "traces": {
            "store": store_trace,
            "recoverAfterLocalForget": recover_trace,
            "recoverInFreshSession": fresh_trace,
        },
        "authorityGranted": False,
        "executionAuthorityGranted": False,
        "domainAcceptanceEstablished": False,
        "nonClaims": [
            "The synthetic world is local, deterministic, and bounded; it is not evidence about arbitrary Internet services.",
            "Typed path enumeration is a bounded candidate generator, not a universal closure search.",
            "The novelty verdict is relative to the finite R2 observation policy and baseline library.",
            "No capability discovery grants authority, permission, or production deployment standing.",
        ],
    }
