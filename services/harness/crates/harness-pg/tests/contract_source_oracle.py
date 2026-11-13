"""Source oracle for Python HarnessRunContract.from_dict v1/v2.

This is a pure deterministic fixture generator. It never opens a database,
provider, Runtime Job, or production configuration. Rust tests consume its
canonical JSON + acceptance label, without porting Python code into production.
"""
from __future__ import annotations

from copy import deepcopy
import json

from anc_canonical import canonical_bytes, canonical_digest
from ordivon_harness.core_contracts import HarnessBoundReference, HarnessRunContract

DIGEST = canonical_digest({"case": "contract-source-qualification"})
def bound(name: str) -> HarnessBoundReference:
    return HarnessBoundReference(name, "test-kind", DIGEST)

contract = HarnessRunContract(
    harness_run_id="harness-run:source-parity",
    harness_implementation_id="test-implementation",
    caller_id="caller:source-parity",
    caller_run_ref="caller-run-ref",
    objective_ref=bound("ref:objective"),
    context_refs=(bound("ref:context"),),
    source_refs=(bound("ref:source"),),
    prior_artifact_refs=(bound("ref:prior-artifact"),),
    provider_id="provider:test",
    adapter_id="adapter:test",
    requested_model_id="model:test",
    tool_catalog_digest=DIGEST,
    tool_grant_digest=DIGEST,
    budget={"maxTurns": 2},
    completion_contract={"mode": "text"},
    system_manifest_ref=bound("ref:system"),
    created_at_ms=1000,
    deadline_ms=2000,
)
V2 = contract.to_dict()
V1 = deepcopy(V2)
V1["schemaVersion"] = 1
V1["correlation"] = {"traceparent": None, "tracestate": None, "links": []}

cases: list[tuple[str, dict]] = []
def offer(name: str, candidate: dict) -> None:
    cases.append((name, deepcopy(candidate)))
def change(name: str, path: tuple, value: object, base: dict = V2) -> None:
    item = deepcopy(base)
    node = item
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    offer(name, item)
def erase(name: str, field: str, base: dict = V2) -> None:
    item = deepcopy(base)
    del item[field]
    offer(name, item)

offer("v2-normal", V2)
offer("v1-correlation", V1)
for version in (None, False, 0, 1, 2, 3, "1", True):
    value = deepcopy(V1 if version in (1, True) else V2)
    value["schemaVersion"] = version
    offer("version-" + repr(version), value)
for name, base in (("v2", V2), ("v1", V1)):
    for field in base:
        erase(name + "-missing-" + field, field, base)
    change(name + "-unexpected", ("unrelatedExtraField",), True, base)
for field in ("harnessRunId", "harnessImplementationId", "callerId",
              "callerRunRef", "providerId", "adapterId", "requestedModelId"):
    for idx, candidate in enumerate(("", " leading", "trailing ", "\u001cvalue",
                                     "value\u001f", "\nvalue", None, False,
                                     "x" * 301, "\u200bvalue")):
        change("text-" + field + "-" + str(idx), (field,), candidate)
for field in ("harnessRunId", "callerId"):
    for idx, candidate in enumerate(("not-prefixed", "other:id",
                                     "harness-run:", "caller:",
                                     "harness-run:\u200b", "caller:\u200b")):
        change("identity-" + field + "-" + str(idx), (field,), candidate)
for field in ("toolCatalogDigest", "toolGrantDigest"):
    for idx, candidate in enumerate(("", DIGEST.upper(), "sha256:" + "0"*63,
                                     "sha256:" + "g"*64, None, True, "0"*64)):
        change("digest-" + field + "-" + str(idx), (field,), candidate)

ref = V2["objectiveRef"]
for field in ("objectiveRef", "systemManifestRef"):
    for idx, candidate in enumerate((None, [], {}, {"ref": ref["ref"]},
                                     {"ref": "", "kind": ref["kind"], "digest": DIGEST},
                                     {"ref": " bad", "kind": ref["kind"], "digest": DIGEST},
                                     {"ref": ref["ref"], "kind": " ", "digest": DIGEST},
                                     {"ref": ref["ref"], "kind": "test", "digest": "x"},
                                     {**ref, "extra": False},
                                     {**ref, "kind": "a" * 201})):
        change("bound-" + field + "-" + str(idx), (field,), candidate)
for field in ("contextRefs", "sourceRefs", "priorArtifactRefs"):
    old = V2[field]
    for idx, candidate in enumerate((None, {}, "list", [True], [None],
                                     [old[0], old[0]], [{}], [{**ref, "ref": ""}])):
        change("references-" + field + "-" + str(idx), (field,), candidate)
change("contextRefs-empty", ("contextRefs",), [])
change("sourceRefs-empty-valid", ("sourceRefs",), [])
change("priorArtifactRefs-empty-valid", ("priorArtifactRefs",), [])

pol = V2["privacy"]
for key in pol:
    for idx, candidate in enumerate((None, True, False, "metadata-only",
                                     "bounded-private-content", "secret", 0)):
        change("privacy-" + key + "-" + str(idx), ("privacy", key), candidate)
for idx, candidate in enumerate((None, [], {}, {**pol, "extra": True},
                                 {"contentPolicy":"bounded-private-content",
                                  "allowModelContent":True,"allowToolContent":True},
                                 {"contentPolicy":"metadata-only",
                                  "allowModelContent":True,"allowToolContent":False})):
    change("privacy-object-" + str(idx), ("privacy",), candidate)

for idx, candidate in enumerate((None, [], {}, {"maxTurns": 0}, {"maxTurns": True},
                                 {"maxTurns": 10**4000}, {"tags": ["a", None, False]},
                                 {"nested": {"number": "ok"}})):
    change("budget-" + str(idx), ("budget",), candidate)
for idx, candidate in enumerate((
    None, [], {}, {"mode": "text"}, {"mode": None},
    {"mode": "text", "conformancePolicy": None},
    {"mode": "structured-result-v1"},
    {"mode": "structured-result-v1", "resultSchema": {}},
    {"mode": "structured-result-v1", "resultSchema": {"type":"object"}},
    {"mode": "structured-result-v1", "resultSchema": {"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object"}},
    {"mode": "structured-result-v1", "resultSchema": {"$schema":"https://json-schema.org/draft/2020-12/schema","type":"nope"}},
    {"mode": "structured-result-v1", "resultSchema": {"$schema":"invalid","type":"object"}},
    {"mode": "structured-result-v1", "resultSchema": {"type":"object"}, "conformancePolicy":"local-json-schema-draft-2020-12-profile-v1"},
    {"mode": "structured-result-v1", "resultSchema": {"type":"object","properties":{"x":{"type":"string"}}}, "conformancePolicy":"local-json-schema-draft-2020-12-profile-v1"},
    {"mode": "structured-result-v1", "resultSchema": {"type":"object","$schema":"https://json-schema.org/draft/2020-12/schema"}, "conformancePolicy":"local-json-schema-draft-2020-12-profile-v1"},
    {"mode": "structured-result-v1", "resultSchema": {"type":"invalid"}, "conformancePolicy":"local-json-schema-draft-2020-12-profile-v1"},
    {"mode": "structured-result-v1", "resultSchema": {"type":"object"}, "conformancePolicy":"unsupported"},
    {"mode": "structured-result-v1", "resultSchema": {"type":"object"}, "conformancePolicy":None},
    {"mode": "structured-result-v1", "resultSchema": {"$schema":"https://json-schema.org/draft/2020-12/schema","minLength":-1}},
    {"mode": "structured-result-v1", "resultSchema": {"$schema":"https://json-schema.org/draft/2020-12/schema","required":"not-an-array"}},
    {"mode": "structured-result-v1", "resultSchema": {"type":"object","additionalProperties":{}},"conformancePolicy":"local-json-schema-draft-2020-12-profile-v1"},
)):
    change("completion-" + str(idx), ("completionContract",), candidate)

for field in ("createdAtMs", "deadlineMs"):
    for idx, candidate in enumerate((None, True, False, -1, 0, 999, 1000, 2000,
                                     10**4095, "1000", [], {})):
        change("time-" + field + "-" + str(idx), (field,), candidate)

good_trace = "00-" + "1" * 32 + "-" + "2" * 16 + "-01"
for idx, candidate in enumerate((None, "", " " + good_trace, "00-" + "0"*32 + "-" + "2"*16 + "-01",
                                 "00-" + "1"*32 + "-" + "0"*16 + "-01",
                                 good_trace, good_trace.upper(), True, 42,
                                 "01-"+"a"*32+"-"+"b"*16+"-ff")):
    change("v1-trace-" + str(idx), ("correlation", "traceparent"), candidate, V1)
for idx, candidate in enumerate((None, "", " hi", "good", "\u001fstate",
                                 "a"*513, True, good_trace)):
    change("v1-tracestate-" + str(idx), ("correlation", "tracestate"), candidate, V1)
for idx, candidate in enumerate((None, [], [ref], [ref, ref], "links",
                                 [{**ref,"kind":""}])):
    change("v1-links-" + str(idx), ("correlation", "links"), candidate, V1)
for idx, candidate in enumerate(({}, None, {"traceparent":None,"tracestate":None},
                                 {**V1["correlation"], "extra":True})):
    change("v1-correlation-" + str(idx), ("correlation",), candidate, V1)

assert len(cases) >= 190, len(cases)
for name, candidate in cases:
    raw = canonical_bytes(candidate).decode("utf-8")
    try:
        HarnessRunContract.from_dict(candidate)
    except (ValueError, TypeError, AssertionError, OverflowError):
        accepted = False
    else:
        accepted = True
    print(json.dumps({"case": name, "accepted": accepted, "canonical": raw},
                     sort_keys=True, ensure_ascii=False, separators=(",", ":")))
