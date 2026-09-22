from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .perceptual import ObserverReport, load_observer_report

_MAX_STDOUT_BYTES = 4 * 1024 * 1024
_MAX_STDERR_BYTES = 1024 * 1024


class PerceptualProviderAdapterError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ProviderExecutionSpec:
    provider_id: str
    executable: str
    args: tuple[str, ...]
    timeout_seconds: int = 300

    def __post_init__(self) -> None:
        if not self.provider_id:
            raise ValueError("provider_id is required")
        if not self.executable:
            raise ValueError("executable is required")
        if self.timeout_seconds < 1 or self.timeout_seconds > 3600:
            raise ValueError("timeout_seconds must be in [1, 3600]")


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _bounded(data: bytes, limit: int) -> bytes:
    if len(data) > limit:
        raise PerceptualProviderAdapterError(
            f"provider output exceeds retained boundary ({len(data)} > {limit})"
        )
    return data


def run_observer_provider(
    *,
    spec: ProviderExecutionSpec,
    task_envelope_path: Path,
    packet_root: Path,
    output_path: Path,
    expected_carrier_sha256: str,
    expected_role: str,
    independence_key: str,
    inherited_environment: dict[str, str] | None = None,
) -> tuple[ObserverReport, dict[str, Any]]:
    """Execute one replaceable observer provider behind a narrow file/JSON contract."""

    envelope_path = task_envelope_path.resolve()
    packet = packet_root.resolve()
    output = output_path.resolve()
    if not envelope_path.is_file():
        raise PerceptualProviderAdapterError(f"task envelope missing: {envelope_path}")
    if not packet.is_dir():
        raise PerceptualProviderAdapterError(f"packet root missing: {packet}")
    if not independence_key:
        raise ValueError("independence_key is required")

    envelope_bytes = envelope_path.read_bytes()
    envelope = json.loads(envelope_bytes)
    if envelope.get("kind") != "publication-perceptual-observer-task":
        raise PerceptualProviderAdapterError("invalid observer task envelope")
    if envelope.get("carrierSha256") != expected_carrier_sha256:
        raise PerceptualProviderAdapterError("task-envelope carrier binding mismatch")
    if envelope.get("role") != expected_role:
        raise PerceptualProviderAdapterError("task-envelope observer role mismatch")

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    env = {
        "PATH": os.environ.get("PATH", ""),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
    }
    if inherited_environment:
        env.update(inherited_environment)

    argv = [
        spec.executable,
        *spec.args,
        "--task-envelope",
        str(envelope_path),
        "--packet-root",
        str(packet),
        "--output",
        str(output),
        "--independence-key",
        independence_key,
    ]

    try:
        completed = subprocess.run(
            argv,
            cwd=packet,
            env=env,
            check=False,
            capture_output=True,
            timeout=spec.timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise PerceptualProviderAdapterError(
            f"provider execution timed out after {spec.timeout_seconds}s"
        ) from exc

    stdout = _bounded(completed.stdout, _MAX_STDOUT_BYTES)
    stderr = _bounded(completed.stderr, _MAX_STDERR_BYTES)
    if completed.returncode != 0:
        raise PerceptualProviderAdapterError(
            f"provider exited nonzero ({completed.returncode}); "
            f"stderrSha256={_sha256_bytes(stderr)}"
        )
    if not output.is_file():
        raise PerceptualProviderAdapterError("provider returned success without observer report")

    report = load_observer_report(output)
    if report.carrier_sha256 != expected_carrier_sha256:
        raise PerceptualProviderAdapterError("observer report carrier binding mismatch")
    if report.role != expected_role:
        raise PerceptualProviderAdapterError("observer report role mismatch")
    if report.independence_key != independence_key:
        raise PerceptualProviderAdapterError("observer report independence binding mismatch")

    receipt = {
        "schemaVersion": 1,
        "kind": "publication-perceptual-provider-execution-receipt",
        "providerId": spec.provider_id,
        "role": expected_role,
        "carrierSha256": expected_carrier_sha256,
        "taskEnvelopeSha256": _sha256_bytes(envelope_bytes),
        "packetManifestSha256": (
            _sha256_file(packet / "packet-manifest-r1.json")
            if (packet / "packet-manifest-r1.json").is_file()
            else None
        ),
        "observerReportSha256": _sha256_file(output),
        "independenceKey": independence_key,
        "exitCode": completed.returncode,
        "stdoutSha256": _sha256_bytes(stdout),
        "stderrSha256": _sha256_bytes(stderr),
        "standing": "PASS_PROVIDER_EXECUTION_BOUND",
        "nonClaims": [
            "provider execution identity does not prove model-weight independence",
            "provider PASS does not imply perceptual consensus PASS",
            "ambient process environment is not inherited unless explicitly allow-listed",
        ],
    }
    return report, receipt


def write_provider_execution_receipt(path: Path, receipt: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
