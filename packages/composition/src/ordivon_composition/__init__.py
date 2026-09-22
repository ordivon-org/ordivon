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
from .verification_obligation_r1 import (
    compile_verification_obligations,
    resolve_verifier_bindings,
    validate_obligation_set,
)

__all__ = [
    "CircuitContractError",
    "canonical_digest",
    "compile_manifest",
    "compile_verification_obligations",
    "currentness_standing",
    "evaluate_gate_results",
    "evaluate_interface",
    "resolve_verifier_bindings",
    "validate_gate_result",
    "validate_manifest",
    "validate_obligation_set",
]
