from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from artifact_core.contracts import file_fact

from .toolchain import verapdf_executable

SUPPORTED_VERAPDF_FLAVOURS = {"4", "4f", "4e", "ua1", "ua2", "wt1r", "wt1a"}


def verify_pdf_conformance(path: Path, flavour: str) -> dict[str, Any]:
    artifact = file_fact(path)
    if flavour not in SUPPORTED_VERAPDF_FLAVOURS:
        return {
            "status": "FAIL",
            "artifact": artifact,
            "flavour": flavour,
            "error": "unsupported veraPDF flavour",
        }
    executable = verapdf_executable()
    if executable is None:
        return {
            "status": "NOT_RUN",
            "artifact": artifact,
            "flavour": flavour,
            "error": "veraPDF is not installed",
        }
    proc = subprocess.run(
        [str(executable), "--format", "json", "--flavour", flavour, str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    compliant = False
    profile_name: str | None = None
    failed_rules: int | None = None
    failed_checks: int | None = None
    parse_error: str | None = None
    try:
        parsed = json.loads(proc.stdout)
        validation = parsed["report"]["jobs"][0]["validationResult"][0]
        compliant = validation.get("compliant") is True
        profile_name = validation.get("profileName")
        details = validation.get("details", {})
        failed_rules = details.get("failedRules")
        failed_checks = details.get("failedChecks")
    except Exception as error:
        parse_error = str(error)
    return {
        "status": "PASS" if compliant and proc.returncode == 0 else "FAIL",
        "artifact": artifact,
        "validator": {
            "implementation": "veraPDF",
            "executable": str(executable),
            "flavour": flavour,
        },
        "profileName": profile_name,
        "compliant": compliant,
        "failedRules": failed_rules,
        "failedChecks": failed_checks,
        "exitCode": proc.returncode,
        "parseError": parse_error,
        "stderr": proc.stderr.strip()[:4000],
        "boundary": (
            "veraPDF conformance is machine-checkable profile evidence only; human "
            "accessibility/use review and target-viewer acceptance remain separate gates."
        ),
    }
