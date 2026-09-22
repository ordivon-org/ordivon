"""Public task-local composition mechanics for Ordivon."""

from .cognitive_circuit_r1 import (
    CircuitContractError,
    canonical_digest,
    compile_manifest,
    evaluate_gate_results,
    validate_gate_result,
    validate_manifest,
)
from .interface_contract_r2 import currentness_standing, evaluate_interface

__all__ = [
    "CircuitContractError",
    "canonical_digest",
    "compile_manifest",
    "currentness_standing",
    "evaluate_gate_results",
    "evaluate_interface",
    "validate_gate_result",
    "validate_manifest",
]
