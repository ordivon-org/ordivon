from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from anc_canonical import JsonValue, canonical_digest, validate_json_value
from ordivon_harness.agent_tool_observation import HarnessToolObservation
from ordivon_harness.core_contracts import HarnessBoundReference, HarnessRunContract
from ordivon_harness.execution_binding import HarnessExecutionBinding
from ordivon_harness.ordivon.adaptive_edit_bridge import (
    AdaptiveEditRuntimeBridge,
    EDIT_WORKSPACE_DEFINITION,
    READ_EDITABLE_WORKSPACE_DEFINITION,
)
from ordivon_harness.ordivon.deepseek import DeepSeekSettings, DeepSeekTurnAdapter
from ordivon_harness.ordivon.loop import OrdivonAgentLoop, RunBudget
from ordivon_harness.ordivon.model import AgentToolCall, AgentToolDefinition
from ordivon_harness.ordivon.sqlite_run_store import SQLiteHarnessRunContinuityStore
from ordivon_harness.ordivon.tool_errors import ToolBridgeError, ToolBridgeErrorKind
from ordivon_harness.runtime_port import HarnessRuntimeErrorDetail, HarnessRuntimeToolRejected
from ordivon_harness.sqlite_store import SQLiteHarnessStore

ROOT = Path.cwd()
FIXTURE = ROOT / "fixtures/harness-replacement-repository-repair-v1"
ORACLE = ROOT / "evals/harness-repository-repair-001/oracle/allocation.py"
HIDDEN = ROOT / "evals/harness-repository-repair-001/verifier/test_outcome.py"
TASK = json.loads((ROOT / "evals/harness-repository-repair-001/task.json").read_text())
READ_PATHS = ("SPEC.md", "allocation.py", "test_allocation.py")
CODECS = ("exact-replacement-v1", "anchored-line-v1")


def sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


class TreatmentGrant:
    allow_opaque_exec = False

    def allows_path(self, name: str, relative_path: str) -> bool:
        if name == "read_workspace":
            return relative_path in READ_PATHS
        return name == "edit_workspace" and relative_path == "allocation.py"

    def execution_check(self, check_id: str):
        raise KeyError(check_id)


class MemoryRuntime:
    def __init__(self) -> None:
        self.files = {name: (FIXTURE / name).read_text() for name in READ_PATHS}
        self.calls: list[tuple[str, dict[str, JsonValue]]] = []
        self.receipts: dict[str, dict[str, JsonValue]] = {}

    @staticmethod
    def _offset(content: str, line: int, column: int) -> int:
        lines = content.split("\n")
        if line < 1 or line > len(lines) or column < 0 or column > len(lines[line - 1]):
            raise ValueError("invalid position")
        return sum(len(item) + 1 for item in lines[: line - 1]) + len(lines[line - 1][:column])

    def call_tool(self, name: str, arguments: dict[str, JsonValue]) -> dict[str, JsonValue]:
        self.calls.append((name, copy.deepcopy(arguments)))
        if name == "workspace.read":
            path = arguments.get("relativePath")
            if not isinstance(path, str) or path not in self.files:
                raise HarnessRuntimeToolRejected(
                    name,
                    HarnessRuntimeErrorDetail(
                        code="not_found",
                        message="path absent",
                        commit_state="not_started",
                        retryable=False,
                        field="relativePath",
                    ),
                )
            content = self.files[path]
            return {
                "workspaceId": arguments["workspaceId"],
                "relativePath": path,
                "content": content,
                "digest": sha(content),
                "byteLength": len(content.encode()),
            }
        if name == "workspace.patch":
            request_id = arguments.get("clientRequestId")
            assert isinstance(request_id, str)
            if request_id in self.receipts:
                return copy.deepcopy(self.receipts[request_id])
            files = arguments.get("files")
            if not isinstance(files, list) or not files:
                raise AssertionError("patch omitted files")
            prepared: list[tuple[str, str, str]] = []
            patched_files: list[dict[str, JsonValue]] = []
            for file in files:
                assert isinstance(file, dict)
                path = file["relativePath"]
                assert isinstance(path, str)
                before = self.files[path]
                before_digest = sha(before)
                if file.get("expectedDigest") != before_digest:
                    raise HarnessRuntimeToolRejected(
                        name,
                        HarnessRuntimeErrorDetail(
                            code="revision_mismatch",
                            message="expectedDigest mismatch",
                            commit_state="not_committed",
                            retryable=False,
                            field="expectedDigest",
                        ),
                    )
                edits = file["edits"]
                assert isinstance(edits, list)
                resolved = []
                for edit in edits:
                    assert isinstance(edit, dict)
                    rng = edit["range"]
                    assert isinstance(rng, dict)
                    start = rng["start"]
                    end = rng["end"]
                    assert isinstance(start, dict) and isinstance(end, dict)
                    a = self._offset(before, int(start["line"]), int(start["column"]))
                    b = self._offset(before, int(end["line"]), int(end["column"]))
                    expected = edit["expectedText"]
                    replacement = edit.get("replacement", "")
                    assert isinstance(expected, str) and isinstance(replacement, str)
                    if before[a:b] != expected:
                        raise HarnessRuntimeToolRejected(
                            name,
                            HarnessRuntimeErrorDetail(
                                code="revision_mismatch",
                                message="expectedText mismatch",
                                commit_state="not_committed",
                                retryable=False,
                                field="expectedText",
                            ),
                        )
                    resolved.append((a, b, replacement))
                after = before
                for a, b, replacement in sorted(resolved, reverse=True):
                    after = after[:a] + replacement + after[b:]
                prepared.append((path, before, after))
                patched_files.append(
                    {
                        "relativePath": path,
                        "beforeDigest": before_digest,
                        "afterDigest": sha(after),
                        "byteLength": len(after.encode()),
                    }
                )
            for path, _before, after in prepared:
                self.files[path] = after
            receipt = {
                "operationId": "patch:live-ab:" + request_id[-16:],
                "clientRequestId": request_id,
                "requestDigest": canonical_digest(arguments),
                "replayed": False,
                "patch": {"files": patched_files, "diff": "", "diffTruncated": False},
            }
            validate_json_value(receipt)
            self.receipts[request_id] = copy.deepcopy(receipt)
            return receipt
        if name == "workspace.patch.get":
            request_id = arguments.get("clientRequestId")
            assert isinstance(request_id, str)
            receipt = self.receipts.get(request_id)
            if receipt is None:
                raise HarnessRuntimeToolRejected(
                    name,
                    HarnessRuntimeErrorDetail(
                        code="not_found",
                        message="patch absent",
                        commit_state="not_started",
                        retryable=False,
                        field="clientRequestId",
                    ),
                )
            return {
                "operationId": receipt["operationId"],
                "clientRequestId": request_id,
                "requestDigest": receipt["requestDigest"],
                "workspaceId": "ws-live-ab",
                "state": "committed",
                "patch": receipt["patch"],
            }
        raise AssertionError(f"unexpected runtime operation {name}")


def treatment_edit_definition(codec: str) -> AgentToolDefinition:
    schema = copy.deepcopy(EDIT_WORKSPACE_DEFINITION.input_schema)
    branches = schema["oneOf"]
    assert isinstance(branches, list)
    branch = branches[0] if codec == "exact-replacement-v1" else branches[1]
    assert isinstance(branch, dict)
    return AgentToolDefinition(
        name="edit_workspace",
        description=f"Live A/B treatment. Use only {codec}. The sourceDigest must come from the latest read_workspace observation.",
        input_schema=branch,
    )


class TreatmentBridge(AdaptiveEditRuntimeBridge):
    def __init__(self, *args, treatment_codec: str, **kwargs) -> None:
        self.treatment_codec = treatment_codec
        super().__init__(*args, **kwargs)

    def _lower_edit_workspace(self, call: AgentToolCall, *, step_id: str):
        if call.arguments.get("codec") != self.treatment_codec:
            raise ToolBridgeError(
                f"live A/B treatment admits only {self.treatment_codec}",
                kind=ToolBridgeErrorKind.MODEL_CORRECTABLE,
            )
        return super()._lower_edit_workspace(call, step_id=step_id)

    def _observation_from_payload(self, **kwargs) -> HarnessToolObservation:
        observation = super()._observation_from_payload(**kwargs)
        if observation.tool_name != "read_workspace" or observation.status != "observed":
            return observation
        structured = dict(observation.structured_content)
        snapshot = structured.get("editSnapshot")
        if isinstance(snapshot, dict):
            snapshot = dict(snapshot)
            snapshot["codecs"] = [self.treatment_codec]
            structured["editSnapshot"] = snapshot
        return HarnessToolObservation(
            tool_call_id=observation.tool_call_id,
            tool_name=observation.tool_name,
            status=observation.status,
            structured_content=structured,
            runtime_job_ref=observation.runtime_job_ref,
            artifact_refs=observation.artifact_refs,
            reconciled=observation.reconciled,
        )


def verify(source: str) -> dict[str, bool]:
    with tempfile.TemporaryDirectory() as directory:
        ws = Path(directory) / "workspace"
        shutil.copytree(FIXTURE, ws)
        (ws / "allocation.py").write_text(source)
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "ORDIVON_EVAL_WORKSPACE": str(ws)}
        visible = subprocess.run(
            ["/usr/bin/python3", "-m", "unittest", "-q", "test_allocation.py"],
            cwd=ws,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        hidden = subprocess.run(
            ["/usr/bin/python3", str(HIDDEN)],
            cwd=ws,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        return {"visiblePassed": visible.returncode == 0, "hiddenPassed": hidden.returncode == 0}


def binding(
    contract: HarnessRunContract, continuity: SQLiteHarnessRunContinuityStore
) -> HarnessExecutionBinding:
    b = continuity.binding
    return HarnessExecutionBinding(
        harness_run_id=contract.harness_run_id,
        workspace_ref="ws-live-ab",
        runtime_references=(
            {
                "namespace": "ordivon.harness",
                "type": "harness_run",
                "id": contract.harness_run_id,
                "generation": str(b.assignment_generation),
                "digest": b.digest,
            },
            {
                "namespace": "ordivon.harness",
                "type": "run_contract",
                "id": f"harness-run-contract:{contract.digest[7:31]}",
                "generation": "1",
                "digest": contract.digest,
            },
            {
                "namespace": "ordivon.harness",
                "type": "tool_grant",
                "id": f"tool-grant:{contract.tool_grant_digest[7:31]}",
                "generation": "1",
                "digest": contract.tool_grant_digest,
            },
        ),
    )


def run_one(
    codec: str, replicate: int, settings: DeepSeekSettings, *, max_total_tokens: int = 64_000
) -> dict[str, JsonValue]:
    edit_def = treatment_edit_definition(codec)
    surface = {
        "schemaVersion": 1,
        "kind": "ordivon.adaptive-edit-r2-live-treatment-surface",
        "codec": codec,
        "tools": [READ_EDITABLE_WORKSPACE_DEFINITION.to_dict(), edit_def.to_dict()],
    }
    surface_digest = canonical_digest(surface)
    grant = {
        "schemaVersion": 1,
        "kind": "ordivon.adaptive-edit-r2-live-treatment-grant",
        "codec": codec,
        "readPaths": list(READ_PATHS),
        "editPaths": ["allocation.py"],
        "runtimeOperations": ["workspace.read", "workspace.patch", "workspace.patch.get"],
    }
    grant_digest = canonical_digest(grant)
    budget = RunBudget(
        max_model_calls=6,
        max_tool_calls=8,
        max_observation_bytes=262_144,
        max_wall_time_ms=90_000,
        max_total_tokens=max_total_tokens,
        max_model_retries=1,
        max_tool_corrections=3,
        max_conclusion_corrections=2,
        max_observation_only_turns=5,
        max_no_progress_turns=4,
        max_model_observation_bytes=64_000,
    )
    objective = str(TASK["objective"])
    context = {
        "taskId": TASK["taskId"],
        "taskVersion": TASK["taskVersion"],
        "objective": objective,
        "treatmentCodec": codec,
    }
    suffix = f"{codec.replace('-', '_')}-{replicate}"
    contract = HarnessRunContract(
        harness_run_id=f"harness-run:r2-live-ab-{suffix}",
        harness_implementation_id="ordivon-harness@"
        + subprocess.check_output(
            ["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        caller_id="caller:r2-live-ab",
        caller_run_ref=f"experiment:r2-live-ab:{suffix}",
        objective_ref=HarnessBoundReference(
            f"objective:r2-live-ab-{suffix}",
            "objective",
            canonical_digest({"objective": objective}),
        ),
        context_refs=(
            HarnessBoundReference(
                f"context:r2-live-ab-{suffix}", "context", canonical_digest(context)
            ),
        ),
        provider_id="provider:deepseek",
        adapter_id=DeepSeekTurnAdapter.adapter_id,
        requested_model_id=settings.model,
        tool_catalog_digest=surface_digest,
        tool_grant_digest=grant_digest,
        budget=budget.to_contract_dict(),
        completion_contract={"mode": "record"},
        system_manifest_ref=HarnessBoundReference(
            f"system-manifest:r2-live-ab-{suffix}",
            "system-manifest",
            canonical_digest({"experiment": "adaptive-edit-r2-live-ab", "revision": 1}),
        ),
        created_at_ms=int(time.time() * 1000),
    )
    runtime = MemoryRuntime()
    initial = (
        {
            "role": "system",
            "content": f"You are in a controlled repository-repair evaluation. You may read SPEC.md, allocation.py, and test_allocation.py. You may modify only allocation.py, using edit_workspace. This treatment admits exactly one edit codec: {codec}. Use sourceDigest from the latest read_workspace result. Do not merely describe a patch: perform the edit. When the repair is complete, submit candidate_completed. No other external effects are available.",
        },
        {"role": "user", "content": objective},
    )
    with tempfile.TemporaryDirectory() as directory:
        store = SQLiteHarnessStore.initialize(Path(directory) / "state")
        store.create_run(contract)
        continuity = SQLiteHarnessRunContinuityStore(store, contract)
        bridge = TreatmentBridge(
            contract,
            continuity,
            binding(contract, continuity),
            runtime,
            treatment_codec=codec,
            tool_definitions=(READ_EDITABLE_WORKSPACE_DEFINITION, edit_def),
            tool_surface_digest=surface_digest,
            tool_grant_digest=grant_digest,
            tool_grant=TreatmentGrant(),
        )
        adapter = DeepSeekTurnAdapter(settings, completion_contract=contract.completion_contract)
        started = time.monotonic()
        try:
            result = OrdivonAgentLoop(adapter, bridge, budget=budget).run(
                harness_run_id=contract.harness_run_id,
                assignment_id=continuity.binding.assignment_id,
                context_digest=contract.context_refs[0].digest,
                initial_messages=initial,
            )
            elapsed = int((time.monotonic() - started) * 1000)
            source = runtime.files["allocation.py"]
            outcome = verify(source)
            rejected = sum(1 for o in result.observations if o.status == "rejected")
            edit_obs = [o for o in result.observations if o.tool_name == "edit_workspace"]
            record = {
                "treatment": codec,
                "replicate": replicate,
                "status": "completed",
                "stopCode": result.stop_code.value,
                "candidateCompleted": result.candidate_completed,
                "modelCalls": result.model_calls,
                "toolCalls": result.tool_calls,
                "observationBytes": result.observation_bytes,
                "elapsedMs": elapsed,
                "usage": result.usage,
                "stopDetail": next(
                    (
                        e.payload.get("detail")
                        for e in reversed(result.trace.events)
                        if e.kind == "run_stopped"
                    ),
                    None,
                ),
                "rejectedObservations": rejected,
                "editObservationStatuses": [o.status for o in edit_obs],
                "runtimeOperations": [name for name, _ in runtime.calls],
                "finalDigest": sha(source),
                "oracleExact": source == ORACLE.read_text(),
                **outcome,
            }
        except Exception as exc:
            elapsed = int((time.monotonic() - started) * 1000)
            source = runtime.files["allocation.py"]
            outcome = verify(source)
            record = {
                "treatment": codec,
                "replicate": replicate,
                "status": "exception",
                "errorType": type(exc).__name__,
                "error": str(exc)[:1000],
                "elapsedMs": elapsed,
                "runtimeOperations": [name for name, _ in runtime.calls],
                "finalDigest": sha(source),
                "oracleExact": source == ORACLE.read_text(),
                **outcome,
            }
        store.close()
        return record


def _summaries(records: list[dict[str, JsonValue]]) -> dict[str, JsonValue]:
    summaries: dict[str, JsonValue] = {}
    for codec in CODECS:
        subset = [r for r in records if r.get("treatment") == codec]
        if not subset:
            continue
        count = len(subset)
        summaries[codec] = {
            "runs": count,
            "candidateCompleted": sum(bool(r.get("candidateCompleted")) for r in subset),
            "visiblePassed": sum(bool(r.get("visiblePassed")) for r in subset),
            "hiddenPassed": sum(bool(r.get("hiddenPassed")) for r in subset),
            "meanModelCalls": sum(int(r.get("modelCalls", 0)) for r in subset) / count,
            "meanToolCalls": sum(int(r.get("toolCalls", 0)) for r in subset) / count,
            "meanTotalTokens": sum(
                int(r.get("usage", {}).get("totalTokens", 0))
                if isinstance(r.get("usage"), dict)
                else 0
                for r in subset
            )
            / count,
            "meanElapsedMs": sum(int(r.get("elapsedMs", 0)) for r in subset) / count,
            "rejectedObservations": sum(int(r.get("rejectedObservations", 0)) for r in subset),
        }
    return summaries


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a small live DeepSeek A/B over the internal Adaptive Edit ACI."
    )
    parser.add_argument("--start-replicate", type=int, default=1)
    parser.add_argument("--replicates", type=int, default=1)
    parser.add_argument("--max-total-tokens", type=int, default=64_000)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--treatment",
        choices=("both", *CODECS),
        default="both",
    )
    args = parser.parse_args()
    if args.start_replicate < 1 or args.replicates < 1 or args.max_total_tokens < 1:
        parser.error("replicate indexes/counts and max-total-tokens must be positive")

    settings = DeepSeekSettings.from_secret_file(
        timeout_seconds=30.0,
        max_response_bytes=2_097_152,
        max_output_tokens=2048,
    )
    treatments = CODECS if args.treatment == "both" else (args.treatment,)
    records: list[dict[str, JsonValue]] = []
    for codec in treatments:
        for replicate in range(
            args.start_replicate,
            args.start_replicate + args.replicates,
        ):
            record = run_one(
                codec,
                replicate,
                settings,
                max_total_tokens=args.max_total_tokens,
            )
            records.append(record)
            progress = {
                key: record.get(key)
                for key in (
                    "treatment",
                    "replicate",
                    "stopCode",
                    "candidateCompleted",
                    "modelCalls",
                    "toolCalls",
                    "elapsedMs",
                    "visiblePassed",
                    "hiddenPassed",
                    "rejectedObservations",
                    "finalDigest",
                )
            }
            print(
                json.dumps({"progress": progress}, ensure_ascii=False, sort_keys=True), flush=True
            )

    report: dict[str, JsonValue] = {
        "schemaVersion": 1,
        "kind": "ordivon.adaptive-edit-r2-live-ab",
        "date": "2026-09-14",
        "taskId": TASK["taskId"],
        "provider": "deepseek",
        "requestedModel": settings.model,
        "startReplicate": args.start_replicate,
        "replicatesPerTreatment": args.replicates,
        "maxTotalTokens": args.max_total_tokens,
        "treatments": list(treatments),
        "scope": (
            "Small live Provider A/B over one repository-repair task. Provisional, "
            "model/task-specific evidence only; not a general codec or model ranking. "
            "Physical workspace is an isolated in-memory Runtime-shaped fixture; durable "
            "real Runtime Patch/recovery is validated separately."
        ),
        "records": records,
        "summaries": _summaries(records),
    }
    report["reportDigest"] = canonical_digest(report)
    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(
        "FINAL_SUMMARY="
        + json.dumps(
            {
                "reportDigest": report["reportDigest"],
                "summaries": report["summaries"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
