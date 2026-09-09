"""Recommended Host-free public facade for Agent applications.

This surface exposes application-level cognitive Run contracts, Provider/model
adaptation, completion evidence, and domain-owned Tool loops. Concrete SQLite stores,
standalone runners, and Runtime bridge implementations are internal migration surfaces. It
does not import Ordivon Host or make Host Task authority a prerequisite for a
Harness Run.

Host integrations are adapters around this caller-neutral authority; they do not
change Harness persistence or execution ownership.
"""

from .completion import (
    decode_structured_completion_result,
    structured_completion_contract_digest,
    structured_completion_result_schema,
)
from .core_contracts import (
    HarnessBoundReference,
    HarnessCorrelationContext,
    HarnessPrivacyPolicy,
    HarnessRunContract,
    STRUCTURED_COMPLETION_MODE,
)
from .execution_binding import HarnessExecutionBinding, HarnessRuntimeReference
from .independent_result import IndependentCompletionProposal, IndependentHarnessRunReceipt
from .loop_driver import DELIBERATE_THEN_ACT_LOOP_DRIVER, SEQUENTIAL_LOOP_DRIVER
from .mandate import (
    CompiledHarnessAttempt,
    HarnessExecutionMandate,
    HarnessExecutionProfile,
    HarnessExecutionStrategy,
    HarnessLoopDriverRef,
    HarnessMandateConsumption,
    compile_harness_attempt,
)
from .ordivon.deepseek import DeepSeekSettings, DeepSeekTurnAdapter
from .ordivon.loop import RunBudget, RunStopCode
from .ordivon.model import AgentTurnAdapter, AgentTurnRequest, AgentTurnResult
from .ordivon.sqlite_agent_bridge import (
    NO_TOOL_AGENT_GRANT_DIGEST,
    NO_TOOL_AGENT_SURFACE_DIGEST,
)
from .ordivon.sqlite_runtime_bridge import (
    INDEPENDENT_SEARCH_TOOL_GRANT_DIGEST,
    INDEPENDENT_SEARCH_TOOL_SURFACE_DIGEST,
)
from .runtime_port import (
    HarnessRuntimeClient,
    HarnessRuntimeClientError,
    HarnessRuntimeErrorDetail,
    HarnessRuntimeToolRejected,
)
from .strategy_selection import (
    HarnessAgentStrategySelection,
    HarnessPriorAttemptEvidence,
    HarnessStrategyEvidence,
    HarnessStrategySelectionContext,
    admit_harness_agent_strategy,
    build_harness_strategy_selection_context,
    compile_harness_selected_attempt,
    derive_harness_mandate_consumption,
)
from .provider_use_policy import (
    HarnessProviderRoute,
    HarnessProviderUsePolicy,
    HarnessProviderUsePolicyError,
)
from .agent_run import (
    HarnessAgentExecution,
    HarnessAgentRun,
    HarnessAgentRunCompositionError,
    HarnessCognitionProfile,
    HarnessCognitionSeed,
    HarnessCognitionSeedSource,
    HarnessCognitionSource,
)
from .domain_tools import (
    AgentToolDefinition,
    DomainToolBridge,
    DomainToolCatalog,
    DomainToolLoopPlan,
    DomainToolLoopRunner,
    ToolBridgeError,
    ToolBridgeErrorKind,
    ToolObservation,
)

__all__ = [
    "AgentTurnAdapter",
    "HarnessAgentExecution",
    "HarnessAgentRun",
    "HarnessAgentRunCompositionError",
    "HarnessCognitionProfile",
    "HarnessCognitionSeed",
    "HarnessCognitionSeedSource",
    "HarnessCognitionSource",
    "AgentTurnRequest",
    "AgentTurnResult",
    "CompiledHarnessAttempt",
    "DeepSeekSettings",
    "DeepSeekTurnAdapter",
    "HarnessBoundReference",
    "HarnessCorrelationContext",
    "HarnessExecutionBinding",
    "HarnessExecutionMandate",
    "HarnessMandateConsumption",
    "HarnessExecutionProfile",
    "HarnessExecutionStrategy",
    "HarnessLoopDriverRef",
    "HarnessAgentStrategySelection",
    "HarnessPriorAttemptEvidence",
    "HarnessStrategyEvidence",
    "HarnessStrategySelectionContext",
    "AgentToolDefinition",
    "DomainToolBridge",
    "DomainToolCatalog",
    "DomainToolLoopPlan",
    "DomainToolLoopRunner",
    "ToolBridgeError",
    "ToolBridgeErrorKind",
    "ToolObservation",
    "HarnessPrivacyPolicy",
    "HarnessRunContract",
    "HarnessRuntimeClient",
    "HarnessRuntimeClientError",
    "HarnessRuntimeErrorDetail",
    "HarnessRuntimeReference",
    "HarnessRuntimeToolRejected",
    "INDEPENDENT_SEARCH_TOOL_GRANT_DIGEST",
    "INDEPENDENT_SEARCH_TOOL_SURFACE_DIGEST",
    "NO_TOOL_AGENT_GRANT_DIGEST",
    "NO_TOOL_AGENT_SURFACE_DIGEST",
    "IndependentCompletionProposal",
    "IndependentHarnessRunReceipt",
    "DELIBERATE_THEN_ACT_LOOP_DRIVER",
    "SEQUENTIAL_LOOP_DRIVER",
    "RunBudget",
    "RunStopCode",
    "STRUCTURED_COMPLETION_MODE",
    "admit_harness_agent_strategy",
    "build_harness_strategy_selection_context",
    "compile_harness_attempt",
    "compile_harness_selected_attempt",
    "decode_structured_completion_result",
    "derive_harness_mandate_consumption",
    "structured_completion_contract_digest",
    "structured_completion_result_schema",
    "HarnessProviderRoute",
    "HarnessProviderUsePolicy",
    "HarnessProviderUsePolicyError",
]
