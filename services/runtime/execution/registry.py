from __future__ import annotations

from dataclasses import dataclass

from execution.adapters.recommendations import RecommendationExecutionAdapter
from execution.adapters.reviews import ReviewExecutionAdapter
from execution.adapters.validation import ValidationExecutionAdapter


class ExecutionAdapterContractError(TypeError):
    pass


@dataclass(frozen=True, slots=True)
class ExecutionAdapterContract:
    family_name: str
    adapter_type: type


class ExecutionAdapterRegistry:
    def __init__(self) -> None:
        self._contracts: dict[str, ExecutionAdapterContract] = {}

    def register(self, family_name: str, adapter_type: type) -> None:
        self._validate_contract(family_name, adapter_type)
        self._contracts[family_name] = ExecutionAdapterContract(
            family_name=family_name,
            adapter_type=adapter_type,
        )

    def resolve(self, family_name: str, db):
        contract = self._contracts.get(family_name)
        if contract is None:
            raise ExecutionAdapterContractError(f"No execution adapter registered for family: {family_name}")
        return contract.adapter_type(db)

    def _validate_contract(self, family_name: str, adapter_type: type) -> None:
        if not family_name or not isinstance(family_name, str):
            raise ExecutionAdapterContractError("Execution adapter family_name must be a non-empty string.")
        adapter_family = getattr(adapter_type, "family_name", None)
        if adapter_family != family_name:
            raise ExecutionAdapterContractError(
                f"Execution adapter {adapter_type.__name__} must declare family_name={family_name!r}."
            )


def build_default_execution_adapter_registry() -> ExecutionAdapterRegistry:
    registry = ExecutionAdapterRegistry()
    registry.register("recommendation", RecommendationExecutionAdapter)
    registry.register("review", ReviewExecutionAdapter)
    registry.register("validation", ValidationExecutionAdapter)
    return registry
