#!/usr/bin/env python3
"""Browserless-backed Agent Automation carrier adapter.

This is intentionally thin. Browserless owns browser lifecycle, queueing, concurrency and health;
Temporal is expected to own durable workflow lifecycle. This adapter retains only provider binding
and the external non-idempotent effect fence that neither substrate can infer for ChatGPT Web.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sqlite3
import subprocess
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]

try:
    from browserless_substrate import BrowserlessPool
    from campaign_birth import (
        CampaignLaunchSpec,
        campaign_census,
        compile_campaign,
    )
    from sqlite_conversation_materializer import SQLiteConversationMaterializer
    from standard_identifiers import require_uuid7
    from browserless_human_handoff import load_verified_handoff
except ModuleNotFoundError:
    from scripts.browserless_substrate import BrowserlessPool
    from scripts.campaign_birth import (
        CampaignLaunchSpec,
        campaign_census,
        compile_campaign,
    )
    from scripts.sqlite_conversation_materializer import SQLiteConversationMaterializer
    from scripts.standard_identifiers import require_uuid7
    from scripts.browserless_human_handoff import load_verified_handoff


def _abs(value: str | Path) -> Path:
    return Path(os.path.abspath(os.fspath(value)))


def _read_json(path: Path) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("expected JSON object")
    return value


def _suffix(value: str, length: int = 24) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:length]


def _write_private(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    os.chmod(path, 0o600)


def _continuation_prompt(value: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("continuation prompt must be non-empty and trimmed")
    if len(value.encode("utf-8")) > 32768:
        raise ValueError("continuation prompt exceeds 32768 UTF-8 bytes")
    return value


def _prompt_file_text(path: Path) -> str:
    value = Path(path).read_text(encoding="utf-8")
    if value.endswith("\r\n"):
        return value[:-2]
    if value.endswith("\n"):
        return value[:-1]
    return value


@dataclass(frozen=True, slots=True)
class BrowserlessAutomationConfig:
    state_root: Path
    browserless_pool: BrowserlessPool
    playwright_python: Path
    submit_script: Path
    reconcile_script: Path
    turn_script: Path
    preflight_script: Path
    human_resume_script: Path
    temporal_python: Path = Path(
        "/root/.local/share/ordivon-workstation/temporal-agent-automation/.venv/bin/python"
    )
    temporal_launch_script: Path = SOURCE_ROOT / "scripts/temporal_agent_automation_launch.py"
    temporal_address: str = "127.0.0.1:17233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "ordivon-agent-automation"
    wait_stable_seconds: int = 150
    reconnect_ms: int = 60000
    human_handoff_ms: int = 60000
    human_handoff_mode: str = "self-hosted-vnc"
    browser_session_timeout_ms: int = 480000

    def __post_init__(self) -> None:
        if self.human_handoff_mode not in {"self-hosted-vnc", "live-url"}:
            raise ValueError("browserlessHumanHandoffMode must be self-hosted-vnc or live-url")
        if self.human_handoff_ms <= 0:
            raise ValueError("browserlessHumanHandoffMs must be positive")
        required_session_budget = (
            self.human_handoff_ms + max(30000, self.wait_stable_seconds * 1000) + 30000
        )
        if self.browser_session_timeout_ms < required_session_budget:
            raise ValueError(
                "browserlessSessionTimeoutMs must cover human handoff + post-verification stabilization + margin"
            )

    @classmethod
    def from_dict(cls, value: dict) -> "BrowserlessAutomationConfig":
        if value.get("schemaVersion") != 1:
            raise ValueError("schemaVersion=1 required")
        return cls(
            state_root=_abs(value["stateRoot"]),
            browserless_pool=BrowserlessPool.from_dict(value["browserSubstrate"]),
            playwright_python=_abs(value["playwrightPython"]),
            submit_script=_abs(value["browserlessSubmitScript"]),
            reconcile_script=_abs(value["browserlessReconcileScript"]),
            turn_script=_abs(value["browserlessTurnScript"]),
            preflight_script=_abs(value["browserlessPreflightScript"]),
            human_resume_script=_abs(
                value.get(
                    "browserlessHumanResumeScript",
                    str(SOURCE_ROOT / "scripts/playwright_browserless_human_resume.py"),
                )
            ),
            temporal_python=_abs(
                value.get(
                    "temporalPython",
                    "/root/.local/share/ordivon-workstation/temporal-agent-automation/.venv/bin/python",
                )
            ),
            temporal_launch_script=_abs(
                value.get(
                    "temporalLaunchScript",
                    str(SOURCE_ROOT / "scripts/temporal_agent_automation_launch.py"),
                )
            ),
            temporal_address=str(value.get("temporalAddress", "127.0.0.1:17233")),
            temporal_namespace=str(value.get("temporalNamespace", "default")),
            temporal_task_queue=str(value.get("temporalTaskQueue", "ordivon-agent-automation")),
            wait_stable_seconds=int(value.get("waitStableSeconds", 150)),
            reconnect_ms=int(value.get("browserlessReconnectMs", 60000)),
            human_handoff_ms=int(
                value.get("browserlessHumanHandoffMs", value.get("browserlessReconnectMs", 60000))
            ),
            human_handoff_mode=str(value.get("browserlessHumanHandoffMode", "self-hosted-vnc")),
            browser_session_timeout_ms=int(value.get("browserlessSessionTimeoutMs", 480000)),
        )

    @property
    def ledger(self) -> Path:
        return self.state_root / "birth-ledger.sqlite"

    @property
    def turn_ledger(self) -> Path:
        return self.state_root / "turn-ledger.sqlite"


class BrowserlessAutomationHold(RuntimeError):
    pass


class BrowserlessAutomationConflict(RuntimeError):
    pass


class BrowserlessCarrierIdentityStale(BrowserlessAutomationConflict):
    pass


class BrowserlessAutomationAmbiguous(RuntimeError):
    pass


class BrowserlessCarrierBusy(RuntimeError):
    pass


# Only carrier/transport-local pre-SEND unavailability may rotate to another profile. Provider
# policy, authentication, challenge and ambiguous UI states remain on the selected carrier.
PRE_SEND_CARRIER_FAILOVER_STANDINGS = frozenset(
    {
        "SUBSTRATE_UNAVAILABLE",
        "CARRIER_BUSY",
        "PROVIDER_UNAVAILABLE",
        "CONNECT_FAILED",
    }
)


@contextmanager
def _carrier_lease(config: BrowserlessAutomationConfig, endpoint_id: str, *, blocking: bool):
    """Serialize every interactive use of one persistent Browserless profile across processes.

    Temporal already serializes activities in-process; this filesystem lease closes the remaining
    gap with CLI/MCP diagnostics, which otherwise can open the same userDataDir concurrently.
    """
    lock_root = config.state_root / "carrier-leases"
    lock_root.mkdir(parents=True, exist_ok=True)
    path = lock_root / f"{_suffix(endpoint_id, 32)}.lock"
    with path.open("a+") as handle:
        operation = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
        try:
            fcntl.flock(handle.fileno(), operation)
        except BlockingIOError as error:
            raise BrowserlessCarrierBusy(f"Browserless carrier busy: {endpoint_id}") from error
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class BrowserlessAutomationService:
    def __init__(self, config: BrowserlessAutomationConfig) -> None:
        self.config = config
        self.config.state_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def load_spec(path: Path) -> CampaignLaunchSpec:
        return CampaignLaunchSpec.from_dict(_read_json(path))

    def _birth(self, spec: CampaignLaunchSpec, agent_id: str):
        rows = [b for b in compile_campaign(spec) if b.agent_id == agent_id]
        if len(rows) != 1:
            raise BrowserlessAutomationConflict("agentId does not identify exactly one occurrence")
        return rows[0]

    def _occurrence_dir(self, birth) -> Path:
        return self.config.state_root / "occurrences" / _suffix(birth.effect_id)

    def _binding_path(self, birth) -> Path:
        return self._occurrence_dir(birth) / "carrier-binding.json"

    def _endpoint_by_id(self, endpoint_id: str):
        rows = [e for e in self.config.browserless_pool.endpoints if e.endpoint_id == endpoint_id]
        if len(rows) != 1:
            raise BrowserlessAutomationConflict("Browserless endpoint binding changed")
        return rows[0]

    def _validate_binding(self, birth, row: dict) -> dict:
        if set(row) != {"effectId", "endpointId", "endpointIdentityDigest"}:
            raise BrowserlessAutomationConflict("carrier binding record has unexpected fields")
        if row.get("effectId") != birth.effect_id:
            raise BrowserlessAutomationConflict(
                "carrier binding belongs to another provider effect"
            )
        try:
            endpoint = self._endpoint_by_id(row["endpointId"])
        except BrowserlessAutomationConflict as error:
            raise BrowserlessCarrierIdentityStale("Browserless endpoint binding changed") from error
        if endpoint.identity_digest != row["endpointIdentityDigest"]:
            raise BrowserlessCarrierIdentityStale("Browserless endpoint identity changed")
        return row

    def _current_binding(self, birth) -> dict | None:
        current = self._binding_path(birth)
        if not current.is_file():
            return None
        return self._validate_binding(birth, _read_json(current))

    def _reconciliation_binding(self, birth) -> tuple[dict | None, str | None]:
        """Return only a carrier that is still the same physical Browserless identity.

        Reconciliation is observational: a restarted/removed carrier cannot prove anything about
        the old SEND boundary, but that loss of observation authority is not an integrity failure
        and never authorizes rerouting or resend. Corrupt/cross-effect binding bytes still fail hard.
        """
        try:
            return self._current_binding(birth), None
        except BrowserlessCarrierIdentityStale:
            return None, "carrier-no-longer-current"

    def _human_handoff_liveness(self, handoff: dict) -> str:
        """Return CURRENT, EXPIRED_PRESENT, INACTIVE, or UNKNOWN.

        Persisted handoff state is historical evidence, not current Browserless truth. A failed
        liveness observation must never be interpreted as permission to create another session.
        """
        if handoff.get("sessionActive") is not True:
            return "INACTIVE"
        mode = handoff.get("mode")
        until = handoff.get("sessionActiveUntilMs")
        deadline_current = (
            isinstance(until, int)
            and not isinstance(until, bool)
            and until > int(time.time() * 1000)
        )
        if mode == "live-url":
            return "CURRENT" if deadline_current else "INACTIVE"
        if mode == "self-hosted-vnc":
            instance = handoff.get("transportInstance")
            if not isinstance(instance, int) or isinstance(instance, bool):
                return "UNKNOWN"
            try:
                from browserless_human_interaction import observe as observe_human_transport

                transport = observe_human_transport(instance)
            except Exception:
                return "UNKNOWN"
            if transport.get("standing") != "READY":
                return "INACTIVE"
            return "CURRENT" if deadline_current else "EXPIRED_PRESENT"
        return "UNKNOWN"

    def census(self, spec_path: Path) -> dict:
        spec = self.load_spec(spec_path)
        result = campaign_census(spec, self.config.ledger)
        by_agent = {birth.agent_id: birth for birth in compile_campaign(spec)}
        active = 0
        for row in result.get("occurrences", []):
            birth = by_agent.get(row.get("agentId"))
            if birth is None:
                continue
            path = (
                self._occurrence_dir(birth) / "human-handoff" / f"{_suffix(birth.effect_id)}.json"
            )
            if not path.is_file():
                continue
            try:
                handoff = load_verified_handoff(path)
            except Exception:
                continue
            available = (
                handoff.get("effectId") == birth.effect_id
                and handoff.get("providerEffectAttempted") is False
                and self._human_handoff_liveness(handoff) == "CURRENT"
                and row.get("materializationStanding") in {"unknown", "human-required"}
            )
            if available:
                row["humanHandoffAvailable"] = True
                row["humanHandoffMode"] = handoff.get("mode")
                active += 1
        result["activeHumanHandoffs"] = active
        return result

    def _require_provider_ready(self, endpoint_id: str) -> dict:
        observation = self.provider_preflight(endpoint_id)
        standing = observation.get("standing")
        if standing != "READY":
            raise BrowserlessAutomationHold(
                f"provider admission HOLD on {endpoint_id}: {standing or 'UNRESOLVED'}; no new provider-effect workflow admitted"
            )
        return observation

    def _require_birth_substrate_available(
        self, birth, *, observations: dict[str, dict] | None = None
    ):
        # Public admission observes only physical Browserless reachability. Provider/UI admission
        # belongs to the Temporal worker while it owns the exact persistent-profile carrier lease.
        observed = observations if observations is not None else {}
        rejected: list[str] = []
        for endpoint in self.config.browserless_pool.candidates(birth.effect_id):
            health = observed.get(endpoint.endpoint_id)
            if health is None:
                health = endpoint.health(timeout_seconds=5)
                observed[endpoint.endpoint_id] = health
            if health.get("healthy"):
                return endpoint
            rejected.append(
                f"{endpoint.endpoint_id}={health.get('detail') or health.get('status') or 'UNHEALTHY'}"
            )
        raise BrowserlessAutomationHold(
            "provider birth substrate HOLD: no healthy carrier before Temporal admission; "
            + ", ".join(rejected)
        )

    def _gate_unrecorded_births(self, spec: CampaignLaunchSpec) -> dict:
        census = campaign_census(spec, self.config.ledger)
        by_agent = {row["agentId"]: row for row in census["occurrences"]}
        observations: dict[str, dict] = {}
        for birth in compile_campaign(spec):
            row = by_agent[birth.agent_id]
            # Campaign launch is roster admission, not recovery. A PRE_EFFECT_FAILED occurrence
            # already has one durable Birth workflow/effect identity and must require an explicit
            # occurrence-level re-entry; otherwise exact campaign replay would create fresh retries.
            if row.get("materializationStanding") is not None:
                continue
            self._require_birth_substrate_available(birth, observations=observations)
        return census

    def _temporal_admit(
        self,
        spec_path: Path,
        operation: str,
        *,
        agent_id: str | None = None,
        prompt: str | None = None,
        turn_request_id: str | None = None,
        resume_id: str | None = None,
    ) -> dict:
        # Temporal workflow history must never retain an invocation-local path (notably /tmp).
        # The worker runs with PrivateTmp=true, while the Campaign registry is deliberately under
        # the service's durable stateRoot and is digest-verified on every resolve. Current specs are
        # registered idempotently here so every entry path—CLI, MCP, or controller—gets the same
        # durable input boundary before workflow admission.
        source_spec = _abs(spec_path)
        raw_spec = _read_json(source_spec)
        CampaignLaunchSpec.from_dict(raw_spec)
        # Registry/JCS validation belongs to admission, not provider-effect execution. Keep the
        # Temporal worker runtime lean: it only needs temporalio plus the already-frozen spec.
        try:
            from agent_automation_registry import CampaignRegistry
        except ModuleNotFoundError as error:
            if error.name != "agent_automation_registry":
                raise
            from scripts.agent_automation_registry import CampaignRegistry
        registry = CampaignRegistry(self.config.state_root)
        registration = registry.register(raw_spec)
        temporal_spec_path = registry.resolve(registration["campaignRef"])

        prompt_dir: tempfile.TemporaryDirectory[str] | None = None
        prompt_file: Path | None = None
        try:
            if prompt is not None:
                prompt = _continuation_prompt(prompt)
                prompt_dir = tempfile.TemporaryDirectory(prefix="ordivon-temporal-prompt-")
                prompt_file = Path(prompt_dir.name) / "prompt.txt"
                prompt_file.write_text(prompt, encoding="utf-8")
                os.chmod(prompt_file, 0o600)
            cmd = [
                str(self.config.temporal_python),
                str(self.config.temporal_launch_script),
                "--spec",
                str(temporal_spec_path),
                "--operation",
                operation,
                "--address",
                self.config.temporal_address,
                "--namespace",
                self.config.temporal_namespace,
                "--task-queue",
                self.config.temporal_task_queue,
            ]
            if agent_id is not None:
                cmd += ["--agent-id", agent_id]
            if prompt_file is not None:
                cmd += ["--prompt-file", str(prompt_file)]
            if turn_request_id is not None:
                cmd += ["--turn-request-id", turn_request_id]
            if resume_id is not None:
                cmd += ["--resume-id", resume_id]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
        finally:
            if prompt_dir is not None:
                prompt_dir.cleanup()
        if proc.returncode != 0:
            detail = (proc.stderr or "").strip().replace("\n", " ")[-800:]
            suffix = f"; detail={detail}" if detail else ""
            raise BrowserlessAutomationAmbiguous(
                f"Temporal admission outcome is unknown (rc={proc.returncode}{suffix}); observe the same identity before any retry"
            )
        try:
            row = json.loads(proc.stdout.strip().splitlines()[-1])
        except Exception as error:
            raise BrowserlessAutomationAmbiguous(
                "Temporal admission outcome is unknown because no machine-readable receipt was returned; observe the same identity before any retry"
            ) from error
        if operation == "campaign-birth":
            workflows = row.get("workflows")
            if (
                row.get("kind") != "temporal-birth-admissions"
                or not isinstance(workflows, list)
                or not workflows
            ):
                raise BrowserlessAutomationAmbiguous(
                    "Temporal campaign admission outcome is unknown because the receipt is malformed; observe the same birth identities before any retry"
                )
            for admitted in workflows:
                if (
                    not isinstance(admitted, dict)
                    or admitted.get("disposition") not in {"admitted", "started", "existing"}
                    or not admitted.get("workflowId")
                    or not admitted.get("effectId")
                ):
                    raise BrowserlessAutomationAmbiguous(
                        "Temporal campaign admission outcome is unknown because one workflow receipt is malformed; observe the same birth identities before any retry"
                    )
        elif row.get("disposition") not in {"admitted", "started", "existing"} or not row.get(
            "workflowId"
        ):
            raise BrowserlessAutomationAmbiguous(
                "Temporal admission outcome is unknown because the receipt is malformed; observe the same identity before any retry"
            )
        return row

    def launch_campaign(self, spec_path: Path) -> dict:
        spec = self.load_spec(spec_path)
        self._gate_unrecorded_births(spec)
        temporal = self._temporal_admit(spec_path, "campaign-birth")
        return {
            "schemaVersion": 1,
            "kind": "ordivon.temporal-campaign-admission",
            "campaignId": spec.campaign_id,
            # Exact campaign replay never creates a fresh PRE_EFFECT retry identity. Explicit
            # occurrence.birth is the recovery surface for one proven PRE_EFFECT_FAILED effect.
            "temporal": temporal,
            "preEffectRetries": [],
            "census": campaign_census(spec, self.config.ledger),
        }

    def launch_occurrence(self, spec_path: Path, agent_id: str) -> dict:
        spec = self.load_spec(spec_path)
        birth = self._birth(spec, agent_id)
        census = campaign_census(spec, self.config.ledger)
        row = next(r for r in census["occurrences"] if r["agentId"] == agent_id)
        standing = row.get("materializationStanding")
        if standing in {None, "pre-effect-failed"}:
            self._require_birth_substrate_available(birth)
        operation = "pre-effect-retry" if standing == "pre-effect-failed" else "agent-birth"
        temporal = self._temporal_admit(spec_path, operation, agent_id=agent_id)
        return {
            "schemaVersion": 1,
            "kind": "ordivon.temporal-occurrence-birth-admission",
            "agentId": agent_id,
            "effectId": birth.effect_id,
            "temporal": temporal,
            "census": campaign_census(spec, self.config.ledger),
        }

    def launch_reconcile(self, spec_path: Path, agent_id: str) -> dict:
        spec = self.load_spec(spec_path)
        birth = self._birth(spec, agent_id)
        census = campaign_census(spec, self.config.ledger)
        row = next(r for r in census["occurrences"] if r["agentId"] == agent_id)
        if row.get("materializationStanding") not in {"unknown", "submit-observed"}:
            raise BrowserlessAutomationHold(
                "only an occurrence with unknown provider-effect outcome may be reconciled"
            )
        temporal = self._temporal_admit(spec_path, "reconcile", agent_id=agent_id)
        result = {
            "schemaVersion": 1,
            "kind": "ordivon.temporal-occurrence-reconcile-admission",
            "agentId": agent_id,
            "temporal": temporal,
            "safeToResend": False,
            "census": census,
        }
        result["effectId"] = birth.effect_id
        return result

    def human_handoff_info(self, spec_path: Path, agent_id: str) -> dict:
        spec = self.load_spec(spec_path)
        birth = self._birth(spec, agent_id)
        census = campaign_census(spec, self.config.ledger)
        row = next(r for r in census["occurrences"] if r["agentId"] == agent_id)
        # While a self-hosted VNC handoff is actively attached, the effect ledger may remain UNKNOWN
        # because the effect attempt was durably claimed before target execution. The private handoff
        # receipt independently proves providerEffectAttempted=false during that bounded window.
        if row.get("materializationStanding") not in {"human-required", "unknown"}:
            raise BrowserlessAutomationHold(
                "occurrence is not waiting for human provider verification"
            )
        path = self._occurrence_dir(birth) / "human-handoff" / f"{_suffix(birth.effect_id)}.json"
        if not path.is_file():
            raise BrowserlessAutomationHold("human verification handoff receipt is unavailable")
        value = load_verified_handoff(path)
        if (
            value.get("effectId") != birth.effect_id
            or value.get("providerEffectAttempted") is not False
        ):
            raise BrowserlessAutomationConflict("human handoff identity/effect proof mismatch")
        liveness = self._human_handoff_liveness(value)
        if liveness != "CURRENT":
            raise BrowserlessAutomationHold(
                f"human verification handoff is not currently usable: {liveness}; resume only after current-session absence is proven"
            )
        mode = value.get("mode")
        self._endpoint_by_id(value.get("browserlessEndpointId"))
        handoff_url = (
            value.get("operatorURL") if mode == "self-hosted-vnc" else value.get("liveURL")
        )
        if not isinstance(handoff_url, str) or not handoff_url:
            raise BrowserlessAutomationHold("human verification interactive URL is unavailable")
        return {
            "schemaVersion": 1,
            "kind": "ordivon.provider-human-verification-handoff",
            "agentId": agent_id,
            "effectId": birth.effect_id,
            "standing": "HUMAN_REQUIRED",
            "ledgerStanding": row.get("materializationStanding"),
            "mode": mode,
            "blocker": value.get("blocker"),
            "handoffURL": handoff_url,
            "sessionActive": value.get("sessionActive"),
            "sessionActiveUntilMs": value.get("sessionActiveUntilMs"),
            "handoffDigest": value.get("handoffDigest"),
            "providerEffectAttempted": False,
        }

    def launch_human_resume(self, spec_path: Path, agent_id: str) -> dict:
        spec = self.load_spec(spec_path)
        birth = self._birth(spec, agent_id)
        census = campaign_census(spec, self.config.ledger)
        row = next(r for r in census["occurrences"] if r["agentId"] == agent_id)
        if row.get("materializationStanding") != "human-required":
            raise BrowserlessAutomationHold(
                "only a HUMAN_REQUIRED occurrence may resume after human verification"
            )
        handoff_path = (
            self._occurrence_dir(birth) / "human-handoff" / f"{_suffix(birth.effect_id)}.json"
        )
        if not handoff_path.is_file():
            raise BrowserlessAutomationHold(
                "HUMAN_REQUIRED occurrence has no private handoff receipt"
            )
        handoff = load_verified_handoff(handoff_path)
        liveness = self._human_handoff_liveness(handoff)
        if handoff.get("mode") == "self-hosted-vnc" and liveness != "INACTIVE":
            raise BrowserlessAutomationHold(
                f"self-hosted human resume requires proven current-session absence; observed {liveness}"
            )
        resume_id = handoff.get("handoffDigest")
        if not isinstance(resume_id, str) or not resume_id.startswith("sha256:"):
            raise BrowserlessAutomationConflict("human handoff lacks stable resume identity")
        temporal = self._temporal_admit(
            spec_path, "human-resume", agent_id=agent_id, resume_id=resume_id
        )
        return {
            "schemaVersion": 1,
            "kind": "ordivon.temporal-human-verification-resume-admission",
            "agentId": agent_id,
            "effectId": birth.effect_id,
            "temporal": temporal,
            "census": census,
        }

    def _turn_effect_row(self, turn_request_id: str) -> dict | None:
        path = self.config.turn_ledger
        if not path.exists():
            return None
        try:
            with sqlite3.connect(path) as db:
                row = db.execute(
                    "SELECT prompt_digest,target_coordinate,state,receipt_json,updated_at_ms FROM turn_effects WHERE turn_request_id=?",
                    (turn_request_id,),
                ).fetchone()
        except sqlite3.OperationalError as error:
            if "no such table" in str(error).lower():
                return None
            raise
        if row is None:
            return None
        return {
            "promptDigest": row[0],
            "targetCoordinate": row[1],
            "state": row[2],
            "receipt": json.loads(row[3]) if row[3] else None,
            "updatedAtMs": row[4],
        }

    def launch_continue(
        self, spec_path: Path, agent_id: str, *, prompt: str, turn_request_id: str
    ) -> dict:
        spec = self.load_spec(spec_path)
        birth = self._birth(spec, agent_id)
        try:
            turn_request_id = require_uuid7(turn_request_id, "turnRequestId")
        except ValueError as error:
            raise BrowserlessAutomationConflict(str(error)) from error
        prompt = _continuation_prompt(prompt)
        census = campaign_census(spec, self.config.ledger)
        row = next(r for r in census["occurrences"] if r["agentId"] == agent_id)
        if row.get("materializationStanding") != "bound" or not row.get("providerResource"):
            raise BrowserlessAutomationHold("occurrence is not provider-bound")
        binding = self._current_binding(birth)
        if binding is None:
            raise BrowserlessAutomationHold(
                "provider-bound occurrence has no current carrier binding"
            )
        endpoint = self._endpoint_by_id(binding["endpointId"])
        ledger_before = self._turn_effect_row(turn_request_id)
        # A claimed turn is never re-sent. Temporal replay remains useful for recovering the
        # original workflow identity, and provider readiness is irrelevant once the effect fence
        # exists.
        if ledger_before is not None:
            temporal = self._temporal_admit(
                spec_path,
                "continue",
                agent_id=agent_id,
                prompt=prompt,
                turn_request_id=turn_request_id,
            )
            return {
                "schemaVersion": 1,
                "kind": "ordivon.temporal-occurrence-continue-admission",
                "agentId": agent_id,
                "turnRequestId": turn_request_id,
                "temporal": temporal,
                "turnLedgerStanding": ledger_before["state"],
                "retryAdmitted": False,
                "census": census,
            }

        self._require_provider_ready(endpoint.endpoint_id)
        temporal = self._temporal_admit(
            spec_path, "continue", agent_id=agent_id, prompt=prompt, turn_request_id=turn_request_id
        )
        retry_admitted = False
        if (
            temporal.get("disposition") == "existing"
            and self._turn_effect_row(turn_request_id) is None
        ):
            retry = self._temporal_admit(
                spec_path,
                "continue-retry",
                agent_id=agent_id,
                prompt=prompt,
                turn_request_id=turn_request_id,
            )
            if retry.get("retryStanding") != "admitted-after-failed":
                raise BrowserlessAutomationHold(
                    f"continuation retry not admitted: {retry.get('retryStanding') or 'prior workflow is not proven failed'}"
                )
            temporal = retry
            retry_admitted = True
        return {
            "schemaVersion": 1,
            "kind": "ordivon.temporal-occurrence-continue-admission",
            "agentId": agent_id,
            "turnRequestId": turn_request_id,
            "temporal": temporal,
            "turnLedgerStanding": None,
            "retryAdmitted": retry_admitted,
            "census": census,
        }

    def _provider_preflight_under_carrier_lease(self, endpoint_id: str) -> dict:
        """Read provider state while the caller already owns this endpoint's carrier lease.

        This helper deliberately does not reacquire ``_carrier_lease``: Linux flock on a separately
        opened fd can conflict with the caller's own exclusive lock. The worker uses this helper
        inside the same lease that remains held through exact endpoint binding and SEND.
        """
        endpoint = self._endpoint_by_id(endpoint_id)
        substrate = endpoint.health(timeout_seconds=5)
        if not substrate.get("healthy"):
            return {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-provider-preflight",
                "endpointId": endpoint.endpoint_id,
                "standing": "SUBSTRATE_UNAVAILABLE",
                "providerEffectAttempted": False,
                "clicked": False,
                "composerFilled": False,
                "sendAttempted": False,
                "assistantOutputRead": False,
                "substrateHealth": substrate,
            }
        # A session can predate the current Ordivon lease contract or come from a non-cooperating
        # client. The filesystem lease alone therefore does not prove exclusive Browserless use.
        if endpoint.sessions(timeout_seconds=3):
            return {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-provider-preflight",
                "endpointId": endpoint.endpoint_id,
                "standing": "CARRIER_BUSY",
                "providerEffectAttempted": False,
                "clicked": False,
                "composerFilled": False,
                "sendAttempted": False,
                "assistantOutputRead": False,
                "substrateHealth": substrate,
            }
        cmd = [
            *endpoint.exec_prefix,
            str(self.config.playwright_python),
            str(self.config.preflight_script),
            "--browserless-endpoint",
            endpoint.public_connection_endpoint,
            "--browserless-token-file",
            str(endpoint.token_file),
            "--endpoint-id",
            endpoint.endpoint_id,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45, check=False)
        if proc.returncode != 0:
            raise BrowserlessAutomationHold(
                f"Browserless provider preflight failed closed (rc={proc.returncode})"
            )
        try:
            row = json.loads(proc.stdout.strip().splitlines()[-1])
        except Exception as error:
            raise BrowserlessAutomationConflict(
                "Browserless provider preflight returned no observation"
            ) from error
        if row.get("endpointId") != endpoint.endpoint_id:
            raise BrowserlessAutomationConflict(
                "Browserless provider preflight endpoint identity mismatch"
            )
        for key in (
            "providerEffectAttempted",
            "clicked",
            "composerFilled",
            "sendAttempted",
            "assistantOutputRead",
        ):
            if row.get(key) is not False:
                raise BrowserlessAutomationConflict(
                    f"Browserless provider preflight violated read-only contract: {key}"
                )
        row["substrateHealth"] = substrate
        return row

    def provider_preflight(self, endpoint_id: str) -> dict:
        endpoint = self._endpoint_by_id(endpoint_id)
        # Public diagnostics are second clients unless they can acquire the carrier nonblockingly.
        try:
            with _carrier_lease(self.config, endpoint.endpoint_id, blocking=False):
                return self._provider_preflight_under_carrier_lease(endpoint.endpoint_id)
        except BrowserlessCarrierBusy:
            substrate = endpoint.health(timeout_seconds=5)
            return {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-provider-preflight",
                "endpointId": endpoint.endpoint_id,
                "standing": "CARRIER_BUSY",
                "providerEffectAttempted": False,
                "clicked": False,
                "composerFilled": False,
                "sendAttempted": False,
                "assistantOutputRead": False,
                "substrateHealth": substrate,
            }

    def doctor(self) -> dict:
        health = self.config.browserless_pool.health()

        class Noop:
            def materialize(self, request):
                raise AssertionError

            def reconcile(self, request):
                raise AssertionError

        ledger = SQLiteConversationMaterializer(self.config.ledger, Noop()).doctor()
        return {
            "schemaVersion": 1,
            "kind": "ordivon.browserless-agent-automation-doctor",
            "healthy": health["healthy"] and ledger["healthy"],
            "browserSubstrate": health,
            "ledger": ledger,
        }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, required=True)
    sub = p.add_subparsers(dest="action", required=True)
    for n in ("census", "launch"):
        s = sub.add_parser(n)
        s.add_argument("--spec", type=Path, required=True)
    for n in ("birth", "reconcile", "human-handoff", "human-resume"):
        s = sub.add_parser(n)
        s.add_argument("--spec", type=Path, required=True)
        s.add_argument("--agent-id", required=True)
    s = sub.add_parser("continue")
    s.add_argument("--spec", type=Path, required=True)
    s.add_argument("--agent-id", required=True)
    s.add_argument("--prompt-file", type=Path, required=True)
    s.add_argument("--turn-request-id", required=True)
    s = sub.add_parser("provider-preflight")
    s.add_argument("--endpoint-id", required=True)
    sub.add_parser("doctor")
    return p


def main() -> int:
    a = parser().parse_args()
    svc = BrowserlessAutomationService(BrowserlessAutomationConfig.from_dict(_read_json(a.config)))
    if a.action == "census":
        r = svc.census(a.spec)
    elif a.action == "launch":
        r = svc.launch_campaign(a.spec)
    elif a.action == "birth":
        r = svc.launch_occurrence(a.spec, a.agent_id)
    elif a.action == "reconcile":
        r = svc.launch_reconcile(a.spec, a.agent_id)
    elif a.action == "human-handoff":
        r = svc.human_handoff_info(a.spec, a.agent_id)
    elif a.action == "human-resume":
        r = svc.launch_human_resume(a.spec, a.agent_id)
    elif a.action == "continue":
        r = svc.launch_continue(
            a.spec,
            a.agent_id,
            prompt=_prompt_file_text(a.prompt_file),
            turn_request_id=a.turn_request_id,
        )
    elif a.action == "provider-preflight":
        r = svc.provider_preflight(a.endpoint_id)
    else:
        r = svc.doctor()
    print(json.dumps(r, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
