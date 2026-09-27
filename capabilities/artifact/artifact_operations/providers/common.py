from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class PreparedOperation:
    immutable_inputs: dict[str, Any]
    context: dict[str, Any]


class OperationHandler(Protocol):
    def prepare(self, operation: dict[str, Any]) -> PreparedOperation: ...

    def produce(
        self, context: dict[str, Any], output_directory: Path
    ) -> tuple[dict[str, str], dict[str, Any]]: ...


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
