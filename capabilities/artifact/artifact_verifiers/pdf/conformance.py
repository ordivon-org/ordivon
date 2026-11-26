from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from artifact_core.contracts import file_fact
from artifact_core.json_validation import decode_json

from .toolchain import verapdf_executable

SUPPORTED_VERAPDF_FLAVOURS = {"4", "4f", "4e", "ua1", "ua2", "wt1r", "wt1a"}


def _integer_field(row: dict, name: str, expected: int | None = None) -> int:
    value = row[name]
    if type(value) is not int or value < 0 or (expected is not None and value != expected):
        raise ValueError(f"inconsistent veraPDF field: {name}")
    return value


def assess_native_report(stdout: str, exit_code: int, artifact: dict) -> dict[str, Any]:
    """Project one completed native validation, not transport errors, into a verdict."""
    report = decode_json(stdout)["report"]
    jobs = report["jobs"]
    if not isinstance(jobs, list) or len(jobs) != 1:
        raise ValueError("expected exactly one veraPDF job")
    job = jobs[0]
    if "taskException" in job:
        raise ValueError("veraPDF job exception")
    item = job["itemDetails"]
    if not isinstance(item["name"], str) or Path(item["name"]).resolve() != Path(artifact["path"]):
        raise ValueError("veraPDF job subject path differs")
    _integer_field(item, "size", artifact["size"])
    results = job["validationResult"]
    if not isinstance(results, list) or len(results) != 1:
        raise ValueError("expected exactly one veraPDF validation result")
    result = results[0]
    compliant = result["compliant"]
    if type(compliant) is not bool or result["jobEndStatus"] != "normal":
        raise ValueError("veraPDF did not complete an unambiguous validation")
    profile_name = result["profileName"]
    if not isinstance(profile_name, str) or not profile_name.strip():
        raise ValueError("missing native profile name")
    batch = report["batchSummary"]
    _integer_field(batch, "totalJobs", 1)
    for key in ("outOfMemory", "veraExceptions", "failedEncryptedJobs", "failedParsingJobs"):
        _integer_field(batch, key, 0)
    summary = batch["validationSummary"]
    for key, expected in (
        ("failedJobCount", 0),
        ("totalJobCount", 1),
        ("successfulJobCount", 1),
        ("compliantPdfaCount", int(compliant)),
        ("nonCompliantPdfaCount", int(not compliant)),
    ):
        _integer_field(summary, key, expected)
    details = result["details"]
    failed_rules = _integer_field(details, "failedRules")
    failed_checks = _integer_field(details, "failedChecks")
    if compliant:
        if exit_code != 0 or failed_rules or failed_checks:
            raise ValueError("inconsistent compliant veraPDF result")
    elif exit_code != 1 or not failed_rules or not failed_checks:
        raise ValueError("inconsistent noncompliant veraPDF result")
    return {
        "status": "PASS" if compliant else "FAIL",
        "compliant": compliant,
        "profileName": profile_name,
        "failedRules": failed_rules,
        "failedChecks": failed_checks,
    }


def verify_pdf_conformance(path: Path, flavour: str) -> dict[str, Any]:
    artifact = file_fact(path)
    value: dict[str, Any] = {
        "status": "NOT_RUN",
        "artifact": artifact,
        "flavour": flavour,
        "compliant": None,
        "profileName": None,
        "failedRules": None,
        "failedChecks": None,
        "parseError": None,
        "boundary": "veraPDF completed native conformance only; human accessibility and "
        "target acceptance remain separate. Path/size and pre/post digest are "
        "observations, not complete process readset or ABA protection.",
    }
    if flavour not in SUPPORTED_VERAPDF_FLAVOURS:
        return {**value, "error": "unsupported veraPDF flavour"}
    executable = verapdf_executable()
    if executable is None:
        return {**value, "error": "veraPDF is not installed"}
    value["validator"] = {
        "implementation": "veraPDF",
        "executable": str(executable),
        "flavour": flavour,
    }
    try:
        proc = subprocess.run(
            [str(executable), "--format", "json", "--flavour", flavour, artifact["path"]],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as error:
        return {**value, "error": str(error)}
    value.update(exitCode=proc.returncode, stderr=proc.stderr.strip()[:4000])
    try:
        observed = assess_native_report(proc.stdout, proc.returncode, artifact)
        if file_fact(path) != artifact:
            raise ValueError("veraPDF subject changed during observation")
    except (KeyError, IndexError, TypeError, ValueError, OSError, RuntimeError) as error:
        return {**value, "parseError": str(error)}
    return {**value, **observed}
