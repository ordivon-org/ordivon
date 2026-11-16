"""Source-only classification fence for the native Gateway MCP Tool surface.

The current released manifest is the tool-set source; enforcement-surface.json
is the reviewed security classification. Neither is an Owner grant or a live
PDP authorization. Test the real Gateway resolver, not a copied Tool registry.
"""

from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from mcp import Client

from ordivon_gateway.authorization_targets import resolve_authorization_target
from ordivon_gateway.http_ingress_guard import needs_verified_ingress
from ordivon_gateway.mcp_server import build_server

ROOT = Path(__file__).resolve().parents[1]

# These are existing capability classes, not a second copy of Tool names.
_PEP_CAPABILITIES = {
    "host-legacy-read-authzen": "host.legacy-read",
    "host-legacy-write-authzen": "host.legacy-write",
    "runtime-artifact-authzen": "artifact.runtime",
    "runtime-release-authzen": "runtime.release.linux",
}


def _source() -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = json.loads((ROOT / "mcp-surface.json").read_text(encoding="utf-8"))
    security = json.loads((ROOT / "enforcement-surface.json").read_text(encoding="utf-8"))
    return manifest, security


async def _native_tool_names() -> list[str]:
    async with Client(build_server(), raise_exceptions=True) as client:
        return [tool.name for tool in (await client.list_tools()).tools]


def _target_arguments(name: str, row: dict[str, Any]) -> dict[str, Any]:
    # Local inert coordinates are used only to exercise pure target projection.
    # They must not be executed, sent to Owners, or treated as credentials.
    if row["routeOwner"] == "host" and row["operation"] == "write":
        return (
            {"authorActorRef": "actor:source:review"}
            if name == "message.post"
            else {"actorRef": "actor:source:review"}
        )
    if name == "artifact.read":
        return {
            "operationRef": "ordivon-exec:v1:runtime.linux:job-test-0123",
            "artifactId": "attempt-test.stdout",
        }
    if name == "runtime.release.apply":
        return {
            "requestId": "source-review",
            "workspaceId": "ws-test",
            "commit": "a" * 40,
            "candidateManifestDigest": "sha256:" + "b" * 64,
            "expectedToolCount": 41,
        }
    return {}


def _check_partition(
    tool_names: list[str],
    manifest: dict[str, Any],
    security: dict[str, Any],
) -> dict[str, int]:
    released = manifest["tools"]
    rows = security["tools"]
    declared = {row["name"]: row for row in rows}

    assert len(tool_names) == len(set(tool_names)), "duplicate registered Tool"
    assert len(released) == len(set(released)), "duplicate released Tool"
    assert len(rows) == len(declared), "duplicate security review entry"
    assert set(tool_names) == set(released), "unreviewed SDK Tool vs release manifest"
    assert set(tool_names) == set(declared), "unreviewed SDK Tool vs enforcement surface"
    assert security["truthBoundary"] == "SOURCE_CONSUMER_ONLY"

    counts = {"public": 0, "identity_only": 0, "object_pep": 0}
    for name in tool_names:
        row = declared[name]
        ingress = row["httpIngress"]
        expected_ingress = (
            "verified-principal" if needs_verified_ingress(name) else "public-metadata"
        )
        assert ingress == expected_ingress, f"unexpected HTTP ingress for {name}"

        pep_label = row["gatewayObjectPep"]
        target = resolve_authorization_target(name, _target_arguments(name, row))
        if pep_label == "none":
            assert target is None, f"silent object PEP removal for {name}"
            kind = "identity_only" if needs_verified_ingress(name) else "public"
            counts[kind] += 1
        else:
            assert pep_label in _PEP_CAPABILITIES, f"unknown Security PEP type for {name}"
            assert needs_verified_ingress(name), f"public Tool acquired Security PEP: {name}"
            assert target is not None, f"declared PEP lacks a real target: {name}"
            assert target.capability == _PEP_CAPABILITIES[pep_label], name
            counts["object_pep"] += 1

        assert row["downstreamAuthorization"] == "UNKNOWN", name
        if row["operation"] in {"execute", "write"}:
            assert needs_verified_ingress(name), f"effectful anonymous Tool: {name}"
    return counts


def test_native_sdk_security_partition_is_reviewed_and_implemented() -> None:
    manifest, security = _source()
    actual = asyncio.run(_native_tool_names())
    counts = _check_partition(actual, manifest, security)
    assert sum(counts.values()) == len(actual)
    # No frozen copied names or numbers: the manifests and implementation own
    # future classified additions. Counts are diagnostic, not permission.
    assert counts["object_pep"] > 0
    assert counts["identity_only"] > 0
    assert counts["public"] > 0


def test_unclassified_new_sdk_tool_is_never_implicitly_identity_only() -> None:
    manifest, security = _source()
    actual = asyncio.run(_native_tool_names())
    injected_tool = "unreviewed.example.effect"

    with pytest.raises(AssertionError, match="unreviewed SDK Tool vs release manifest"):
        _check_partition(actual + [injected_tool], manifest, security)

    manifest_copy = deepcopy(manifest)
    manifest_copy["tools"].append(injected_tool)
    with pytest.raises(AssertionError, match="unreviewed SDK Tool vs enforcement surface"):
        _check_partition(actual + [injected_tool], manifest_copy, security)


def test_declared_security_pep_cannot_silently_become_none() -> None:
    manifest, security = _source()
    actual = asyncio.run(_native_tool_names())
    changed = deepcopy(security)
    row = next(item for item in changed["tools"] if item["gatewayObjectPep"] != "none")
    row["gatewayObjectPep"] = "none"
    with pytest.raises(AssertionError, match="silent object PEP removal"):
        _check_partition(actual, manifest, changed)
