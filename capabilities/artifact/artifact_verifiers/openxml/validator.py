from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from artifact_core.contracts import file_fact

from .toolchain import openxml_validator_executable


def verify_openxml_artifact(path: Path) -> dict[str, Any]:
    artifact = file_fact(path)
    validator = openxml_validator_executable()
    if not validator.is_file():
        return {
            "status": "NOT_RUN",
            "artifact": artifact,
            "error": "DocumentFormat.OpenXml validator runtime is unavailable",
        }

    proc = subprocess.run(
        [str(validator), str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    parsed: dict[str, Any] | None = None
    parse_error: str | None = None
    try:
        parsed = json.loads(proc.stdout)
    except Exception as error:
        parse_error = str(error)

    return {
        "status": (
            "PASS"
            if proc.returncode == 0 and parsed and parsed.get("status") == "PASS"
            else "FAIL"
        ),
        "artifact": artifact,
        "validatorOutput": parsed,
        "exitCode": proc.returncode,
        "parseError": parse_error,
        "stderr": proc.stderr.strip()[:4000],
        "boundary": (
            "DocumentFormat.OpenXml schema/semantic validation only; Office target "
            "rendering, visual acceptance and delivery remain independent."
        ),
    }
