"""Freeze the original Python Host MCP success-output schemas for Rust.

The Python MCP SDK produces these from TypedDict/Pydantic source contracts.
The Rust binary reads the checked-in static JSON: Python is not a Rust
runtime dependency. --check requires exact equality to the authoritative
Python source tool registry (not just a tool name list).
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from ordivon_host_v2.mcp_server import build_server

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "contracts" / "python_host_mcp_output_schemas.json"


async def source_contracts() -> dict[str, dict]:
    server = build_server("host=127.0.0.1 port=1 user=unused dbname=unused")
    items = await server.list_tools()
    schemas: dict[str, dict] = {}
    for tool in items:
        data = tool.model_dump(mode="json", by_alias=True, exclude_none=True)
        name = data["name"]
        output = data.get("outputSchema")
        if name in schemas or not isinstance(output, dict) or output.get("type") != "object":
            raise RuntimeError(f"Host tool {name}: duplicate or missing real object outputSchema")
        schemas[name] = output
    if len(schemas) != 31:
        raise RuntimeError(f"Expected 31 original Python Host tools, got {len(schemas)}")
    return dict(sorted(schemas.items()))


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    raw = json.dumps(asyncio.run(source_contracts()), sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"
    if args.write:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        TARGET.write_text(raw, encoding="utf-8")
    else:
        if not TARGET.is_file() or TARGET.read_text(encoding="utf-8") != raw:
            raise SystemExit("RUST_OUTPUT_SCHEMA_DRIFT_FROM_ORIGINAL_PYTHON_HOST")
    print(f"RUST_PYTHON_OUTPUT_SCHEMA_SOURCE_EXACT_PASS tools=31 bytes={len(raw.encode())} mode={'write' if args.write else 'check'}")


if __name__ == "__main__":
    main()
