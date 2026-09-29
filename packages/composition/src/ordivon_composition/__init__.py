"""Public task-local composition mechanics for Ordivon."""

from .agent_run_binding_r1 import (
    AgentRunBindingError,
    compile_agent_run_binding,
    require_ready_agent_run_binding,
    validate_agent_run_binding,
)
from .authority_obligation_r1 import (
    AuthorityObligationError,
    compile_authority_obligations,
    validate_authority_obligation_set,
)
from .cognitive_circuit_r1 import (
    CircuitContractError,
    canonical_digest,
    compile_manifest,
    evaluate_gate_results,
    validate_gate_result,
    validate_manifest,
)
from .interface_contract_r2 import currentness_standing, evaluate_interface
from .successor_contract_r1 import (
    compile_successor_contract,
    evaluate_successor_gates,
    validate_successor_contract,
    validate_successor_gate_result,
)
from .verification_obligation_r1 import (
    compile_verification_obligations,
    resolve_verifier_bindings,
    validate_obligation_set,
)

__all__ = [
    "AuthorityObligationError",
    "AgentRunBindingError",
    "CircuitContractError",
    "canonical_digest",
    "compile_agent_run_binding",
    "compile_authority_obligations",
    "compile_manifest",
    "compile_successor_contract",
    "compile_verification_obligations",
    "currentness_standing",
    "evaluate_gate_results",
    "evaluate_interface",
    "evaluate_successor_gates",
    "require_ready_agent_run_binding",
    "resolve_verifier_bindings",
    "validate_gate_result",
    "validate_agent_run_binding",
    "validate_authority_obligation_set",
    "validate_manifest",
    "validate_obligation_set",
    "validate_successor_contract",
    "validate_successor_gate_result",
]
