#!/usr/bin/env python3
"""Real Python AgentToolCall.from_dict / Domain Tool Grant source oracle.

Domain bridge is a no-effect stub. Real source objects still validate each
call's identity/digest and _GrantedDomainToolBridge's grant denial; this does
NOT test Runtime dispatch or PG effect authorization.
"""
from __future__ import annotations

from anc_canonical import canonical_bytes
from ordivon_harness.ordivon.model import AgentToolCall, AgentToolDefinition
from ordivon_harness.domain_tools import DomainToolCatalog, _GrantedDomainToolBridge
from ordivon_harness.ordivon.tool_errors import ToolBridgeError, ToolBridgeErrorKind

def D(c):
    return "sha256:" + c * 64
catalog = DomainToolCatalog(
    domain_id="domain:model-proposal-lab",
    revision="v7_proposal",
    tools=tuple(
        AgentToolDefinition(
            name=name,
            description=f"Research and test {name}",
            input_schema={"type":"object", "properties":{"text":{"type":"string"}}},
        )
        for name in ("read", "edit", "delete")
    ),
)
class NoEffectBridge:
    catalog = catalog
    bridge_identity = {"kind": "test-only", "physicalDispatch": False}
    def execute(self, call: AgentToolCall, *, step_id: str):
        assert call.name in ("read", "edit")
        assert step_id.startswith("test:")
        return None

bridge = _GrantedDomainToolBridge(NoEffectBridge(), ("edit", "read"))
allowed = set(t.name for t in bridge.definitions())

# Exact A/B source-bounded ToolSurface expectation is one frozen catalog/grant.
print("\t".join(("C", canonical_bytes(catalog.to_dict()).hex(),
    catalog.digest, catalog._granted_digest(("edit", "read")))))

def emit(record: dict, *, seen: bool) -> None:
    payload = canonical_bytes(record).hex()
    try:
        parsed = AgentToolCall.from_dict(record)
        if seen:
            result = "duplicate"
        elif parsed.argument_error is not None:
            result = "argument_error"
        else:
            try:
                # The real Python _GrantedDomainToolBridge gate, using a
                # deliberately side-effect-free fake executor.
                bridge.execute(parsed, step_id="test:oracle")
            except ToolBridgeError as error:
                assert error.kind is ToolBridgeErrorKind.AUTHORITY_DENIED
                result = "not_visible"
            else:
                result = "needs_auth"
        print("\t".join((
            "T", "1", payload, parsed.digest,
            parsed.tool_call_id, parsed.name, result, str(int(seen)),
        )))
    except (TypeError, ValueError):
        print("\t".join(("T", "0", payload, "-", "-", "-", "-", str(int(seen)))))


for i in range(48):
    base = AgentToolCall(
        tool_call_id=f"call:model_{i}_中文",
        name=("read", "edit", "delete", "unlisted")[i % 4],
        arguments={"text": f"🌍 {i}", "counter": 10 ** (i % 24), "nested": {"x": [1, True, None]}},
    ).to_dict()
    invalid_diag = AgentToolCall(
        tool_call_id=base["toolCallId"], name=base["name"],
        arguments=base["arguments"],
        argument_error=("unavailable_tool" if i % 2 == 0 else "malformed_arguments"),
        raw_arguments_digest=D("a"),
        raw_arguments_preview="{unclosed",
    ).to_dict()

    def modified(record, key, value):
        result = dict(record)
        result[key] = value
        return result

    fixtures = [
        base,
        invalid_diag,
        modified(base, "providerArguments", {
            "error": None, "rawDigest": None, "preview": None,
        }),
        modified(base, "providerArguments", {
            "error": "invalid_json", "rawDigest": D("1"), "preview": "",
        }),
        modified(base, "providerArguments", {
            "error": "invalid_json", "rawDigest": D("2"), "preview": "a"*2048,
        }),
        modified(base, "providerArguments", {
            "error": "invalid_json", "rawDigest": D("3"), "preview": "a"*2049,
        }),
        modified(base, "providerArguments", {
            "error": "broken", "rawDigest": None, "preview": None,
        }),
        modified(base, "providerArguments", {
            "error": None, "rawDigest": D("4"), "preview": None,
        }),
        modified(base, "providerArguments", {
            "error": "", "rawDigest": D("5"), "preview": "",
        }),
        modified(base, "providerArguments", {
            "error": "bad", "rawDigest": D("A"), "preview": "",
        }),
        modified(base, "providerArguments", {
            "error": "bad", "rawDigest": D("6"), "preview": "", "extra": "x",
        }),
        modified(base, "providerArguments", None),
        modified(base, "providerArguments", {}),
        modified(base, "arguments", []),
        modified(base, "arguments", {"bigint": int("9" * 4096)} if i == 0 else {"v": 0}),
        modified(base, "toolCallId", " \t"),
        modified(base, "toolCallId", "\x1c" + base["toolCallId"]),
        modified(base, "toolCallId", "\u200b" + base["toolCallId"]),
        modified(base, "name", ""),
        modified(base, "name", "\u001f" + base["name"]),
        modified(base, "name", "z"*121),
        modified(base, "name", 100),
        modified(base, "missing_extra", "extra"),
        {"name": base["name"], "arguments": base["arguments"]},
    ]
    for j, sample in enumerate(fixtures):
        emit(sample, seen=((i + j) % 9 == 0))
