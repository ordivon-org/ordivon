from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from artifact_core.contracts import file_fact, sha256_file
from artifact_verifiers.openxml import openxml_validator_executable

from .toolchain import (
    DEFAULT_TOOLCHAIN_LOCK,
    GLOBAL_PANDOC,
    GLOBAL_PANDOC_ARCHIVE,
    selected_external_file,
)

RequestValidator = Callable[[Path], dict[str, Any]]
DeliveryPlanner = Callable[[Path], dict[str, Any]]


@dataclass(frozen=True)
class DocumentDependencyHooks:
    validate_delivery_request: RequestValidator
    compile_delivery_plan: DeliveryPlanner


def verify_document_dependencies(
    request_path: Path,
    document: Path,
    pandoc: Path | None = None,
    pandoc_archive: Path | None = None,
    toolchain_lock: Path | None = None,
    openxml_validator: Path | None = None,
    *,
    hooks: DocumentDependencyHooks,
) -> dict[str, Any]:
    validation = hooks.validate_delivery_request(request_path)
    plan = hooks.compile_delivery_plan(request_path)
    lock_path = toolchain_lock or DEFAULT_TOOLCHAIN_LOCK
    executable = pandoc or selected_external_file("ARTIFACT_PANDOC", GLOBAL_PANDOC)
    archive = pandoc_archive or selected_external_file("ARTIFACT_PANDOC_ARCHIVE", GLOBAL_PANDOC_ARCHIVE)
    validator = openxml_validator or openxml_validator_executable()
    failures: list[str] = []

    if validation.get("status") != "PASS":
        failures.append("delivery request did not PASS exact input validation")
    if (
        plan.get("status") != "PASS"
        or plan.get("artifactClass") != "document"
        or plan.get("buildAdapter") != "pandoc-docx"
    ):
        failures.append(
            "delivery plan did not select the mature pandoc-docx document adapter"
        )

    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        pandoc_lock = lock.get("pandoc", {}) if isinstance(lock, dict) else {}
    except Exception as error:
        pandoc_lock = {}
        failures.append(f"toolchain lock could not be read: {error}")

    pandoc_fact: dict[str, Any] = {"path": str(executable)}
    if not executable.is_file() or not os.access(executable, os.X_OK):
        failures.append("locked Pandoc executable is unavailable")
    else:
        proc = subprocess.run(
            [str(executable), "--version"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=20,
        )
        version_line = (
            proc.stdout.splitlines()[0]
            if proc.returncode == 0 and proc.stdout
            else ""
        )
        digest = sha256_file(executable)
        expected_version = str(pandoc_lock.get("version", ""))
        expected_digest = pandoc_lock.get("binarySha256")
        pandoc_fact = {
            **file_fact(executable),
            "version": version_line,
            "expectedVersion": f"pandoc {expected_version}",
            "versionMatched": version_line == f"pandoc {expected_version}",
            "expectedSha256": expected_digest,
            "digestMatched": digest == expected_digest,
        }
        if not pandoc_fact["versionMatched"]:
            failures.append("Pandoc version does not match the toolchain lock")
        if not pandoc_fact["digestMatched"]:
            failures.append("Pandoc binary digest does not match the toolchain lock")

    archive_fact: dict[str, Any] = {"path": str(archive)}
    if not archive.is_file():
        failures.append("locked Pandoc release archive is unavailable")
    else:
        expected_archive = pandoc_lock.get("linuxAmd64ArchiveSha256")
        archive_fact = {
            **file_fact(archive),
            "expectedSha256": expected_archive,
            "digestMatched": sha256_file(archive) == expected_archive,
        }
        if not archive_fact["digestMatched"]:
            failures.append(
                "Pandoc release archive digest does not match the toolchain lock"
            )

    validator_fact: dict[str, Any] = {"path": str(validator)}
    if not validator.is_file() or not os.access(validator, os.X_OK):
        failures.append("locked Open XML validator runtime is unavailable")
    else:
        validator_fact = file_fact(validator)

    resolved = (
        validation.get("resolved", {})
        if isinstance(validation.get("resolved"), dict)
        else {}
    )
    return {
        "status": "PASS" if not failures else "FAIL",
        "artifact": file_fact(document),
        "request": file_fact(request_path),
        "profile": resolved.get("profile"),
        "source": resolved.get("source"),
        "declaredMaterials": resolved.get("materials", []),
        "pandoc": pandoc_fact,
        "pandocReleaseArchive": archive_fact,
        "openXmlValidator": validator_fact,
        "toolchainLock": (
            file_fact(lock_path) if lock_path.is_file() else {"path": str(lock_path)}
        ),
        "failures": failures,
        "boundary": (
            "Dependency PASS binds the exact request/source/profile plus locked "
            "Pandoc builder bytes, official release archive digest, and Open XML "
            "validator availability. It does not establish Microsoft Word target "
            "behavior, PDF companion correctness, accessibility, visual acceptance, "
            "or release-signature authenticity."
        ),
    }
