from __future__ import annotations

from pathlib import Path
from typing import Any

from .contract import validate_operation_envelope
from .receipt import ReceiptFence


class ArtifactOperationExecutor:
    """Execute stable Artifact operation envelopes through a replaceable provider."""

    def __init__(self, state_root: Path, *, provider: Any) -> None:
        self.provider = provider
        self.receipts = ReceiptFence(state_root)

    def execute(self, value: dict[str, Any]) -> dict[str, Any]:
        operation = validate_operation_envelope(value)
        prepared = self.provider.prepare_operation(operation)
        result = self.receipts.run(
            operation["operationKind"],
            operation["operationId"],
            prepared.immutable_inputs,
            lambda output_directory: self.provider.produce(
                operation["operationKind"],
                prepared.context,
                output_directory,
            ),
        )
        if operation["operationKind"] == "package":
            result["packageDirectory"] = str(
                Path(result["operationDirectory"]) / "package" / "layout"
            )
        return result
