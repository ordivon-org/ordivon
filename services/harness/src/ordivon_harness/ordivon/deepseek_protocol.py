"""Pure DeepSeek provider wire representations for tools, history, and conclusions.

No HTTP transport, credentials, Run scheduling, or durable state lives here.
"""

from __future__ import annotations

from collections.abc import Mapping

from anc_canonical import JsonValue, canonical_bytes, validate_json_value

from ..completion import structured_completion_result_schema
from ..tool_program import HarnessToolProgram, HarnessToolProgramAction, HarnessToolProgramStep
from ..working_view import (
    WORKING_SET_HISTORY_CONTROL_NAME,
    AgentCallerIngressPromotionProposal,
    AgentWorkingSetTransitionProposal,
    HarnessWorkingSetPin,
)
from .model import AgentRunConclusion, AgentStructuredResult, AgentToolDefinition

_CONCLUSION_TOOL_NAME = "submit_run_conclusion"
_WORKING_SET_TRANSITION_TOOL_NAME = "propose_working_set_transition"
_CALLER_INGRESS_PROMOTION_TOOL_NAME = "promote_caller_ingress"
_TOOL_PROGRAM_ACTION_NAME = "compose_tool_program"


def _conclusion_tool(
    structured_result_schema: dict[str, JsonValue] | None = None,
) -> dict[str, JsonValue]:
    string_array: dict[str, JsonValue] = {
        "type": "array",
        "items": {"type": "string"},
        "maxItems": 128,
    }
    result_property: dict[str, JsonValue]
    result_name: str
    if structured_result_schema is None:
        result_name = "summary"
        result_property = {"type": "string", "minLength": 1}
    else:
        result_name = "result"
        result_property = structured_result_schema
    return {
        "type": "function",
        "function": {
            "name": _CONCLUSION_TOOL_NAME,
            "description": (
                "Stop this bounded Harness Run and submit a candidate result for independent "
                "caller or domain verification. Use candidate_completed when the available "
                "bounded evidence supports the candidate result. Use needs_input when a "
                "required fact remains unresolved after the useful available observations, "
                "including when further observation-only searches would only repeat or "
                "rephrase evidence already seen. This does not complete caller-owned work."
            ),
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["candidate_completed", "needs_input"],
                        "description": (
                            "Choose needs_input rather than continuing equivalent bounded "
                            "searches when required evidence remains unavailable or unknown."
                        ),
                    },
                    result_name: result_property,
                    "artifact_refs": string_array,
                    "evidence_refs": string_array,
                    "unresolved_unknowns": string_array,
                },
                "required": [
                    "status",
                    result_name,
                    "artifact_refs",
                    "evidence_refs",
                    "unresolved_unknowns",
                ],
            },
        },
    }


def _tool_program_action_tool(
    allowed_tool_names: tuple[str, ...],
    *,
    max_steps: int,
) -> dict[str, JsonValue]:
    return {
        "type": "function",
        "function": {
            "name": _TOOL_PROGRAM_ACTION_NAME,
            "description": (
                "Compose one bounded linear program over only the Runtime Tools admitted "
                "for this exact turn. Use this when later Tool arguments depend mechanically "
                "on exact JSON fields observed from earlier steps. Each step remains one "
                "physical Tool Call with normal budget, recovery, UNKNOWN, and effect semantics. "
                'References use {"$harnessObservationRef":{"stepId":...,"path":[...]}}. '
                "No branching, loops, shell, Python, expressions, or hidden Tools are allowed."
            ),
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "steps": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": max_steps,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "step_id": {"type": "string", "minLength": 1},
                                "tool_name": {
                                    "type": "string",
                                    "enum": list(allowed_tool_names),
                                },
                                "arguments": {
                                    "type": "object",
                                    "additionalProperties": True,
                                },
                            },
                            "required": ["step_id", "tool_name", "arguments"],
                        },
                    },
                    "outputs": {
                        "type": "object",
                        "additionalProperties": True,
                    },
                },
                "required": ["steps", "outputs"],
            },
        },
    }


def _parse_tool_program_action(
    action_call_id: str,
    arguments: dict[str, JsonValue],
) -> HarnessToolProgramAction:
    if set(arguments) != {"steps", "outputs"}:
        raise ValueError("DeepSeek ToolProgram fields differ")
    raw_steps = arguments["steps"]
    raw_outputs = arguments["outputs"]
    if not isinstance(raw_steps, list) or any(not isinstance(item, dict) for item in raw_steps):
        raise TypeError("DeepSeek ToolProgram steps must be objects")
    if not isinstance(raw_outputs, dict):
        raise TypeError("DeepSeek ToolProgram outputs must be an object")
    steps: list[HarnessToolProgramStep] = []
    for raw_step in raw_steps:
        if set(raw_step) != {"step_id", "tool_name", "arguments"}:
            raise ValueError("DeepSeek ToolProgram step fields differ")
        if not isinstance(raw_step["arguments"], dict):
            raise TypeError("DeepSeek ToolProgram step arguments must be an object")
        steps.append(
            HarnessToolProgramStep(
                step_id=raw_step["step_id"],
                tool_name=raw_step["tool_name"],
                arguments=dict(raw_step["arguments"]),
            )
        )
    return HarnessToolProgramAction(
        action_call_id=action_call_id,
        program=HarnessToolProgram(steps=tuple(steps), outputs=dict(raw_outputs)),
    )


def _working_set_transition_tool() -> dict[str, JsonValue]:
    pin_schema: dict[str, JsonValue] = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "slot": {"type": "string", "minLength": 1},
            "logical_ref": {"type": "string", "minLength": 1},
            "logical_generation": {"type": "string", "minLength": 1},
            "resolved_digest": {
                "type": "string",
                "pattern": "^sha256:[0-9a-f]{64}$",
            },
        },
        "required": [
            "slot",
            "logical_ref",
            "logical_generation",
            "resolved_digest",
        ],
    }
    return {
        "type": "function",
        "function": {
            "name": _WORKING_SET_TRANSITION_TOOL_NAME,
            "description": (
                "Choose the exact already-known sources that should form the next "
                "committed Working Set. This changes only your model-visible cognition "
                "view; it is not an external Tool effect and does not discover sources. "
                "Use an unchanged exact pin selection only when you intentionally want "
                "a new cognition attempt with the same durable sources; that is an "
                "attempt reset, not progress and not a way to wait for caller input. "
                "When waiting for caller input, submit a needs_input conclusion instead."
            ),
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "next_attempt_id": {"type": "string", "minLength": 1},
                    "pins": {
                        "type": "array",
                        "items": pin_schema,
                        "maxItems": 128,
                    },
                    "basis": {"type": "string", "minLength": 1},
                },
                "required": ["next_attempt_id", "pins", "basis"],
            },
        },
    }


def _caller_ingress_promotion_tool(
    allowed_caller_indexes: tuple[int, ...],
) -> dict[str, JsonValue]:
    return {
        "type": "function",
        "function": {
            "name": _CALLER_INGRESS_PROMOTION_TOOL_NAME,
            "description": (
                "Add exact messages from the current caller interaction to the current "
                "durable Working Set. Choose only message indexes you actually saw and "
                "one new successor slot. Existing selected sources are retained "
                "mechanically; do not restate or guess their pin identities. You cannot "
                "provide or rewrite promoted bytes; Harness derives them from caller-ingress "
                "authority. This is cognition state, not a Runtime effect."
            ),
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "next_attempt_id": {"type": "string", "minLength": 1},
                    "promotion_slot": {"type": "string", "minLength": 1},
                    "caller_message_indexes": {
                        "type": "array",
                        "items": {
                            "type": "integer",
                            "enum": list(allowed_caller_indexes),
                        },
                        "minItems": 1,
                        "maxItems": min(32, len(allowed_caller_indexes)),
                    },
                    "basis": {"type": "string", "minLength": 1},
                },
                "required": [
                    "next_attempt_id",
                    "promotion_slot",
                    "caller_message_indexes",
                    "basis",
                ],
            },
        },
    }


def _parse_caller_ingress_promotion(
    arguments: dict[str, JsonValue],
) -> AgentCallerIngressPromotionProposal:
    expected = {
        "next_attempt_id",
        "promotion_slot",
        "caller_message_indexes",
        "basis",
    }
    if set(arguments) != expected:
        raise ValueError("DeepSeek caller ingress promotion fields differ")
    next_attempt_id = arguments["next_attempt_id"]
    promotion_slot = arguments["promotion_slot"]
    basis = arguments["basis"]
    raw_indexes = arguments["caller_message_indexes"]
    if not all(isinstance(value, str) for value in (next_attempt_id, promotion_slot, basis)):
        raise TypeError("DeepSeek caller ingress promotion text fields are invalid")
    if not isinstance(raw_indexes, list):
        raise TypeError("DeepSeek caller ingress promotion indexes must be a list")
    return AgentCallerIngressPromotionProposal(
        next_attempt_id=next_attempt_id,
        promotion_slot=promotion_slot,
        caller_message_indexes=tuple(raw_indexes),
        basis=basis,
    )


def _working_set_history_tool() -> dict[str, JsonValue]:
    return {
        "type": "function",
        "function": {
            "name": WORKING_SET_HISTORY_CONTROL_NAME,
            "description": (
                "Inspect a bounded reverse-chronological catalog of exact source pins "
                "from earlier committed Working Sets. This does not read source content, "
                "rank memories, or change cognition. Use propose_working_set_transition "
                "separately if you choose to recall one of the returned pins."
            ),
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 32,
                    },
                    "before_sequence": {
                        "type": "integer",
                        "minimum": 1,
                    },
                },
                "required": ["limit"],
            },
        },
    }


def _parse_working_set_transition(
    arguments: dict[str, JsonValue],
) -> AgentWorkingSetTransitionProposal:
    if set(arguments) != {"next_attempt_id", "pins", "basis"}:
        raise ValueError("DeepSeek Working Set transition fields differ")
    next_attempt_id = arguments["next_attempt_id"]
    basis = arguments["basis"]
    raw_pins = arguments["pins"]
    if not isinstance(next_attempt_id, str) or not isinstance(basis, str):
        raise TypeError("DeepSeek Working Set transition text fields are invalid")
    if not isinstance(raw_pins, list) or any(not isinstance(item, dict) for item in raw_pins):
        raise TypeError("DeepSeek Working Set transition pins must be objects")
    pins: list[HarnessWorkingSetPin] = []
    for raw_pin in raw_pins:
        if set(raw_pin) != {
            "slot",
            "logical_ref",
            "logical_generation",
            "resolved_digest",
        }:
            raise ValueError("DeepSeek Working Set transition pin fields differ")
        pins.append(
            HarnessWorkingSetPin(
                slot=raw_pin["slot"],
                logical_ref=raw_pin["logical_ref"],
                logical_generation=raw_pin["logical_generation"],
                resolved_digest=raw_pin["resolved_digest"],
            )
        )
    return AgentWorkingSetTransitionProposal(
        next_attempt_id=next_attempt_id,
        pins=tuple(sorted(pins, key=lambda pin: pin.slot)),
        basis=basis,
    )


def _provider_tool(tool: AgentToolDefinition) -> dict[str, JsonValue]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_schema,
        },
    }


def _provider_messages(
    messages: tuple[dict[str, JsonValue], ...],
) -> list[dict[str, JsonValue]]:
    translated: list[dict[str, JsonValue]] = []
    for message in messages:
        role = message.get("role")
        if role in {"system", "user"}:
            content = message.get("content")
            if not isinstance(content, str):
                raise ValueError(f"DeepSeek {role} message content must be a string")
            translated.append({"role": role, "content": content})
            continue
        if role == "assistant":
            raw_calls = message.get("toolCalls")
            conclusion = message.get("conclusion")
            tool_program_action = message.get("toolProgramAction")
            if conclusion is not None:
                if not isinstance(conclusion, dict):
                    raise ValueError("DeepSeek assistant conclusion history is invalid")
                validate_json_value(conclusion)
                content = message.get("content")
                if content is not None and not isinstance(content, str):
                    raise ValueError("DeepSeek assistant content must be a string or null")
                retained = "Retained Harness conclusion: " + canonical_bytes(conclusion).decode(
                    "utf-8"
                )
                if content:
                    retained = f"{content}\n\n{retained}"
                translated.append({"role": "assistant", "content": retained})
                continue
            if tool_program_action is not None:
                if not isinstance(tool_program_action, dict):
                    raise ValueError("DeepSeek assistant ToolProgram history is invalid")
                HarnessToolProgramAction.from_dict(tool_program_action)
                content = message.get("content")
                if content is not None and not isinstance(content, str):
                    raise ValueError("DeepSeek assistant content must be a string or null")
                retained = "Retained Harness ToolProgram action: " + canonical_bytes(
                    tool_program_action
                ).decode("utf-8")
                if content:
                    retained = f"{content}\n\n{retained}"
                translated.append({"role": "assistant", "content": retained})
                continue
            if not isinstance(raw_calls, list) or not raw_calls:
                raise ValueError("DeepSeek assistant history must retain Tool Calls")
            calls: list[dict[str, JsonValue]] = []
            for raw_call in raw_calls:
                if (
                    not isinstance(raw_call, dict)
                    or not {
                        "toolCallId",
                        "name",
                        "arguments",
                    }.issubset(raw_call)
                    or set(raw_call)
                    - {
                        "toolCallId",
                        "name",
                        "arguments",
                        "providerArguments",
                    }
                ):
                    raise ValueError("DeepSeek assistant Tool Call history is invalid")
                call_id = raw_call["toolCallId"]
                name = raw_call["name"]
                arguments = raw_call["arguments"]
                if not isinstance(call_id, str) or not isinstance(name, str):
                    raise TypeError("DeepSeek assistant Tool Call identities are invalid")
                validate_json_value(arguments)
                calls.append(
                    {
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": name,
                            "arguments": canonical_bytes(arguments).decode("utf-8"),
                        },
                    }
                )
            content = message.get("content")
            if content is not None and not isinstance(content, str):
                raise ValueError("DeepSeek assistant content must be a string or null")
            translated.append({"role": "assistant", "content": content, "tool_calls": calls})
            continue
        if role == "tool":
            tool_call_id = message.get("toolCallId")
            observation = message.get("observation")
            if not isinstance(tool_call_id, str):
                raise ValueError("DeepSeek Tool message has no Tool Call identity")
            validate_json_value(observation)
            translated.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": canonical_bytes(observation).decode("utf-8"),
                }
            )
            continue
        raise ValueError(f"unsupported DeepSeek message role: {role}")
    return translated


def _string_tuple(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"DeepSeek conclusion {label} must be a string array")
    return tuple(value)


def _parse_conclusion(
    arguments: dict[str, JsonValue],
    *,
    completion_contract: Mapping[str, JsonValue] | None = None,
) -> AgentRunConclusion:
    structured = (
        None
        if completion_contract is None
        else structured_completion_result_schema(completion_contract)
    )
    result_name = "result" if structured is not None else "summary"
    expected = {
        "status",
        result_name,
        "artifact_refs",
        "evidence_refs",
        "unresolved_unknowns",
    }
    if set(arguments) != expected:
        raise ValueError("DeepSeek conclusion fields differ")
    status = arguments["status"]
    if not isinstance(status, str):
        raise TypeError("DeepSeek conclusion status must be a string")
    structured_result: AgentStructuredResult | None = None
    if structured is None:
        summary = arguments["summary"]
        if not isinstance(summary, str):
            raise TypeError("DeepSeek conclusion summary must be a string")
    else:
        structured_result = AgentStructuredResult(arguments["result"])
        summary = f"Structured result {structured_result.digest}"
    return AgentRunConclusion(
        status=status,
        summary=summary,
        artifact_refs=_string_tuple(arguments["artifact_refs"], "Artifact refs"),
        evidence_refs=_string_tuple(arguments["evidence_refs"], "evidence refs"),
        unresolved_unknowns=_string_tuple(arguments["unresolved_unknowns"], "unresolved unknowns"),
        structured_result=structured_result,
    )
