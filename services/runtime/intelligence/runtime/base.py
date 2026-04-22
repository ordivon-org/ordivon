from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from domains.research.models import AnalysisResult
from intelligence.tasks.contracts import IntelligenceTaskRequest
from orchestrator.context.context_builder import AnalysisContext


@dataclass(frozen=True, slots=True)
class RuntimeDescriptor:
    runtime_name: str
    provider_name: str
    model_name: str | None = None
    adapter_name: str | None = None


class AgentRuntime(ABC):
    @property
    @abstractmethod
    def descriptor(self) -> RuntimeDescriptor:
        raise NotImplementedError

    @abstractmethod
    def analyze(
        self,
        ctx: AnalysisContext,
        request: IntelligenceTaskRequest | None = None,
    ) -> AnalysisResult:
        raise NotImplementedError
