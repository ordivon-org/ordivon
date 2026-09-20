from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PreparedOperation:
    immutable_inputs: dict[str, Any]
    context: dict[str, Any]
