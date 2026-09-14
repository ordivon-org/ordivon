"""Provider-neutral authority boundary for Debug Adapter Protocol integrations.

DAP mixes observation with process control and direct mutation.  Harness therefore does
not model a debugger provider as globally read-only.  Every admitted action has a fixed
consequence class, and transient DAP handles are fenced to one exact stopped epoch.
Transport, adapter lifecycle, and debugger implementation remain external provider
mechanics.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol, runtime_checkable

from anc_canonical import JsonValue, canonical_digest, validate_json_value

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

OBSERVATION = "observation"
EXECUTION_CONTROL = "execution-control"
DEBUGGER_CONFIGURATION = "debugger-configuration"
TARGET_MUTATION = "target-mutation"
PROCESS_LIFECYCLE = "process-lifecycle"
EFFECT_CAPABLE = "effect-capable"

_PROCESS_OWNERS = frozenset({"runtime", "dap-provider", "external"})
_EFFECT_EXECUTORS = frozenset({"none", "runtime", "dap-provider", "external"})

_ACTION_CONSEQUENCE = {
    # Observation-only protocol requests in the Harness R8 contract.
    "threads": OBSERVATION,
    "stackTrace": OBSERVATION,
    "scopes": OBSERVATION,
    "variables": OBSERVATION,
    "source": OBSERVATION,
    "modules": OBSERVATION,
    "loadedSources": OBSERVATION,
    "readMemory": OBSERVATION,
    "disassemble": OBSERVATION,
    "breakpointLocations": OBSERVATION,
    "dataBreakpointInfo": OBSERVATION,
    "exceptionInfo": OBSERVATION,
    "completions": OBSERVATION,
    # These alter target execution state even when they do not mutate source bytes.
    "continue": EXECUTION_CONTROL,
    "next": EXECUTION_CONTROL,
    "stepIn": EXECUTION_CONTROL,
    "stepOut": EXECUTION_CONTROL,
    "stepBack": EXECUTION_CONTROL,
    "reverseContinue": EXECUTION_CONTROL,
    "pause": EXECUTION_CONTROL,
    "goto": EXECUTION_CONTROL,
    "restartFrame": EXECUTION_CONTROL,
    # Breakpoints/watchpoints alter debugger and potentially inferior state.
    "setBreakpoints": DEBUGGER_CONFIGURATION,
    "setFunctionBreakpoints": DEBUGGER_CONFIGURATION,
    "setExceptionBreakpoints": DEBUGGER_CONFIGURATION,
    "setInstructionBreakpoints": DEBUGGER_CONFIGURATION,
    "setDataBreakpoints": DEBUGGER_CONFIGURATION,
    # Direct target state mutation.
    "setVariable": TARGET_MUTATION,
    "setExpression": TARGET_MUTATION,
    "writeMemory": TARGET_MUTATION,
    # Session/process lifecycle.
    "launch": PROCESS_LIFECYCLE,
    "attach": PROCESS_LIFECYCLE,
    "restart": PROCESS_LIFECYCLE,
    "terminate": PROCESS_LIFECYCLE,
    "disconnect": PROCESS_LIFECYCLE,
    # DAP evaluate cannot be treated as read-only: debuggers may execute commands,
    # inferior function calls, or other target-affecting expressions.
    "evaluate": EFFECT_CAPABLE,
}

_STOP_SCOPED_ACTIONS = frozenset(
    {
        "stackTrace",
        "scopes",
        "variables",
        "readMemory",
        "disassemble",
        "dataBreakpointInfo",
        "exceptionInfo",
        "continue",
        "next",
        "stepIn",
        "stepOut",
        "stepBack",
        "reverseContinue",
        "pause",
        "goto",
        "restartFrame",
        "setVariable",
        "setExpression",
        "writeMemory",
        "evaluate",
    }
)


@dataclass(frozen=True, slots=True)
class DapProviderIdentity:
    provider_id: str
    implementation: str
    version: str

    def __post_init__(self) -> None:
        _trimmed(self.provider_id, "DAP provider id")
        _trimmed(self.implementation, "DAP provider implementation")
        _trimmed(self.version, "DAP provider version")

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "providerId": self.provider_id,
            "implementation": self.implementation,
            "version": self.version,
        }


@dataclass(frozen=True, slots=True)
class DapProviderReady:
    identity: DapProviderIdentity
    supported_actions: tuple[str, ...]
    raw_capabilities: dict[str, JsonValue]

    def __post_init__(self) -> None:
        if not self.supported_actions:
            raise ValueError("DAP provider must declare at least one supported action")
        if tuple(sorted(set(self.supported_actions))) != self.supported_actions:
            raise ValueError("DAP supported actions must be unique and sorted")
        unknown = [action for action in self.supported_actions if action not in _ACTION_CONSEQUENCE]
        if unknown:
            raise ValueError(f"DAP provider advertises unknown Harness actions: {unknown}")
        validate_json_value(self.raw_capabilities)

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        value: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.harness-dap-provider-ready",
            "identity": self.identity.to_dict(),
            "supportedActions": list(self.supported_actions),
            "rawCapabilities": self.raw_capabilities,
        }
        validate_json_value(value)
        return value


@dataclass(frozen=True, slots=True)
class DapTargetBinding:
    session_id: str
    target_ref: str
    process_owner: str
    effect_executor: str

    def __post_init__(self) -> None:
        _trimmed(self.session_id, "DAP session id")
        _trimmed(self.target_ref, "DAP target reference")
        if self.process_owner not in _PROCESS_OWNERS:
            raise ValueError("DAP process owner is invalid")
        if self.effect_executor not in _EFFECT_EXECUTORS - {"none"}:
            raise ValueError("DAP target effect executor must be explicit and non-none")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        value: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.harness-dap-target-binding",
            "sessionId": self.session_id,
            "targetRef": self.target_ref,
            "processOwner": self.process_owner,
            "effectExecutor": self.effect_executor,
        }
        validate_json_value(value)
        return value


@dataclass(frozen=True, slots=True)
class DapStopEpoch:
    session_id: str
    epoch: int
    thread_id: int
    reason: str
    all_threads_stopped: bool

    def __post_init__(self) -> None:
        _trimmed(self.session_id, "DAP stop session id")
        if type(self.epoch) is not int or self.epoch < 1:
            raise ValueError("DAP stop epoch must be a positive integer")
        if type(self.thread_id) is not int or self.thread_id < 1:
            raise ValueError("DAP stopped thread id must be a positive integer")
        _trimmed(self.reason, "DAP stop reason")
        if type(self.all_threads_stopped) is not bool:
            raise TypeError("DAP allThreadsStopped must be boolean")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        value: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.harness-dap-stop-epoch",
            "sessionId": self.session_id,
            "epoch": self.epoch,
            "threadId": self.thread_id,
            "reason": self.reason,
            "allThreadsStopped": self.all_threads_stopped,
        }
        validate_json_value(value)
        return value


@dataclass(frozen=True, slots=True)
class DapTransientHandle:
    stop_digest: str
    handle_kind: str
    handle: int

    def __post_init__(self) -> None:
        if _DIGEST_RE.fullmatch(self.stop_digest) is None:
            raise ValueError("DAP transient handle requires exact stop digest")
        if self.handle_kind not in {"frame", "variables", "memory"}:
            raise ValueError("DAP transient handle kind is invalid")
        if type(self.handle) is not int or self.handle < 0:
            raise ValueError("DAP transient handle must be a non-negative integer")

    def require_stop(self, stop: DapStopEpoch) -> None:
        if self.stop_digest != stop.digest:
            raise ValueError("DAP transient handle belongs to a different stopped epoch")

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "stopDigest": self.stop_digest,
            "handleKind": self.handle_kind,
            "handle": self.handle,
        }


@dataclass(frozen=True, slots=True)
class DapActionIntent:
    session_id: str
    target_binding_digest: str
    action: str
    arguments: dict[str, JsonValue]
    stop_digest: str | None = None

    def __post_init__(self) -> None:
        _trimmed(self.session_id, "DAP action session id")
        if _DIGEST_RE.fullmatch(self.target_binding_digest) is None:
            raise ValueError("DAP action requires exact target binding digest")
        if self.action not in _ACTION_CONSEQUENCE:
            raise ValueError(f"DAP action is not admitted by Harness: {self.action}")
        validate_json_value(self.arguments)
        if self.action in _STOP_SCOPED_ACTIONS:
            if self.stop_digest is None or _DIGEST_RE.fullmatch(self.stop_digest) is None:
                raise ValueError(f"DAP action {self.action} requires exact stop digest")
        elif self.stop_digest is not None and _DIGEST_RE.fullmatch(self.stop_digest) is None:
            raise ValueError("DAP action stop digest is malformed")

    @property
    def consequence(self) -> str:
        return _ACTION_CONSEQUENCE[self.action]

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        value: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.harness-dap-action-intent",
            "sessionId": self.session_id,
            "targetBindingDigest": self.target_binding_digest,
            "action": self.action,
            "consequence": self.consequence,
            "arguments": self.arguments,
            "stopDigest": self.stop_digest,
        }
        validate_json_value(value)
        return value


@dataclass(frozen=True, slots=True)
class DapActionObservation:
    intent_digest: str
    action: str
    consequence: str
    response: dict[str, JsonValue]
    events: tuple[dict[str, JsonValue], ...]
    effect_executor: str

    def __post_init__(self) -> None:
        if _DIGEST_RE.fullmatch(self.intent_digest) is None:
            raise ValueError("DAP observation requires exact intent digest")
        expected = _ACTION_CONSEQUENCE.get(self.action)
        if expected is None or expected != self.consequence:
            raise ValueError("DAP observation consequence differs from Harness action law")
        validate_json_value(self.response)
        for event in self.events:
            validate_json_value(event)
        if self.effect_executor not in _EFFECT_EXECUTORS:
            raise ValueError("DAP observation effect executor is invalid")
        if self.consequence == OBSERVATION and self.effect_executor != "none":
            raise ValueError("observation-only DAP action cannot claim an effect executor")
        if self.consequence != OBSERVATION and self.effect_executor == "none":
            raise ValueError("effectful DAP action must identify its physical effect executor")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        value: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.harness-dap-action-observation",
            "intentDigest": self.intent_digest,
            "action": self.action,
            "consequence": self.consequence,
            "response": self.response,
            "events": list(self.events),
            "effectExecutor": self.effect_executor,
        }
        validate_json_value(value)
        return value


@runtime_checkable
class HarnessDapProviderPort(Protocol):
    """Replaceable DAP provider boundary.

    Harness owns action consequence classification and handle freshness.  The provider
    owns protocol transport and debugger mechanics.  Effectful requests require separate
    Run/Tool authority before they are passed to this port; implementing this protocol
    does not itself grant that authority.
    """

    async def initialize(self) -> DapProviderReady: ...

    async def execute(self, intent: DapActionIntent) -> DapActionObservation: ...

    async def shutdown(self) -> None: ...


def dap_action_consequence(action: str) -> str:
    try:
        return _ACTION_CONSEQUENCE[action]
    except KeyError as error:
        raise ValueError(f"DAP action is not admitted by Harness: {action}") from error


def admitted_dap_actions() -> tuple[str, ...]:
    return tuple(sorted(_ACTION_CONSEQUENCE))


def _trimmed(value: str, label: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty and trimmed")


__all__ = [
    "DEBUGGER_CONFIGURATION",
    "EFFECT_CAPABLE",
    "EXECUTION_CONTROL",
    "HarnessDapProviderPort",
    "OBSERVATION",
    "PROCESS_LIFECYCLE",
    "TARGET_MUTATION",
    "DapActionIntent",
    "DapActionObservation",
    "DapProviderIdentity",
    "DapProviderReady",
    "DapStopEpoch",
    "DapTargetBinding",
    "DapTransientHandle",
    "admitted_dap_actions",
    "dap_action_consequence",
]
