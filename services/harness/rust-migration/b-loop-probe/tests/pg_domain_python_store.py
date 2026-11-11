#!/usr/bin/env python3
"""Extend A's existing disposable PG18 fixture with an actual Domain Tool Run.

Uses the real Python PostgresHarnessStore and DomainToolCatalog as producers.
No schema bootstrapping, second Store, product DB DSN or tool invocation.
"""
import json
import os
from pathlib import Path
from dataclasses import replace

from anc_canonical import digest_bytes
from ordivon_harness.core_contracts import HarnessBoundReference, HarnessRunContract
from ordivon_harness.domain_tools import DomainToolCatalog
from ordivon_harness.ordivon.model import AgentToolDefinition, AgentToolCall
from ordivon_harness.ordivon.agent_bridge import (
    NO_TOOL_AGENT_SURFACE_DIGEST,
    NO_TOOL_AGENT_GRANT_DIGEST,
)
from ordivon_harness.ordivon.runtime_bridge import (
    INDEPENDENT_SEARCH_TOOL_SURFACE_DIGEST,
    INDEPENDENT_SEARCH_TOOL_GRANT_DIGEST,
)
from ordivon_harness.postgres_store import PostgresHarnessStore

dsn = os.environ["HARNESS_RUST_TEST_PG_DSN"]
schema = os.environ["HARNESS_RUST_TEST_SCHEMA"]
path = Path(os.environ["HARNESS_RUST_TEST_FIXTURE_PATH"])
assert schema.startswith("hpg_rust_isolated_a_")
assert "valid" in json.loads(path.read_text())

catalog = DomainToolCatalog(
    domain_id="domain:pg-evidence",
    revision="r2_source",
    tools=tuple(
        AgentToolDefinition(
            name=name,
            description="Source-verified " + name + " 🧩",
            input_schema={"type": "object", "properties": {"text": {"type": "string"}}},
        )
        for name in ("read", "edit", "delete")
    ),
)
allowed = ("edit", "read")
dg = digest_bytes(b"isolated-rust-verified-domain-consumer")
def ref(prefix: str) -> HarnessBoundReference:
    return HarnessBoundReference(
        ref=f"test:{prefix}:bound", kind="test-only", digest=dg
    )
contract = HarnessRunContract(
    harness_run_id="harness-run:test-pg-bound-domain",
    harness_implementation_id="test:pg-domain-consumer",
    caller_id="caller:test-pg-domain",
    caller_run_ref="test-run-domain",
    objective_ref=ref("objective"),
    context_refs=(ref("context"),),
    provider_id="provider:verified-source",
    adapter_id="adapter:verified-source",
    requested_model_id="model:verified-source",
    tool_catalog_digest=catalog.digest,
    tool_grant_digest=catalog._granted_digest(allowed),
    budget={"maxTurns": 2},
    completion_contract={"mode": "text"},
    system_manifest_ref=ref("manifest"),
    created_at_ms=1000,
)
# Build three distinct compositions through real Python HarnessRunContract
# constructors. The mixed and Runtime Search contracts are structurally
# valid but must never be admitted by the no-Tool consumer.
no_tool_contract = replace(
    contract,
    harness_run_id="harness-run:test-pg-no-tool",
    caller_run_ref="test-run-no-tool",
    tool_catalog_digest=NO_TOOL_AGENT_SURFACE_DIGEST,
    tool_grant_digest=NO_TOOL_AGENT_GRANT_DIGEST,
)
mixed_no_tool = replace(
    no_tool_contract,
    harness_run_id="harness-run:test-pg-no-tool-mixed",
    caller_run_ref="test-run-no-tool-mixed",
    tool_grant_digest=catalog._granted_digest(allowed),
)
runtime_search = replace(
    no_tool_contract,
    harness_run_id="harness-run:test-pg-runtime-search",
    caller_run_ref="test-run-runtime-search",
    tool_catalog_digest=INDEPENDENT_SEARCH_TOOL_SURFACE_DIGEST,
    tool_grant_digest=INDEPENDENT_SEARCH_TOOL_GRANT_DIGEST,
)
with PostgresHarnessStore(dsn, schema=schema, initialize=False) as store:
    for variant in (contract, no_tool_contract, mixed_no_tool, runtime_search):
        assert store.create_run(variant).value == "created"
        store.validate_run_history(variant.harness_run_id)
original = json.loads(path.read_text(encoding="utf-8"))
source_call = AgentToolCall(
    tool_call_id="call:pg1",
    name="read",
    arguments={"text": "hello"},
)
original["no_tool"] = {
    "runId": no_tool_contract.harness_run_id,
    "contractDigest": no_tool_contract.digest,
    "providerId": no_tool_contract.provider_id,
    "adapterId": no_tool_contract.adapter_id,
    "requestedModelId": no_tool_contract.requested_model_id,
    "catalogDigest": NO_TOOL_AGENT_SURFACE_DIGEST,
    "grantDigest": NO_TOOL_AGENT_GRANT_DIGEST,
    "mixedRunId": mixed_no_tool.harness_run_id,
    "runtimeSearchRunId": runtime_search.harness_run_id,
}
original["domain_bridge"] = {
    "modelToolCall": source_call.to_dict(),
    "modelToolCallDigest": source_call.digest,
    "runId": contract.harness_run_id,
    "providerId": contract.provider_id,
    "adapterId": contract.adapter_id,
    "requestedModelId": contract.requested_model_id,
    "catalog": catalog.to_dict(),
    "allowedTools": list(allowed),
    "contractDigest": contract.digest,
    "catalogDigest": catalog.digest,
    "grantDigest": catalog._granted_digest(allowed),
}
path.write_text(json.dumps(original, ensure_ascii=False, sort_keys=True), encoding="utf-8")
print("PYTHON_PG_DOMAIN_TOOL_CONTRACT_CREATED", contract.digest)
