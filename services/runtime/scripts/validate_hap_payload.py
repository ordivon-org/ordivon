#!/usr/bin/env python3
"""HAP payload validation script.

Validates HAP v0 JSON payloads against their JSON schemas.
Local-only, no API, no MCP, no external side effects.

Usage:
    python scripts/validate_hap_payload.py <payload.json>
    python scripts/validate_hap_payload.py examples/hap/basic/harness-adapter-manifest.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "src" / "ordivon_verify" / "schemas"

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed. Run: uv pip install jsonschema")
    sys.exit(2)


def _load_schema(schema_name: str) -> dict:
    path = SCHEMAS_DIR / f"{schema_name}.schema.json"
    if not path.exists():
        print(f"ERROR: Schema not found: {path}")
        sys.exit(2)
    return json.loads(path.read_text(encoding="utf-8"))


def _detect_schema_name(payload: dict) -> str | None:
    """Detect which HAP schema a payload likely belongs to."""
    if "adapter_id" in payload and "harness_family" in payload and "capabilities" in payload:
        return "hap-adapter-manifest"
    if "request_id" in payload and "requested_capabilities" in payload and "task_type" in payload:
        return "hap-task-request"
    if "receipt_id" in payload and "commands_run" in payload and "files_changed" in payload:
        return "hap-execution-receipt"
    return None


def validate_payload(payload_path: Path) -> tuple[bool, str]:
    if not payload_path.exists():
        return False, f"File not found: {payload_path}"

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"

    schema_name = _detect_schema_name(payload)
    if schema_name is None:
        return (
            False,
            "Cannot determine HAP schema for payload. Expected adapter-manifest, task-request, or execution-receipt structure.",
        )

    schema = _load_schema(schema_name)

    try:
        jsonschema.validate(instance=payload, schema=schema)
        return True, f"VALID ({schema_name})"
    except jsonschema.ValidationError as e:
        return False, f"INVALID ({schema_name}): {e.message}"
    except Exception as e:
        return False, f"ERROR ({schema_name}): {e}"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_hap_payload.py <payload.json>")
        return 2

    payload_path = Path(sys.argv[1])
    valid, message = validate_payload(payload_path)
    print(message)
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
