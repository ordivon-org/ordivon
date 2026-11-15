"""Compare the real Python Host MCP registry with the Rust staging tools/list.

This is a disposable-PostgreSQL protocol check, not a claim of complete tool parity.
The produced JSON contains metadata only, never DSNs, credentials, or result bodies.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


def wire_bytes(value: object) -> int:
    return len(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())


def python_tools() -> list[dict]:
    from ordivon_host_v2.mcp_server import build_server

    # build_server registers tools without opening a database session.
    srv = build_server("host=127.0.0.1 port=1 user=unused dbname=unused")
    return [
        tool.model_dump(by_alias=True, mode="json", exclude_none=True)
        for tool in asyncio.run(srv.list_tools())
    ]


def rust_tools(binary: Path) -> list[dict]:
    dsn = os.environ.get("HOST_RUST_TEST_DSN")
    if not dsn or dsn != os.environ.get("ORDIVON_HOST_V2_DSN"):
        raise RuntimeError("Rust audit requires matching explicit disposable PG DSNs")
    parsed = urlparse(dsn)
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError("Rust audit requires disposable loopback PostgreSQL")
    process = subprocess.Popen(
        [str(binary)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=os.environ.copy(),
    )

    def call(method: str, params: dict | None, request_id: int | None) -> dict:
        assert process.stdin is not None
        assert process.stdout is not None
        message = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        if request_id is not None:
            message["id"] = request_id
        process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        process.stdin.flush()
        if request_id is None:
            return {}
        line = process.stdout.readline()
        if not line:
            raise RuntimeError("Rust MCP exited during audit without response")
        reply = json.loads(line)
        if "error" in reply or reply.get("id") != request_id:
            raise RuntimeError(f"Rust MCP tool registry request failed: {reply.get('error')}")
        return reply["result"]

    try:
        call(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "host-mcp-contract-auditor", "version": "1.0.0"},
            },
            1,
        )
        call("notifications/initialized", None, None)
        result = call("tools/list", {}, 2)
        if result.get("nextCursor"):
            raise RuntimeError("MCP tools/list pagination requires full iteration; not audited")
        return result["tools"]
    finally:
        process.terminate()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()


def inventory(items: list[dict], *, name: str) -> dict[str, dict]:
    by_name: dict[str, dict] = {}
    for item in items:
        key = item["name"]
        if key in by_name:
            raise RuntimeError(f"Duplicate {name} MCP tool: {key}")
        by_name[key] = item
    return by_name


def extract_enum(schema: dict, prop: dict) -> list | None:
    if "enum" in prop:
        return prop["enum"]
    if "$ref" in prop:
        root = prop["$ref"]
        if root.startswith("#/$defs/"):
            return extract_enum(schema, schema.get("$defs", {}).get(root[len("#/$defs/"):], {}))
        if root.startswith("#/definitions/"):
            return extract_enum(
                schema, schema.get("definitions", {}).get(root[len("#/definitions/"):], {})
            )
    for selector in ("anyOf", "oneOf", "allOf"):
        if selector in prop:
            variants = [extract_enum(schema, item) for item in prop[selector]]
            options = [v for v in variants if v is not None]
            if options:
                return sorted({x for group in options for x in group}, key=str)
    return None


def details(value: dict) -> dict:
    schema = value.get("inputSchema") or {}
    props = schema.get("properties", {})
    return {
        "required": sorted(schema.get("required", [])),
        "properties": sorted(props),
        "defaults": {k: v["default"] for k, v in sorted(props.items()) if "default" in v},
        "enums": {k: e for k, v in sorted(props.items())
                  if (e := extract_enum(schema, v)) is not None},
        "additionalProperties": schema.get("additionalProperties"),
        "hasOutputSchema": "outputSchema" in value,
        "hasDescription": bool(value.get("description")),
        "bytes": wire_bytes(value),
    }


def compare(expected: dict, actual: dict) -> dict:
    e, a = details(expected), details(actual)
    differences = {}
    if "outputSchema" in expected and "outputSchema" in actual:
        if expected["outputSchema"] != actual["outputSchema"]:
            differences["outputSchemaContent"] = {
                "python": expected["outputSchema"],
                "rust": actual["outputSchema"],
            }
    for name in ("required", "properties", "defaults", "enums", "additionalProperties", "hasOutputSchema"):
        if e[name] != a[name]:
            differences[name] = {"python": e[name], "rust": a[name]}
    return differences


def require_explicit_native_extensions(
    rust_only: list[str], approved: list[str], rust: dict[str, dict]
) -> None:
    """Prevent Rust-only additions from being counted as original Python parity."""
    if len(set(approved)) != len(approved) or rust_only != sorted(approved):
        raise RuntimeError(
            f"Rust-only tool set differs from explicitly reviewed extensions:"
            f" actual={rust_only}, allowed={sorted(approved)}"
        )
    for name in rust_only:
        tool = rust[name]
        for field in ("inputSchema", "outputSchema"):
            schema = tool.get(field)
            if not isinstance(schema, dict) or schema.get("type") != "object":
                raise RuntimeError(
                    f"Rust-only tool {name} must publish a concrete object {field}"
                )
            if not isinstance(schema.get("properties"), dict) or not schema["properties"]:
                raise RuntimeError(
                    f"Rust-only tool {name} cannot publish an empty {field} placeholder"
                )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rust-bin", required=True, type=Path)
    parser.add_argument("--source-manifest", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument(
        "--extension", action="append", default=[],
        help="Explicit new Rust-only tool; must be backed by typed input/output schemas"
    )
    args = parser.parse_args()
    reference = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    source = inventory(python_tools(), name="Python")
    rust = inventory(rust_tools(args.rust_bin.resolve()), name="Rust")
    declared = sorted(reference["tools"])
    if declared != sorted(source):
        raise RuntimeError("Original Python Host source manifest differs from actual registry")
    source_names = set(source)
    rust_names = set(rust)
    # A new native capability MUST NOT disguise an absent old Python tool.
    # Extensions are a separate additive source epoch, not Python parity.
    rust_only = sorted(rust_names - source_names)
    require_explicit_native_extensions(rust_only, args.extension, rust)
    if list(rust) != sorted(rust):
        raise RuntimeError("Rust tools/list order is not deterministic lexical ordering")

    intersection = sorted(rust_names & source_names)
    mismatches = {name: diff for name in intersection if (diff := compare(source[name], rust[name]))}
    report = {
        "kind": "ordivon.host-mcp-source-rust-differential",
        "schemaVersion": 1,
        "sourceEpoch": reference["surfaceEpoch"],
        "pythonTools": len(source),
        "rustTools": len(rust),
        "missingRustTools": sorted(source_names - rust_names),
        "rustOnlyTools": rust_only,
        "comparableSourceTools": len(intersection),
        "metadataBytes": {
            "python": sum(wire_bytes(v) for v in source.values()),
            "rust": sum(wire_bytes(v) for v in rust.values()),
        },
        "toolsWithDescriptions": {
            "python": sum(bool(v.get("description")) for v in source.values()),
            "rust": sum(bool(v.get("description")) for v in rust.values()),
        },
        "toolsWithOutputSchema": {
            "python": sum("outputSchema" in v for v in source.values()),
            "rust": sum("outputSchema" in v for v in rust.values()),
        },
        "schemaDifferences": mismatches,
        "truthBoundary": (
            "Compares real source Python SDK registry to isolated Rust tools/list; "
            "additional Rust-only tools are explicit unmerged source extensions, "
            "not an installed-connector or end-to-end output/effect parity proof"
        ),
    }
    # Critical caller input shape is not negotiable; metadata differences
    # about outputSchema/defaults are reported separately without greenwashing.
    unsafe = {
        name: {k: v for k, v in diffs.items() if k in {"required", "properties"}}
        for name, diffs in mismatches.items()
        if any(k in diffs for k in ("required", "properties"))
    }
    if unsafe:
        raise RuntimeError(f"Rust MCP tool input shape differs from Python: {unsafe}")
    # A declared success output schema must be exactly original Python SDK's
    # concrete TypedDict schema, never an invented permissive object marker.
    output_violations = {
        name: sorted(k for k in mismatches.get(name, {})
                     if k in {"hasOutputSchema", "outputSchemaContent"})
        for name in intersection
        if any(k in mismatches.get(name, {}) for k in
               ("hasOutputSchema", "outputSchemaContent"))
    }
    if output_violations:
        raise RuntimeError(
            f"Rust published output schemas diverge from original Python: {output_violations}"
        )
    # Once a tool is published, exact Python input defaults/enum/shape parity
    # is a precondition for substituting the native Rust endpoint. Missing
    # tools are listed separately and can be integrated in a later slice.
    if mismatches:
        raise RuntimeError(
            f"Rust MCP published tool metadata differs from Python source: {mismatches}"
        )
    print("MCP_PYTHON_RUST_OUTPUT_SCHEMA_EXACT",
          len(intersection), "of", len(source), "registered tools")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "HOST_MCP_CONTRACT_AUDIT"
        f" source={len(source)} rust={len(rust)} missing={len(source_names - rust_names)}"
        f" rust_only={rust_only}"
        f" schema_diffs={len(mismatches)}"
        f" metadata_bytes={report['metadataBytes']}"
        f" described={report['toolsWithDescriptions']}"
        f" output_schema={report['toolsWithOutputSchema']}"
    )
    for name, diff in sorted(mismatches.items()):
        print("MCP_SCHEMA_DIFF", name, ",".join(sorted(diff)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
