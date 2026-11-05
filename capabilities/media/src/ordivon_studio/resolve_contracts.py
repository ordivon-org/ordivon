"""Shared on-wire Resolve operation identity and profile constants.

These are the source-side operation/result protocol names, not a replacement
of the self-contained Windows Resolve Runner or the OpenTimelineIO schema.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

RUNNER_FILENAME = "Ordivon Studio Runner.py"
CONFIG_FILENAME = "ordivon-runner.config.json"
OPERATION_FILENAME = "resolve-operation.json"
RESULT_FILENAME = "resolve-result.json"
SMOKE_FIXTURE_FILENAME = "resolve-smoke-1080p30.mp4"
COMPATIBILITY_OTIO_FILENAME = "resolve-21.0.3.7-compatibility.otio"
COMPATIBILITY_PROJECT_PREFIX = "Ordivon Resolve 21 Compatibility "
COMPATIBILITY_PRODUCT_NAME = "DaVinci Resolve"
COMPATIBILITY_VERSION_STRING = "21.0.3.7"
COMPATIBILITY_VERSION = [21, 0, 3, 7, ""]
DEVELOPER_README_PATH = Path(
    "/mnt/c/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt"
)
ASSEMBLY_CONFORM_PROJECT_PREFIX = "Ordivon Runtime Introduction Conform Probe "
ASSEMBLY_CONFORM_TIMELINE_NAME = "Assembly v0 Conform Probe"
ASSEMBLY_CONFORM_OTIO_FILENAME = "assembly.v0.resolve-21.0.3.7.otio"
_OPERATION_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
_DIGEST = re.compile(r"^sha256:[a-f0-9]{64}$")


def canonical_operation_digest(value: object) -> str:
    """The same canonical JSON SHA-256 used by the standalone Resolve Runner."""
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"
