from __future__ import annotations

import os
from pathlib import Path

DEFAULT_OPENXML_VALIDATOR = Path(
    "/root/.local/share/ordivon-workstation/artifact-openxml-v1/current/bin/validate-openxml"
)


def openxml_validator_executable() -> Path:
    configured = os.environ.get("ARTIFACT_OPENXML_VALIDATOR")
    return Path(configured) if configured else DEFAULT_OPENXML_VALIDATOR
