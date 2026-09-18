#!/usr/bin/env python3
"""Temporal compatibility adapter for stable Artifact operation envelopes."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from artifact_operations import (
    ArtifactOperationExecutor,
    operation_envelope,
    operation_file_fact,
    operation_key,
    validate_public_trust_material_envelope,
)
from artifact_operations.providers import (
    DirectPythonOperationProvider,
    DeliveryCliOperationProvider,
)

DEFAULT_ARTIFACT_PYTHON = Path(
    "/root/.local/share/ordivon-workstation/artifact-delivery-python-v1/current/bin/python"
)

# Compatibility aliases retained for existing tests/callers.
file_fact = operation_file_fact
_operation_key = operation_key


class ReceiptFencedArtifactExecutor:
    """Compatibility adapter from historical activity payloads to ArtifactOperation."""

    def __init__(
        self,
        state_root: Path,
        *,
        artifact_python: Path = DEFAULT_ARTIFACT_PYTHON,
        artifact_cli: Path | None = None,
        artifact_oci_cli: Path | None = None,
    ) -> None:
        if artifact_cli is not None or artifact_oci_cli is not None:
            provider_kwargs: dict[str, Any] = {"artifact_python": artifact_python}
            if artifact_cli is not None:
                provider_kwargs["artifact_cli"] = artifact_cli
            if artifact_oci_cli is not None:
                provider_kwargs["artifact_oci_cli"] = artifact_oci_cli
            selected_provider: Any = DeliveryCliOperationProvider(**provider_kwargs)
        else:
            selected_provider = DirectPythonOperationProvider()
        self.provider = selected_provider
        self.executor = ArtifactOperationExecutor(state_root, provider=self.provider)

    @staticmethod
    def _cli_failure_message(label: str, process: Any, report: Path | None = None) -> str:
        return DeliveryCliOperationProvider.cli_failure_message(label, process, report)

    def execute_operation(self, value: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(value)

    def prepare(self, value: dict[str, Any]) -> dict[str, Any]:
        return self.execute_operation(
            operation_envelope(
                str(value["operationId"]),
                "prepare",
                {"request": dict(value["request"])},
            )
        )

    def build(self, value: dict[str, Any]) -> dict[str, Any]:
        return self.execute_operation(
            operation_envelope(
                str(value["operationId"]),
                "build",
                {"request": dict(value["request"])},
            )
        )

    def verify(self, value: dict[str, Any]) -> dict[str, Any]:
        return self.execute_operation(
            operation_envelope(
                str(value["operationId"]),
                "verify",
                {
                    "profile": dict(value["profile"]),
                    "artifact": dict(value["artifact"]),
                },
            )
        )

    def _validate_trust_material(self, value: dict[str, Any]) -> dict[str, Any]:
        return self.provider.validate_trust_material(value)

    def verify_trust(self, value: dict[str, Any]) -> dict[str, Any]:
        return self.execute_operation(
            operation_envelope(
                str(value["operationId"]),
                "verify-trust",
                {
                    "profile": dict(value["profile"]),
                    "artifact": dict(value["artifact"]),
                    "gateVsas": dict(value["gateVsas"]),
                    "trustMaterial": dict(value["trustMaterial"]),
                },
            )
        )

    def package(self, value: dict[str, Any]) -> dict[str, Any]:
        inputs: dict[str, Any] = {
            "profile": dict(value["profile"]),
            "artifact": dict(value["artifact"]),
            "verifyReport": dict(value["verifyReport"]),
        }
        local = bool(value.get("allowLocalUnsignedDevelopment", False))
        if not local and value.get("trustMaterial") is not None:
            inputs["trustMaterial"] = dict(value["trustMaterial"])
        return self.execute_operation(
            operation_envelope(
                str(value["operationId"]),
                "package",
                inputs,
                {"allowLocalUnsignedDevelopment": local},
            )
        )
