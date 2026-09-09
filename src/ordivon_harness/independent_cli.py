from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from anc_canonical import JsonValue, validate_json_value

from .agent_run import HarnessAgentRun
from .core_contracts import HarnessRunContract
from .independent_result import IndependentRunRecorder, StoredIndependentRunResult
from .ordivon.deepseek import DeepSeekSettings, DeepSeekTurnAdapter
from .ordivon.model import AgentTurnAdapter
from .ordivon.sqlite_agent_bridge import (
    NO_TOOL_AGENT_GRANT_DIGEST,
    NO_TOOL_AGENT_SURFACE_DIGEST,
)
from .ordivon.sqlite_run_store import SQLiteHarnessRunContinuityStore
from .sqlite_store import SQLiteHarnessStore
from .standalone import HarnessAgentExecution
from .store import HarnessRunStatus


def dispatch(args, *, clock_ms) -> dict[str, object]:
    command = args.command
    root = _state_root(args)
    if command == "doctor":
        with SQLiteHarnessStore(root) as store:
            return {
                "ok": True,
                "authority": "independent-harness-run",
                "stateRoot": str(root),
                "store": store.doctor(full=True),
            }
    if command == "status":
        with SQLiteHarnessStore(root) as store:
            return {
                "ok": True,
                "authority": "independent-harness-run",
                "stateRoot": str(root),
                "run": store.load_run(args.harness_run_id).to_dict(),
            }
    if command == "inspect":
        with SQLiteHarnessStore(root) as store:
            return _inspect(store, args.harness_run_id, root=root, clock_ms=clock_ms)
    if command == "explain":
        with SQLiteHarnessStore(root) as store:
            inspected = _inspect(store, args.harness_run_id, root=root, clock_ms=clock_ms)
            inspected["proofBoundaries"] = {
                "durable": (
                    "Run/Contract/Provider/Snapshot/Recovery objects are exact Harness "
                    "Journal/CAS projections"
                ),
                "processLocal": (
                    "fresh durable inspection does not infer whether an application-owned "
                    "Adapter or Runtime client is currently live; use HarnessAgentRun.explain() "
                    "for validated in-process composition"
                ),
                "external": "Provider/Runtime/domain liveness and world truth are not claimed",
            }
            return inspected
    if command == "run":
        contract = _load_contract(args.contract)
        if (
            contract.tool_catalog_digest != NO_TOOL_AGENT_SURFACE_DIGEST
            or contract.tool_grant_digest != NO_TOOL_AGENT_GRANT_DIGEST
        ):
            raise ValueError(
                "independent CLI execution currently supports only the canonical "
                "no-Tool profile; Tool-bearing Runs require an application-supplied "
                "HarnessRuntimeClient through ordivon_harness.api"
            )
        messages = _load_messages(args)
        if not messages:
            raise ValueError("independent run requires at least one input message")
        handle = HarnessAgentRun.create(
            root,
            contract,
            lambda exact_contract: _adapter(exact_contract, args),
            clock_ms=clock_ms,
            monotonic_ms=clock_ms,
        )
        status = handle.status()
        if status["status"] in {
            HarnessRunStatus.STOPPED.value,
            HarnessRunStatus.COMPLETED.value,
            HarnessRunStatus.FAILED.value,
        }:
            with SQLiteHarnessStore(root) as store:
                return _inspect(store, contract.harness_run_id, root=root, clock_ms=clock_ms)
        if status["status"] == HarnessRunStatus.PAUSED.value:
            raise ValueError("paused independent Harness Run requires resume")
        execution = handle.run(messages)
        with SQLiteHarnessStore(root) as store:
            return _execution_value(execution, root=root, store=store)
    if command == "resume":
        handle = HarnessAgentRun.open(
            root,
            args.harness_run_id,
            lambda exact_contract: _adapter(exact_contract, args),
            clock_ms=clock_ms,
            monotonic_ms=clock_ms,
        )
        execution = handle.resume(additional_messages=_load_messages(args))
        with SQLiteHarnessStore(root) as store:
            return _execution_value(execution, root=root, store=store)
    raise ValueError(f"unsupported independent Harness command: {command}")


def _state_root(args) -> Path:
    root = args.state_root
    if root is None:
        raise ValueError("Harness command requires --state-root")
    return root.expanduser().resolve()


def _load_contract(path: Path) -> HarnessRunContract:
    raw = _load_json(path)
    if not isinstance(raw, dict):
        raise ValueError("Harness Run Contract file must contain one JSON object")
    return HarnessRunContract.from_dict(raw)


def _load_messages(args) -> tuple[dict[str, JsonValue], ...]:
    values: list[dict[str, JsonValue]] = []
    path = getattr(args, "messages_json", None)
    if path is not None:
        raw = _load_json(path)
        if not isinstance(raw, list) or any(not isinstance(item, dict) for item in raw):
            raise ValueError("messages JSON must contain an array of objects")
        for item in raw:
            value = dict(item)
            validate_json_value(value)
            values.append(value)
    for message in getattr(args, "message", ()):
        value: dict[str, JsonValue] = {"role": "user", "content": message}
        validate_json_value(value)
        values.append(value)
    return tuple(values)


def _load_json(path: Path) -> Any:
    resolved = path.expanduser().resolve()
    return json.loads(resolved.read_text(encoding="utf-8"))


def _adapter(contract: HarnessRunContract, args) -> AgentTurnAdapter:
    if contract.adapter_id != DeepSeekTurnAdapter.adapter_id:
        raise ValueError(
            "independent CLI execution currently supports only "
            f"{DeepSeekTurnAdapter.adapter_id}; use the Host-free Python API for another Adapter"
        )
    return DeepSeekTurnAdapter(
        DeepSeekSettings.from_secret_file(args.deepseek_secret),
        completion_contract=contract.completion_contract,
    )


def _execution_value(
    execution: HarnessAgentExecution,
    *,
    root: Path,
    store: SQLiteHarnessStore,
) -> dict[str, object]:
    projection = store.load_run(execution.loop_result.harness_run_id)
    terminal = execution.terminal_result
    return {
        "ok": True,
        "authority": "independent-harness-run",
        "stateRoot": str(root),
        "run": projection.to_dict(),
        "stopCode": execution.loop_result.stop_code.value,
        "usage": execution.loop_result.usage,
        "runReceipt": None if terminal is None else terminal.receipt.to_dict(),
        "completionProposal": (
            None
            if terminal is None or terminal.completion_proposal is None
            else terminal.completion_proposal.to_dict()
        ),
    }


def _inspect(
    store: SQLiteHarnessStore,
    harness_run_id: str,
    *,
    root: Path,
    clock_ms,
) -> dict[str, object]:
    projection = store.load_run(harness_run_id)
    continuity = SQLiteHarnessRunContinuityStore.open(
        store,
        harness_run_id,
        clock_ms=clock_ms,
    )
    recorder = IndependentRunRecorder(
        store,
        continuity.contract,
        continuity.binding,
        clock_ms=clock_ms,
    )
    provider: dict[str, JsonValue] | None = None
    try:
        retained_provider = continuity.load_current_provider_call()
        provider = retained_provider.record.to_dict()
    except KeyError:
        pass
    snapshot: dict[str, JsonValue] | None = None
    try:
        snapshot = continuity.load_current_snapshot().snapshot.to_dict()
    except KeyError:
        pass
    terminal: StoredIndependentRunResult | None = None
    if projection.status.terminal:
        try:
            terminal = recorder.load_terminal_result()
        except KeyError:
            pass
    run_value = projection.to_dict()
    run_receipt = None if terminal is None else terminal.receipt.to_dict()
    completion_proposal = (
        None
        if terminal is None or terminal.completion_proposal is None
        else terminal.completion_proposal.to_dict()
    )
    return {
        "ok": True,
        "authority": "independent-harness-run",
        "stateRoot": str(root),
        "run": run_value,
        "contract": continuity.contract.to_dict(),
        "providerCall": provider,
        "snapshot": snapshot,
        "runReceipt": run_receipt,
        "completionProposal": completion_proposal,
    }




__all__ = ["dispatch"]
