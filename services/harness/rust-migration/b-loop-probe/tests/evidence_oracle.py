#!/usr/bin/env python3
"""Live Python-source oracle for run_recovery._advance_turn_evidence."""
from __future__ import annotations

import random
from anc_canonical import canonical_digest
from ordivon_harness.ordivon.model import AgentToolCall
from ordivon_harness.ordivon.run_contract import RunBudget
from ordivon_harness.agent_tool_observation import HarnessToolObservation
from ordivon_harness.ordivon.run_recovery import (
    _advance_turn_evidence,
    _observation_evidence_signature,
    _search_evidence,
)

rng = random.Random(26155)
only = frozenset({"search_workspace", "read_workspace", "read_artifact"})
for scenario in range(16):
    signatures: set[str] = set()
    search: dict[tuple[str, str], set[str]] = {}
    prior_n = 0
    prior_o = 0
    budget = RunBudget(
        max_model_calls=8, max_tool_calls=8,
        max_observation_bytes=1024, max_wall_time_ms=10_000,
        max_no_progress_turns=2 + scenario % 5,
        max_observation_only_turns=3 + scenario % 7,
    )
    for turn in range(40):
        index = scenario * 40 + turn
        tool = rng.choice(("search_workspace", "search_workspace",
                           "read_workspace", "read_artifact", "edit_workspace"))
        status = rng.choice(("observed", "observed", "observed", "observed",
                             "unknown", "rejected", "cancelled", "cancel-requested"))
        query = rng.choice(("rust", "lease", "provider"))
        path = rng.choice((".", "src", "src/a", "src/a/", "src2", "other"))
        code = rng.choice((0, 0, 1, 2))
        sample = {"path": rng.choice(("f1", "f2")), "line": rng.randrange(3)}
        if tool == "search_workspace" and turn % 3 == 0:
            queries = [query, "rust"]
            args = {"queries": queries, "relativePath": path}
            content = {"queryResults": [
                {"query": item, "matches": [sample], "exitCode": code,
                 "status": "succeeded"}
                for item in queries
            ]}
            if turn % 13 == 0:
                content = {"queryResults": [{"query": "wrong"}]}
        elif tool == "search_workspace":
            args = {"query": query, "relativePath": path}
            content = {"matches": [sample], "exitCode": code,
                       "executionDisposition": "succeeded"}
            if turn % 11 == 0:
                content = {"matches": "malformed", "executionDisposition": "unknown"}
        else:
            args = {"relativePath": path}
            content = {"value": rng.randrange(5), "kind": rng.choice(("ok", "uncertain"))}
        call = AgentToolCall(f"call-{index}", tool, args)
        obs = HarnessToolObservation(f"call-{index}", tool, status, content)
        has_call = turn % 17 != 0
        calls = (call,) if has_call else ()
        units = (_search_evidence(call, obs)
                 if tool == "search_workspace" and status == "observed" and has_call
                 else None)
        signature = _observation_evidence_signature(obs)
        actual = _advance_turn_evidence(calls, (obs,), only, signatures, search)
        signatures, search = actual.evidence_signatures, actual.search_evidence
        updated_n = (0 if actual.action_progress or actual.new_evidence
                     else prior_n + 1)
        updated_o = (prior_o + 1 if actual.observation_only else 0)
        gate = budget.observation_gate_reason(
            no_progress_turns=updated_n, observation_only_turns=updated_o
        )
        if units is None:
            encoded = "*"
        else:
            encoded = "|".join(
                "~".join((key[0], key[1], ",".join(sorted(matches))))
                for key, matches in units
            )
        print("\t".join((
            "E", str(scenario), tool, status, signature, encoded,
            str(int(actual.observation_only)),
            str(int(actual.action_progress)),
            str(int(actual.new_evidence)),
            str(len(signatures)),
            str(len(search)),
            str(sum(len(v) for v in search.values())),
            str(prior_n), str(prior_o),
            str(budget.max_no_progress_turns),
            str(budget.max_observation_only_turns),
            str(updated_n), str(updated_o),
            gate if gate is not None else "none",
        )))
        prior_n, prior_o = updated_n, updated_o
