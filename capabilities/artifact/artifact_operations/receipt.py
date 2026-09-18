from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any, Callable

from artifact_core.contracts import FileCommitment


Producer = Callable[[Path], tuple[dict[str, str], dict[str, Any]]]


def operation_file_fact(path: Path) -> dict[str, Any]:
    return FileCommitment.from_path(path).as_dict()


def expected_file(value: dict[str, Any], label: str) -> Path:
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} must be a file commitment object")
    unknown = set(value) - {"path", "sha256", "name", "size"}
    if unknown:
        raise RuntimeError(f"{label} contains unsupported fields: {sorted(unknown)}")
    if not isinstance(value.get("path"), str) or not isinstance(
        value.get("sha256"), str
    ):
        raise RuntimeError(f"{label}.path and sha256 are required")
    path = Path(value["path"]).resolve()
    actual = operation_file_fact(path)
    if actual["sha256"] != value["sha256"]:
        raise RuntimeError(f"{label} SHA-256 drift")
    if value.get("name") is not None and value["name"] != actual["name"]:
        raise RuntimeError(f"{label} name drift")
    if value.get("size") is not None and value["size"] != actual["size"]:
        raise RuntimeError(f"{label} size drift")
    return path


def operation_key(operation_kind: str, operation_id: str) -> str:
    return hashlib.sha256(f"{operation_kind}\0{operation_id}".encode()).hexdigest()


class ReceiptFence:
    """Generic exactly-once local commit fence for Artifact operations.

    This class knows operation identity and exact output bytes only. It does not know
    Artifact profiles, builders, verifiers, trust policy, OCI, or Temporal.
    """

    def __init__(self, state_root: Path) -> None:
        self.state_root = state_root.resolve()
        (self.state_root / "operations").mkdir(parents=True, exist_ok=True)
        (self.state_root / "locks").mkdir(parents=True, exist_ok=True)

    def _receipt_view(
        self, opdir: Path, receipt: dict[str, Any], *, replayed: bool
    ) -> dict[str, Any]:
        roles = {
            role: operation_file_fact(opdir / rel)
            for role, rel in receipt["roles"].items()
        }
        return {
            "schemaVersion": 1,
            "kind": "ordivon.artifact-operation-result",
            "operationKind": receipt["operationKind"],
            "operationId": receipt["operationId"],
            "replayed": replayed,
            "operationDirectory": str(opdir),
            "inputs": receipt["inputs"],
            "roles": roles,
            "metadata": receipt.get("metadata", {}),
        }

    def _verify_receipt(
        self,
        opdir: Path,
        receipt: dict[str, Any],
        operation_kind: str,
        operation_id: str,
        inputs: dict[str, Any],
    ) -> None:
        if (
            receipt.get("operationKind") != operation_kind
            or receipt.get("operationId") != operation_id
        ):
            raise RuntimeError("committed operation receipt identity mismatch")
        if receipt.get("inputs") != inputs:
            raise RuntimeError(
                "operationId reuse attempted with different immutable inputs"
            )
        if not isinstance(receipt.get("outputs"), dict) or not receipt["outputs"]:
            raise RuntimeError("committed operation receipt has no outputs")
        for relative, expected in receipt["outputs"].items():
            actual = operation_file_fact(opdir / relative)
            if (
                actual["sha256"] != expected.get("sha256")
                or actual["size"] != expected.get("size")
            ):
                raise RuntimeError(f"committed operation output drift: {relative}")

    def run(
        self,
        operation_kind: str,
        operation_id: str,
        inputs: dict[str, Any],
        producer: Producer,
    ) -> dict[str, Any]:
        if not operation_id:
            raise RuntimeError("operationId is required")
        key = operation_key(operation_kind, operation_id)
        operation_root = self.state_root / "operations" / operation_kind
        operation_root.mkdir(parents=True, exist_ok=True)
        final = operation_root / key
        with (self.state_root / "locks" / f"{key}.lock").open("a+b") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            receipt_path = final / "activity-receipt.json"
            if receipt_path.is_file():
                receipt = json.loads(receipt_path.read_text())
                self._verify_receipt(
                    final, receipt, operation_kind, operation_id, inputs
                )
                return self._receipt_view(final, receipt, replayed=True)

            if final.exists():
                shutil.rmtree(final)
            final.mkdir(parents=True)
            try:
                roles, metadata = producer(final)
                outputs: dict[str, Any] = {}
                normalized_roles: dict[str, str] = {}
                for role, relative in roles.items():
                    relative_path = Path(relative)
                    if relative_path.is_absolute() or ".." in relative_path.parts:
                        raise RuntimeError(
                            f"invalid operation output role path: {relative}"
                        )
                    fact = operation_file_fact(final / relative_path)
                    normalized_roles[role] = relative_path.as_posix()
                    outputs[relative_path.as_posix()] = {
                        key: fact[key] for key in ("sha256", "size", "name")
                    }
                if not outputs:
                    raise RuntimeError("operation producer returned no outputs")
                receipt = {
                    "schemaVersion": 1,
                    "kind": "ordivon.artifact-operation-receipt",
                    "operationKind": operation_kind,
                    "operationId": operation_id,
                    "inputs": inputs,
                    "roles": normalized_roles,
                    "outputs": outputs,
                    "metadata": metadata,
                }
                temporary = final / ".activity-receipt.json.tmp"
                with temporary.open("w") as handle:
                    handle.write(
                        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
                    )
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, receipt_path)
                return self._receipt_view(final, receipt, replayed=False)
            except Exception:
                shutil.rmtree(final, ignore_errors=True)
                raise
