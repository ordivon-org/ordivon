#!/usr/bin/env python3
"""Prove the installed Harness completes and reopens without Host."""

from __future__ import annotations

import importlib.util
import os
import uuid

import psycopg
from psycopg import sql

from anc_canonical import canonical_digest

from ordivon_harness.api import (
    AgentTurnResult,
    HarnessBoundReference,
    HarnessRunContract,
    NO_TOOL_AGENT_SURFACE_DIGEST,
)
from ordivon_harness.ordivon.model import AgentRunConclusion, ScriptedTurnAdapter
from ordivon_harness.agent_run import HarnessAgentRun
from ordivon_harness.postgres_store import PostgresHarnessStore

DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64


class FixedClock:
    def __init__(self, value: int = 1_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


def main() -> int:
    if importlib.util.find_spec("ordivon_host") is not None:
        raise RuntimeError("Host-free Harness check unexpectedly found ordivon-host")
    contract = HarnessRunContract(
        harness_run_id="harness-run:host-free-smoke",
        harness_implementation_id="ordivon-harness@host-free-smoke",
        caller_id="caller:host-free-smoke",
        caller_run_ref="host-free-smoke:1",
        objective_ref=HarnessBoundReference("objective:host-free-smoke", "objective", DIGEST_A),
        context_refs=(HarnessBoundReference("context:host-free-smoke", "context", DIGEST_B),),
        provider_id="provider:scripted",
        adapter_id=ScriptedTurnAdapter.adapter_id,
        requested_model_id=ScriptedTurnAdapter.model_id,
        tool_catalog_digest=NO_TOOL_AGENT_SURFACE_DIGEST,
        tool_grant_digest=canonical_digest(
            {"schemaVersion": 1, "kind": "ordivon.no-tool-grant", "tools": []}
        ),
        budget={
            "maxModelCalls": 1,
            "maxToolCalls": 1,
            "maxWallTimeMs": 10_000,
        },
        completion_contract={"mode": "record"},
        system_manifest_ref=HarnessBoundReference(
            "system-manifest:host-free-smoke", "system-manifest", DIGEST_A
        ),
        created_at_ms=1_000,
    )
    result = AgentTurnResult(
        model_call_id="model-call:host-free-smoke",
        model_id=ScriptedTurnAdapter.model_id,
        content="completed",
        tool_calls=(),
        conclusion=AgentRunConclusion(
            status="candidate_completed",
            summary="Host-free Harness completed and persisted its Run.",
        ),
        usage={"inputTokens": 5, "outputTokens": 3},
        finish_reason="stop",
        raw_response_digest=canonical_digest({"harness": "host-free-smoke"}),
    )
    dsn = os.environ.get("HARNESS_PG_TEST_DSN")
    if not dsn:
        raise RuntimeError("HARNESS_PG_TEST_DSN required for real Host-free PostgreSQL check")
    schema = "hpg_hostfree_" + uuid.uuid4().hex[:18]
    with PostgresHarnessStore(dsn, schema=schema, initialize=True):
        pass
    clock = FixedClock()
    try:
        first = HarnessAgentRun.create(
            dsn, schema, contract,
            lambda _contract: ScriptedTurnAdapter((result,)),
            clock_ms=clock, monotonic_ms=clock,
        )
        execution = first.run(({"role": "user", "content": "complete"},))
        if execution.terminal_result is None:
            raise RuntimeError("Host-free Harness did not produce terminal evidence")
        receipt_digest = execution.terminal_result.receipt.digest
        reopened = HarnessAgentRun.open(
            dsn, schema, contract.harness_run_id,
            lambda _contract: ScriptedTurnAdapter((result,)),
            clock_ms=clock, monotonic_ms=clock,
        )
        inspected = reopened.inspect_terminal()
        if inspected.receipt.digest != receipt_digest:
            raise RuntimeError("Host-free Harness PG restart inspection differs")
        with PostgresHarnessStore(dsn, schema=schema) as store:
            if not store.doctor(full=True)["healthy"]:
                raise RuntimeError("Host-free Harness PostgreSQL Store Doctor failed")
    finally:
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
    print("harness without host: passed (PostgreSQL, reopened and inspected)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
