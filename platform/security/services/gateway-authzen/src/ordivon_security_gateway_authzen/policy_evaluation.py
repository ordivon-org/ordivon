"""One native OPA decision over the exact private per-evaluation capture."""

from __future__ import annotations

import hashlib
import hmac
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from .json_qualification import qualify_json_object


class EvaluationUnavailable(Exception):
    pass


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _declared_release_revision(path: Path) -> str | None:
    # A path label is not proof of source or installed interpreter identity.
    release = path.parent.parent
    if release.parent.name == "releases" and re.fullmatch(
        r"[0-9a-f]{40}|[0-9a-f]{64}", release.name
    ):
        return release.name
    return None


@dataclass(frozen=True, slots=True)
class PolicyEvaluation:
    decision: bool
    policy_sha256: str
    policy_data_commitment: str
    input_sha256: str
    declared_release_revision: str | None
    evaluated_at_ms: int

    def standing(self, *, request_id: str, instance_id: str) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "standing": "OBSERVED_FOR_DECISION",
            "requestId": request_id,
            "instanceId": instance_id,
            "policySha256": self.policy_sha256,
            "policyDataCommitment": self.policy_data_commitment,
            "inputSha256": self.input_sha256,
            "declaredReleaseRevision": self.declared_release_revision,
            "evaluatedAtEpochMs": self.evaluated_at_ms,
        }


def evaluate_policy(
    payload: bytes, opa: str, policy: str, data: str, commitment_key: bytes
) -> PolicyEvaluation:
    """Capture once and evaluate those bytes; do not infer a future decision.

    Private data are never projected, and its keyed commitment is comparable
    only within the same app instance. Cross-file capture is not atomic.
    """
    try:
        resolved_policy = Path(policy).resolve(strict=True)
        policy_bytes = resolved_policy.read_bytes()
        data_bytes = Path(data).read_bytes()
        qualify_json_object(data_bytes)
        with tempfile.TemporaryDirectory(prefix="ordivon-pdp-") as directory:
            root = Path(directory)
            policy_snapshot, data_snapshot = root / "policy.rego", root / "data.json"
            policy_snapshot.write_bytes(policy_bytes)
            data_snapshot.write_bytes(data_bytes)
            result = subprocess.run(
                [
                    opa,
                    "eval",
                    "--stdin-input",
                    "--format",
                    "raw",
                    "--data",
                    str(policy_snapshot),
                    "--data",
                    str(data_snapshot),
                    "data.ordivon.security.gateway_artifact.allow",
                ],
                input=payload,
                capture_output=True,
                timeout=2.0,
                check=True,
            )
    except (OSError, ValueError, RecursionError, subprocess.SubprocessError) as exc:
        raise EvaluationUnavailable("OPA decision unavailable") from exc
    output = result.stdout.strip()
    if output not in (b"true", b"false"):
        raise EvaluationUnavailable("OPA returned a nonboolean result")
    return PolicyEvaluation(
        decision=output == b"true",
        policy_sha256=_sha256(policy_bytes),
        policy_data_commitment="hmac-sha256:"
        + hmac.digest(commitment_key, data_bytes, "sha256").hex(),
        input_sha256=_sha256(payload),
        declared_release_revision=_declared_release_revision(resolved_policy),
        evaluated_at_ms=time.time_ns() // 1_000_000,
    )
