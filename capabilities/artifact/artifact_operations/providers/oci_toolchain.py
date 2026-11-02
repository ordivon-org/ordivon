"""Exact ORAS OCI carrier and OPA Rego evaluation adapters for Artifact releases.

No alternate OCI parser, policy engine, release authority, or effect implementation.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from artifact_core.contracts import sha256_file

ARTIFACT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ORAS = Path(os.environ.get("ARTIFACT_ORAS", "/opt/ordivon/external/oras/1.3.4/bin/oras"))
DEFAULT_OPA = Path(os.environ.get("ARTIFACT_OPA", "/opt/ordivon/external/opa/1.20.2/bin/opa"))
DEFAULT_RELEASE_POLICY = Path(
    os.environ.get(
        "ARTIFACT_RELEASE_POLICY", str(ARTIFACT_ROOT / "artifact-delivery/policy/release.rego")
    )
)


def run_oras(args: list[str], *, cwd: Path, timeout: int = 120) -> dict[str, Any]:
    if not DEFAULT_ORAS.is_file() or not os.access(DEFAULT_ORAS, os.X_OK):
        raise RuntimeError(f"ORAS carrier is unavailable: {DEFAULT_ORAS}")
    proc = subprocess.run(
        [str(DEFAULT_ORAS), *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
        env=dict(os.environ),
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"ORAS command failed ({proc.returncode}): {' '.join(args)}\n"
            f"stdout={proc.stdout[-4000:]}\nstderr={proc.stderr[-4000:]}"
        )
    text = proc.stdout.strip()
    if not text:
        return {}
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"ORAS returned non-JSON output: {error}: {text[-4000:]}") from error
    if not isinstance(value, dict):
        raise RuntimeError("ORAS JSON output is not an object")
    return value


def evaluate_release_policy(policy_input: dict[str, Any]) -> dict[str, Any]:
    if not DEFAULT_OPA.is_file() or not os.access(DEFAULT_OPA, os.X_OK):
        raise RuntimeError(f"OPA carrier is unavailable: {DEFAULT_OPA}")
    if not DEFAULT_RELEASE_POLICY.is_file():
        raise RuntimeError(f"Artifact release policy is unavailable: {DEFAULT_RELEASE_POLICY}")
    proc = subprocess.run(
        [
            str(DEFAULT_OPA),
            "eval",
            "--format",
            "raw",
            "--data",
            str(DEFAULT_RELEASE_POLICY),
            "--stdin-input",
            "data.artifact.release.ready",
        ],
        input=json.dumps(policy_input, separators=(",", ":")),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
        env=dict(os.environ),
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"OPA release policy evaluation failed ({proc.returncode}): {proc.stderr[-4000:]}"
        )
    raw = proc.stdout.strip()
    if raw not in {"true", "false"}:
        raise RuntimeError(f"OPA release policy returned unexpected result: {raw!r}")
    return {
        "status": "PASS",
        "ready": raw == "true",
        "query": "data.artifact.release.ready",
        "input": policy_input,
        "policy": {
            "path": str(DEFAULT_RELEASE_POLICY.resolve()),
            "sha256": sha256_file(DEFAULT_RELEASE_POLICY),
        },
        "tool": {
            "path": str(DEFAULT_OPA.resolve()),
            "sha256": sha256_file(DEFAULT_OPA),
            "version": "1.20.2",
        },
    }
