from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from artifact_operations.receipt import expected_file, operation_file_fact

from .common import PreparedOperation, write_json

CompilePlan = Callable[[Path], dict[str, Any]]


class PrepareOperationHandler:
    def __init__(self, compile_plan: CompilePlan) -> None:
        self.compile_plan = compile_plan

    def prepare(self, operation: dict[str, Any]) -> PreparedOperation:
        request_path = expected_file(dict(operation["inputs"]["request"]), "request")
        return PreparedOperation(
            {"request": operation_file_fact(request_path)},
            {"requestPath": request_path},
        )

    def produce(
        self, context: dict[str, Any], output_directory: Path
    ) -> tuple[dict[str, str], dict[str, Any]]:
        plan = self.compile_plan(context["requestPath"])
        out = output_directory / "derived-plan.json"
        write_json(out, plan)
        if plan.get("status") != "PASS":
            raise RuntimeError(f"derived plan did not PASS: {plan.get('failures')}")
        resolved = plan["resolvedInputs"]

        def simple(value: dict[str, Any]) -> dict[str, Any]:
            digest = value.get("sha256") or (value.get("digest") or {}).get("sha256")
            return {
                "path": str(Path(value["path"]).resolve()),
                "sha256": digest,
                "name": value.get("name") or Path(value["path"]).name,
                "size": value.get("size"),
            }

        return {"plan": "derived-plan.json"}, {
            "requestId": plan.get("requestId"),
            "profile": simple(resolved["profile"]),
            "source": simple(resolved["source"]),
            "requiredGates": plan.get("requiredGates", []),
        }
