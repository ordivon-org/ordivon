from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RawLLMResponse:
    ok: bool = False
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    duration_ms: int = 0
    timed_out: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseLLMClient:
    def generate(self, prompt: str, **kwargs) -> RawLLMResponse:
        raise NotImplementedError("Subclasses must implement generate()")
