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
    from campaign_materialization import (
        CampaignLaunchSpec,
        campaign_census,
        compile_campaign,
    )
    from sqlite_conversation_materializer import SQLiteConversationMaterializer
    from standard_identifiers import require_uuid7
    from browserless_human_handoff import load_verified_handoff
    from provider_boundary_diagnosis import (
        CARRIER_FAILOVER_STANDINGS,
        diagnose_provider_preflight,
        provider_boundary_policy,
    )
except ModuleNotFoundError:
    from scripts.browserless_substrate import BrowserlessPool
    from scripts.campaign_materialization import (
        CampaignLaunchSpec,
        campaign_census,
        compile_campaign,
    )
    from scripts.sqlite_conversation_materializer import SQLiteConversationMaterializer
    from scripts.standard_identifiers import require_uuid7
    from scripts.browserless_human_handoff import load_verified_handoff
    from scripts.provider_boundary_diagnosis import (
        CARRIER_FAILOVER_STANDINGS,
        diagnose_provider_preflight,
        provider_boundary_policy,
    )


PRE_SEND_CARRIER_FAILOVER_STANDINGS = CARRIER_FAILOVER_STANDINGS


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
    browserless_start_timeout_seconds: int = 20
    browserless_idle_ttl_seconds: int = 900
    browserless_warm_endpoint_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.human_handoff_mode not in {"self-hosted-vnc", "live-url"}:
            raise ValueError("browserlessHumanHandoffMode must be self-hosted-vnc or live-url")
        if self.human_handoff_ms <= 0:
            raise ValueError("browserlessHumanHandoffMs must be positive")
        required_session_budget = (
            self.human_handoff_ms + max(30000, self.wait_stable_seconds * 1000) + 30000
        )
        if self.browserless_start_timeout_seconds <= 0:
            raise ValueError("browserlessStartTimeoutSeconds must be positive")
        if self.browserless_idle_ttl_seconds <= 0:
            raise ValueError("browserlessIdleTtlSeconds must be positive")
        if len(set(self.browserless_warm_endpoint_ids)) != len(self.browserless_warm_endpoint_ids):
            raise ValueError("browserlessWarmEndpointIds must be unique")
        endpoint_ids = {endpoint.endpoint_id for endpoint in self.browserless_pool.endpoints}
        if set(self.browserless_warm_endpoint_ids) - endpoint_ids:
            raise ValueError("browserlessWarmEndpointIds contains unknown endpoint")
        if self.browser_session_timeout_ms < required_session_budget:
            raise ValueError(
                "browserlessSessionTimeoutMs must cover human handoff + post-verification stabilization + margin"
            )

    @classmethod
    def from_dict(cls, value: dict) -> "BrowserlessAutomationConfig":
        if value.get("schemaVersion") != 1:
            raise ValueError("schemaVersion=1 required")
        warm = value.get("browserlessWarmEndpointIds", [])
        if not isinstance(warm, list) or any(
            not isinstance(item, str) or not item for item in warm
        ):
            raise ValueError("browserlessWarmEndpointIds must be a list of non-empty strings")
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
            browserless_start_timeout_seconds=int(
                value.get("browserlessStartTimeoutSeconds", 20)
            ),
            browserless_idle_ttl_seconds=int(value.get("browserlessIdleTtlSeconds", 900)),
            browserless_warm_endpoint_ids=tuple(warm),
        )

    @property
    def ledger(self) -> Path:
        return self.state_root / "materialization-ledger.sqlite"

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


# PRE_SEND_CARRIER_FAILOVER_STANDINGS is imported from the pure Provider Boundary policy LEGO.
# Provider policy/auth/challenge/UI observations remain on the selected carrier.


def _carrier_last_use_path(config: BrowserlessAutomationConfig, endpoint_id: str) -> Path:
    return config.state_root / "carrier-lifecycle" / f"{_suffix(endpoint_id, 32)}.last-use"


def _touch_carrier_last_use(config: BrowserlessAutomationConfig, endpoint_id: str) -> Path:
    path = _carrier_last_use_path(config, endpoint_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    os.chmod(path, 0o600)
    return path


_CF07_SESSION_COUNT_CLASSES = frozenset({"ZERO", "NONZERO", "NOT_OBSERVED", "LEASE_BUSY"})


def _write_private_create_new(path: Path, value: object) -> bool:
    """Create one private JSON file without replacing an existing authority object."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(payload)
    return True


def _cf07_profile_first_observed(
    config: BrowserlessAutomationConfig, endpoint_id: str, *, observed_at_ms: int
) -> int:
    """Return Ordivon's first observation timestamp for one carrier profile."""
    root = config.state_root / "cf07-profile-first-observed"
    path = root / f"{_suffix(endpoint_id, 32)}.json"
    marker = {
        "schemaVersion": 1,
        "kind": "ordivon.cf07-profile-first-observed",
        "endpointId": endpoint_id,
        "firstObservedAtMs": observed_at_ms,
        "semanticProviderSessionCreationKnown": False,
    }
    if _write_private_create_new(path, marker):
        return observed_at_ms
    existing = _read_json(path)
    if set(existing) != {
        "schemaVersion",
        "kind",
        "endpointId",
        "firstObservedAtMs",
        "semanticProviderSessionCreationKnown",
    }:
        raise BrowserlessAutomationConflict("CF07 profile-first-observed marker has unexpected fields")
    if (
        existing.get("schemaVersion") != 1
        or existing.get("kind") != "ordivon.cf07-profile-first-observed"
        or existing.get("endpointId") != endpoint_id
        or existing.get("semanticProviderSessionCreationKnown") is not False
        or not isinstance(existing.get("firstObservedAtMs"), int)
        or existing["firstObservedAtMs"] < 0
    ):
        raise BrowserlessAutomationConflict("CF07 profile-first-observed marker is invalid")
    return existing["firstObservedAtMs"]


def _cf07_preflight_event(
    config: BrowserlessAutomationConfig,
    row: dict,
    *,
    lifecycle_started: bool,
    session_count_class: str,
) -> dict:
    """Persist one content-minimal prospective CF07 provider-preflight metadata event."""
    if session_count_class not in _CF07_SESSION_COUNT_CLASSES:
        raise ValueError("unsupported CF07 session-count class")
    endpoint_id = row.get("endpointId")
    standing = row.get("standing")
    if not isinstance(endpoint_id, str) or not endpoint_id:
        raise BrowserlessAutomationConflict("CF07 telemetry requires endpointId")
    if not isinstance(standing, str) or not standing:
        raise BrowserlessAutomationConflict("CF07 telemetry requires standing")
    for key in (
        "providerEffectAttempted",
        "clicked",
        "composerFilled",
        "sendAttempted",
        "assistantOutputRead",
    ):
        if row.get(key) is not False:
            raise BrowserlessAutomationConflict(
                f"CF07 telemetry refuses non-read-only provider observation: {key}"
            )

    observed_at_ms = time.time_ns() // 1_000_000
    first_observed_at_ms = _cf07_profile_first_observed(
        config, endpoint_id, observed_at_ms=observed_at_ms
    )
    event = {
        "schemaVersion": 1,
        "kind": "ordivon.cf07-provider-preflight-metadata",
        "observedAtMs": observed_at_ms,
        "endpointId": endpoint_id,
        "standing": standing,
        "lifecycleStarted": bool(lifecycle_started),
        "sessionCountClass": session_count_class,
        "providerEffectAttempted": False,
        "clicked": False,
        "composerFilled": False,
        "sendAttempted": False,
        "assistantOutputRead": False,
        "profileFirstObservedAtMs": first_observed_at_ms,
        "semanticProviderSessionCreationKnown": False,
    }
    nonce = _suffix(f"{endpoint_id}:{time.time_ns()}:{os.getpid()}", 16)
    path = (
        config.state_root
        / "cf07-provider-preflight-events"
        / f"{observed_at_ms}-{_suffix(endpoint_id, 16)}-{nonce}.json"
    )
    if not _write_private_create_new(path, event):
        raise BrowserlessAutomationConflict("CF07 provider-preflight event identity collision")
    return {
        "standing": "RECORDED",
        "observedAtMs": observed_at_ms,
        "profileFirstObservedAtMs": first_observed_at_ms,
        "sessionCountClass": session_count_class,
    }


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

    def _record_cf07_preflight(
        self,
        row: dict,
        *,
        lifecycle_started: bool,
        session_count_class: str,
    ) -> dict:
        """Attach non-authoritative telemetry standing without changing provider standing."""
        result = dict(row)
        try:
            result["cf07Telemetry"] = _cf07_preflight_event(
                self.config,
                result,
                lifecycle_started=lifecycle_started,
                session_count_class=session_count_class,
            )
        except Exception as error:
            result["cf07Telemetry"] = {
                "standing": "WRITE_FAILED",
                "errorClass": type(error).__name__,
            }
        result["providerBoundaryDiagnosis"] = diagnose_provider_preflight(result)
        return result

    @staticmethod
    def load_spec(path: Path) -> CampaignLaunchSpec:
        return CampaignLaunchSpec.from_dict(_read_json(path))

    def _materialization(self, spec: CampaignLaunchSpec, agent_id: str):
        requests = compile_campaign(spec)
        try:
            return requests[agent_id]
        except KeyError as error:
            raise BrowserlessAutomationConflict("agentId does not identify exactly one campaign request") from error

    def _materialization_dir(self, materialization) -> Path:
        return self.config.state_root / "materializations" / _suffix(materialization.request_id)

    def _binding_path(self, materialization) -> Path:
        return self._materialization_dir(materialization) / "carrier-binding.json"

    def _endpoint_by_id(self, endpoint_id: str):
        rows = [e for e in self.config.browserless_pool.endpoints if e.endpoint_id == endpoint_id]
        if len(rows) != 1:
            raise BrowserlessAutomationConflict("Browserless endpoint binding changed")
        return rows[0]

    def _validate_binding(self, materialization, row: dict) -> dict:
        if set(row) != {"effectId", "endpointId", "endpointIdentityDigest"}:
            raise BrowserlessAutomationConflict("carrier binding record has unexpected fields")
        if row.get("effectId") != materialization.request_id:
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

    def _current_binding(self, materialization) -> dict | None:
        current = self._binding_path(materialization)
        if not current.is_file():
            return None
        return self._validate_binding(materialization, _read_json(current))

    def _reconciliation_binding(self, materialization) -> tuple[dict | None, str | None]:
        """Return only a carrier that is still the same physical Browserless identity.

        Reconciliation is observational: a restarted/removed carrier cannot prove anything about
        the old SEND boundary, but that loss of observation authority is not an integrity failure
        and never authorizes rerouting or resend. Corrupt/cross-effect binding bytes still fail hard.
        """
        try:
            return self._current_binding(materialization), None
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
        by_agent = compile_campaign(spec)
        active = 0
        for row in result.get("materializations", []):
            materialization = by_agent.get(row.get("agentId"))
            if materialization is None:
                continue
            path = (
                self._materialization_dir(materialization) / "human-handoff" / f"{_suffix(materialization.request_id)}.json"
            )
            if not path.is_file():
                continue
            try:
                handoff = load_verified_handoff(path)
            except Exception:
                continue
            available = (
                handoff.get("effectId") == materialization.request_id
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

    def ensure_endpoint_active(self, endpoint) -> dict:
        """Ensure one explicitly managed Browserless carrier is active, then observe health.

        Endpoint health remains observational. Lifecycle mutation exists only when the endpoint
        configuration explicitly binds one systemd service unit; unmanaged/test endpoints retain
        the previous observation-only behavior.
        """
        raw_unit = getattr(endpoint, "service_unit", None)
        unit = raw_unit if isinstance(raw_unit, str) and raw_unit else None
        started = False
        if unit is not None:
            observed = subprocess.run(
                ["/usr/bin/systemctl", "is-active", "--quiet", unit],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if observed.returncode != 0:
                proc = subprocess.run(
                    ["/usr/bin/systemctl", "start", unit],
                    capture_output=True,
                    text=True,
                    timeout=self.config.browserless_start_timeout_seconds,
                    check=False,
                )
                if proc.returncode != 0:
                    return {
                        "id": endpoint.endpoint_id,
                        "healthy": False,
                        "identityDigest": endpoint.identity_digest,
                        "detail": f"systemd-start-rc-{proc.returncode}",
                        "serviceUnit": unit,
                        "lifecycleStarted": False,
                    }
                started = True
        deadline = time.monotonic() + self.config.browserless_start_timeout_seconds
        health = endpoint.health(timeout_seconds=5)
        while not health.get("healthy") and unit is not None and time.monotonic() < deadline:
            time.sleep(0.25)
            health = endpoint.health(timeout_seconds=3)
        if unit is not None:
            health = dict(health)
            health["serviceUnit"] = unit
            health["lifecycleStarted"] = started
            if health.get("healthy") is True:
                _touch_carrier_last_use(self.config, endpoint.endpoint_id)
        return health

    def _require_provider_ready(self, endpoint_id: str) -> dict:
        observation = self.provider_preflight(endpoint_id)
        standing = observation.get("standing")
        if standing != "READY":
            raise BrowserlessAutomationHold(
                f"provider admission HOLD on {endpoint_id}: {standing or 'UNRESOLVED'}; no new provider-effect workflow admitted"
            )
        return observation

    def _require_materialization_substrate_available(
        self, materialization, *, observations: dict[str, dict] | None = None
    ):
        # Public admission observes only physical Browserless reachability. Provider/UI admission
        # belongs to the Temporal worker while it owns the exact persistent-profile carrier lease.
        observed = observations if observations is not None else {}
        rejected: list[str] = []
        for endpoint in self.config.browserless_pool.candidates(materialization.request_id):
            health = observed.get(endpoint.endpoint_id)
            if health is None:
                health = self.ensure_endpoint_active(endpoint)
                observed[endpoint.endpoint_id] = health
            if health.get("healthy"):
                return endpoint
            rejected.append(
                f"{endpoint.endpoint_id}={health.get('detail') or health.get('status') or 'UNHEALTHY'}"
            )
        raise BrowserlessAutomationHold(
            "provider materialization substrate HOLD: no healthy carrier before Temporal admission; "
            + ", ".join(rejected)
        )

    def _gate_unrecorded_materializations(self, spec: CampaignLaunchSpec) -> dict:
        census = campaign_census(spec, self.config.ledger)
        by_agent = {row["agentId"]: row for row in census["materializations"]}
        observations: dict[str, dict] = {}
        for agent_id, materialization in compile_campaign(spec).items():
            row = by_agent[agent_id]
            # Campaign launch is roster admission, not recovery. A PRE_EFFECT_FAILED materialization
            # already has one durable materialization workflow/effect identity and must require an explicit
            # materialization-level re-entry; otherwise exact campaign replay would create fresh retries.
            if row.get("materializationStanding") is not None:
                continue
            self._require_materialization_substrate_available(materialization, observations=observations)
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
        campaign_agent_ids: tuple[str, ...] | None = None,
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
                "--campaign-ref",
                registration["campaignRef"],
                "--address",
                self.config.temporal_address,
                "--namespace",
                self.config.temporal_namespace,
                "--task-queue",
                self.config.temporal_task_queue,
            ]
            if agent_id is not None:
                cmd += ["--agent-id", agent_id]
            if campaign_agent_ids is not None:
                for campaign_agent_id in campaign_agent_ids:
                    cmd += ["--campaign-agent-id", campaign_agent_id]
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
        if operation == "campaign-materialize":
            effects = row.get("effects")
            if (
                row.get("kind") != "temporal-campaign-materialization-admission"
                or row.get("disposition") not in {"admitted", "started", "existing"}
                or not row.get("workflowId")
                or not isinstance(effects, list)
                or not effects
            ):
                raise BrowserlessAutomationAmbiguous(
                    "Temporal campaign admission outcome is unknown because the parent receipt is malformed; observe the same campaign workflow identity before any retry"
                )
            for effect in effects:
                if (
                    not isinstance(effect, dict)
                    or not effect.get("agentId")
                    or not effect.get("effectId")
                ):
                    raise BrowserlessAutomationAmbiguous(
                        "Temporal campaign admission outcome is unknown because one child intent is malformed; observe the same campaign workflow identity before any retry"
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
        census = self._gate_unrecorded_materializations(spec)
        unrecorded = tuple(
            row["agentId"]
            for row in census["materializations"]
            if row.get("materializationStanding") is None
        )
        if unrecorded:
            temporal = self._temporal_admit(
                spec_path,
                "campaign-materialize",
                campaign_agent_ids=unrecorded,
            )
        else:
            temporal = {
                "kind": "temporal-campaign-materialization-admission",
                "disposition": "not-required",
                "requested": 0,
                "effects": [],
            }
        return {
            "schemaVersion": 1,
            "kind": "ordivon.temporal-campaign-admission",
            "campaignId": spec.campaign_id,
            "temporal": temporal,
            "preEffectRetries": [],
            "census": campaign_census(spec, self.config.ledger),
        }

    def launch_reconcile(self, spec_path: Path, agent_id: str) -> dict:
        spec = self.load_spec(spec_path)
        materialization = self._materialization(spec, agent_id)
        census = campaign_census(spec, self.config.ledger)
        row = next(r for r in census["materializations"] if r["agentId"] == agent_id)
        standing = row.get("materializationStanding")

        if standing in {None, "pre-effect-failed"}:
            self._require_materialization_substrate_available(materialization)
            operation = "pre-effect-retry" if standing == "pre-effect-failed" else "materialize"
            temporal = self._temporal_admit(spec_path, operation, agent_id=agent_id)
            return {
                "schemaVersion": 1,
                "kind": "ordivon.temporal-materialization-reconcile-admission",
                "agentId": agent_id,
                "effectId": materialization.request_id,
                "temporal": temporal,
                "safeToResend": False,
                "census": campaign_census(spec, self.config.ledger),
            }

        if standing == "bound":
            return {
                "schemaVersion": 1,
                "kind": "ordivon.temporal-materialization-reconcile-admission",
                "agentId": agent_id,
                "effectId": materialization.request_id,
                "safeToResend": False,
                "census": census,
            }

        if standing not in {"unknown", "submit-observed"}:
            raise BrowserlessAutomationHold(
                "materialization cannot be safely converged from its current materialization standing"
            )

        temporal = self._temporal_admit(spec_path, "reconcile", agent_id=agent_id)
        return {
            "schemaVersion": 1,
            "kind": "ordivon.temporal-materialization-reconcile-admission",
            "agentId": agent_id,
            "effectId": materialization.request_id,
            "temporal": temporal,
            "safeToResend": False,
            "census": census,
        }


    def human_handoff_info(self, spec_path: Path, agent_id: str) -> dict:
        spec = self.load_spec(spec_path)
        materialization = self._materialization(spec, agent_id)
        census = campaign_census(spec, self.config.ledger)
        row = next(r for r in census["materializations"] if r["agentId"] == agent_id)
        # While a self-hosted VNC handoff is actively attached, the effect ledger may remain UNKNOWN
        # because the effect attempt was durably claimed before target execution. The private handoff
        # receipt independently proves providerEffectAttempted=false during that bounded window.
        if row.get("materializationStanding") not in {"human-required", "unknown"}:
            raise BrowserlessAutomationHold(
                "materialization is not waiting for human provider verification"
            )
        path = self._materialization_dir(materialization) / "human-handoff" / f"{_suffix(materialization.request_id)}.json"
        if not path.is_file():
            raise BrowserlessAutomationHold("human verification handoff receipt is unavailable")
        value = load_verified_handoff(path)
        if (
            value.get("effectId") != materialization.request_id
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
            "effectId": materialization.request_id,
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
        materialization = self._materialization(spec, agent_id)
        census = campaign_census(spec, self.config.ledger)
        row = next(r for r in census["materializations"] if r["agentId"] == agent_id)
        if row.get("materializationStanding") != "human-required":
            raise BrowserlessAutomationHold(
                "only a HUMAN_REQUIRED materialization may resume after human verification"
            )
        handoff_path = (
            self._materialization_dir(materialization) / "human-handoff" / f"{_suffix(materialization.request_id)}.json"
        )
        if not handoff_path.is_file():
            raise BrowserlessAutomationHold(
                "HUMAN_REQUIRED materialization has no private handoff receipt"
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
            "effectId": materialization.request_id,
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
        materialization = self._materialization(spec, agent_id)
        try:
            turn_request_id = require_uuid7(turn_request_id, "turnRequestId")
        except ValueError as error:
            raise BrowserlessAutomationConflict(str(error)) from error
        prompt = _continuation_prompt(prompt)
        census = campaign_census(spec, self.config.ledger)
        row = next(r for r in census["materializations"] if r["agentId"] == agent_id)
        if row.get("materializationStanding") != "bound" or not row.get("providerResource"):
            raise BrowserlessAutomationHold("materialization is not provider-bound")
        binding = self._current_binding(materialization)
        if binding is None:
            raise BrowserlessAutomationHold(
                "provider-bound materialization has no current carrier binding"
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
                "kind": "ordivon.temporal-conversation-continue-admission",
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
            "kind": "ordivon.temporal-conversation-continue-admission",
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
        substrate = self.ensure_endpoint_active(endpoint)
        lifecycle_started = substrate.get("lifecycleStarted") is True
        if not substrate.get("healthy"):
            return self._record_cf07_preflight(
                {
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
                },
                lifecycle_started=lifecycle_started,
                session_count_class="NOT_OBSERVED",
            )
        # A session can predate the current Ordivon lease contract or come from a non-cooperating
        # client. The filesystem lease alone therefore does not prove exclusive Browserless use.
        sessions = endpoint.sessions(timeout_seconds=3)
        if sessions:
            return self._record_cf07_preflight(
                {
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
                },
                lifecycle_started=lifecycle_started,
                session_count_class="NONZERO",
            )
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
        return self._record_cf07_preflight(
            row,
            lifecycle_started=lifecycle_started,
            session_count_class="ZERO",
        )

    def provider_preflight(self, endpoint_id: str) -> dict:
        endpoint = self._endpoint_by_id(endpoint_id)
        # Public diagnostics are second clients unless they can acquire the carrier nonblockingly.
        try:
            with _carrier_lease(self.config, endpoint.endpoint_id, blocking=False):
                return self._provider_preflight_under_carrier_lease(endpoint.endpoint_id)
        except BrowserlessCarrierBusy:
            substrate = endpoint.health(timeout_seconds=5)
            return self._record_cf07_preflight(
                {
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
                },
                lifecycle_started=False,
                session_count_class="LEASE_BUSY",
            )

    def _doctor_browser_substrate_health(self) -> dict:
        rows: list[dict] = []
        warm = set(self.config.browserless_warm_endpoint_ids)
        for endpoint in self.config.browserless_pool.endpoints:
            raw_unit = getattr(endpoint, "service_unit", None)
            unit = raw_unit if isinstance(raw_unit, str) and raw_unit else None
            if unit is None:
                row = endpoint.health()
                row = dict(row)
                row["lifecycleStanding"] = "UNMANAGED_OBSERVED"
                rows.append(row)
                continue

            observed = subprocess.run(
                ["/usr/bin/systemctl", "is-active", "--quiet", unit],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if observed.returncode == 0:
                row = dict(endpoint.health())
                row["serviceUnit"] = unit
                row["lifecycleStanding"] = "ACTIVE"
                rows.append(row)
                continue

            base = {
                "id": endpoint.endpoint_id,
                "identityDigest": endpoint.identity_digest,
                "networkNamespace": endpoint.network_namespace,
                "serviceUnit": unit,
                "observedActive": False,
            }
            if endpoint.endpoint_id in warm:
                rows.append(
                    {
                        **base,
                        "healthy": False,
                        "lifecycleStanding": "WARM_ENDPOINT_INACTIVE",
                        "detail": "configured warm endpoint is not active",
                    }
                )
            else:
                rows.append(
                    {
                        **base,
                        "healthy": True,
                        "lifecycleStanding": "SLEEPING_ON_DEMAND",
                    }
                )

        return {
            "kind": "browserless",
            "healthy": bool(rows) and all(row["healthy"] for row in rows),
            "endpoints": rows,
        }

    def doctor(self) -> dict:
        health = self._doctor_browser_substrate_health()

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
            "providerBoundaryPolicy": provider_boundary_policy(),
            "ledger": ledger,
        }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, required=True)
    sub = p.add_subparsers(dest="action", required=True)
    for n in ("census", "launch"):
        s = sub.add_parser(n)
        s.add_argument("--spec", type=Path, required=True)
    for n in ("reconcile", "human-handoff", "human-resume"):
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
