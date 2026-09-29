from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from artifact_operations.receipt import expected_file, operation_file_fact

from .common import PreparedOperation, write_json

ExecuteBuild = Callable[[Path, Path | None], dict[str, Any]]


class BuildOperationHandler:
    def __init__(self, execute_build: ExecuteBuild) -> None:
        self.execute_build = execute_build

    def prepare(self, operation: dict[str, Any]) -> PreparedOperation:
        request_path = expected_file(dict(operation["inputs"]["request"]), "request")
        return PreparedOperation(
            {"request": operation_file_fact(request_path)},
            {"requestPath": request_path},
        )

    def produce(
        self, context: dict[str, Any], output_directory: Path
    ) -> tuple[dict[str, str], dict[str, Any]]:
        artifacts = output_directory / "artifacts"
        result = self.execute_build(context["requestPath"], artifacts)
        report = output_directory / "build-stage.json"
        write_json(report, result)
        if result.get("status") != "PASS":
            raise RuntimeError(f"build stage did not PASS: {result.get('failures')}")
        artifact_path = Path(result["artifact"]["path"])
        if (
            artifact_path.parent.resolve() != artifacts.resolve()
            or not artifact_path.is_file()
        ):
            raise RuntimeError("build output escaped operation directory")
        return {
            "buildReport": "build-stage.json",
            "artifact": f"artifacts/{artifact_path.name}",
        }, {
            "artifactName": artifact_path.name,
            "adapter": result.get("plan", {}).get("buildAdapter"),
        }
