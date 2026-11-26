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

    try:
        proc = subprocess.run(
            [str(validator), str(path)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"status": "NOT_RUN", "artifact": artifact, "error": str(error)}

    parsed = None
    parse_error = None
    standing = "NOT_RUN"
    try:
        parsed = json.loads(proc.stdout)
        if not isinstance(parsed, dict):
            raise ValueError("OpenXML report must be an object")
        subject = parsed.get("artifact")
        authority = parsed.get("validator")
        errors = parsed.get("validationErrors")
        count = parsed.get("validationErrorCount")
        if (
            not isinstance(subject, dict)
            or subject.get("sha256") != artifact["digest"]["sha256"]
            or not isinstance(authority, dict)
            or authority.get("implementation") != "DocumentFormat.OpenXml"
            or authority.get("api") != "OpenXmlValidator"
            or not isinstance(errors, list)
            or type(count) is not int
            or count != len(errors)
            or any(
                not isinstance(item, dict) or not isinstance(item.get("id"), str) for item in errors
            )
        ):
            raise ValueError("OpenXML report identity or validation error shape is unqualified")
        if proc.returncode == 0 and parsed.get("status") == "PASS" and count == 0:
            standing = "PASS"
        elif proc.returncode == 1 and parsed.get("status") == "FAIL" and count > 0:
            standing = "FAIL"
        else:
            raise ValueError("OpenXML report status, errors and exit code disagree")
    except (ValueError, TypeError) as error:
        parse_error = str(error)

    return {
        "status": standing,
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
