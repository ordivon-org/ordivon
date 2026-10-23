#!/usr/bin/env python3
"""Worker-only Browserless provider-effect adapter for Agent Automation.

This module is the sole owner of raw ChatGPT Web write capability. It is intended to be
instantiated only by Temporal Activities. MCP, CLI and local read bridges use
BrowserlessAutomationService, which deliberately exposes no raw provider-effect methods.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from ordivon_harness.gateway_execution_port import GatewayExecutionPort
from ordivon_harness.mcp_http_client import LoopbackMcpEndpoint, OfficialMcpClient
from ordivon_harness.user_browser_gateway import (
    UserBrowserGatewayConfig,
    UserBrowserGatewayController,
)

try:
    from agent_automation_browserless import (
        BrowserlessAutomationConfig,
        BrowserlessAutomationConflict,
        BrowserlessAutomationHold,
        BrowserlessAutomationService,
        diagnose_provider_preflight,
        _suffix,
        _write_private,
    )
    from browserless_materialization_target import BrowserlessMaterializationTarget
    from chatgpt_provider_resource import canonical_chatgpt_resource
    from campaign_materialization import campaign_census
    from sqlite_conversation_materializer import SQLiteConversationMaterializer
    from windows_user_browser_materialization_target import WindowsUserBrowserMaterializationTarget
    from cft_human_session import DurableSessionAuthority, resolve_session
    from cft_human_materialization import (
        CftAuthenticatedSendTarget,
        CftHumanRequiredTarget,
        prepare_chatgpt_human_session,
    )
except ModuleNotFoundError:
    from scripts.agent_automation_browserless import (
        BrowserlessAutomationConfig,
        BrowserlessAutomationConflict,
        BrowserlessAutomationHold,
        BrowserlessAutomationService,
        diagnose_provider_preflight,
        _suffix,
        _write_private,
    )
    from scripts.browserless_materialization_target import BrowserlessMaterializationTarget
    from scripts.chatgpt_provider_resource import canonical_chatgpt_resource
    from scripts.campaign_materialization import campaign_census
    from scripts.sqlite_conversation_materializer import SQLiteConversationMaterializer
    from scripts.windows_user_browser_materialization_target import WindowsUserBrowserMaterializationTarget
    from scripts.cft_human_session import DurableSessionAuthority, resolve_session
    from scripts.cft_human_materialization import (
        CftAuthenticatedSendTarget,
        CftHumanRequiredTarget,
        prepare_chatgpt_human_session,
    )


class BrowserlessEffectAdapter:
    """Raw effect writer. Temporal Activities are the only production caller."""

    def __init__(self, config: BrowserlessAutomationConfig) -> None:
        self.config = config
        self.context = BrowserlessAutomationService(config)

    def _write_binding(self, materialization, endpoint) -> dict:
        binding = {
            "effectId": materialization.request_id,
            "endpointId": endpoint.endpoint_id,
            "endpointIdentityDigest": endpoint.identity_digest,
        }
        _write_private(self.context._binding_path(materialization), binding)
        return binding

    def _target(self, materialization, endpoint):
        if isinstance(getattr(endpoint, "service_unit", None), str):
            health = self.context.ensure_endpoint_active(endpoint)
            if not health.get("healthy"):
                raise BrowserlessAutomationHold(
                    f"Browserless carrier unavailable: {endpoint.endpoint_id}; {health.get('detail') or 'UNHEALTHY'}"
                )
        return BrowserlessMaterializationTarget(
            endpoint=endpoint,
            state_dir=self.context._materialization_dir(materialization),
            submit_script=self.config.submit_script,
            reconcile_script=self.config.reconcile_script,
            playwright_python=self.config.playwright_python,
            wait_stable_seconds=self.config.wait_stable_seconds,
            reconnect_ms=self.config.reconnect_ms,
            human_resume_script=self.config.human_resume_script,
            human_handoff_ms=self.config.human_handoff_ms,
            human_handoff_mode=self.config.human_handoff_mode,
            session_timeout_ms=self.config.browser_session_timeout_ms,
        )

    def _user_browser_target(self):
        cfg = self.config.windows_user_browser
        if cfg is None:
            raise BrowserlessAutomationHold("Windows user-browser carrier is not configured")
        bearer_path = os.environ.get("ORDIVON_AGENT_GATEWAY_BEARER_TOKEN_FILE", "").strip()
        if not bearer_path:
            raise BrowserlessAutomationHold("Gateway local service credential is not injected")
        client = OfficialMcpClient(
            LoopbackMcpEndpoint(cfg.gateway_url),
            bearer_token_file=Path(bearer_path),
            timeout_seconds=max(1.0, cfg.timeout_ms / 1000),
        )
        controller = UserBrowserGatewayController(
            GatewayExecutionPort(client, max_observations=4096, poll_interval_seconds=0.25),
            UserBrowserGatewayConfig(
                workspace_id=cfg.workspace_id,
                powershell_path=cfg.powershell_path,
                driver_path=cfg.driver_path,
                proxy_url=cfg.proxy_url,
                linux_stage_root=str(cfg.linux_stage_root),
                windows_stage_root=cfg.windows_stage_root,
                timeout_ms=cfg.timeout_ms,
            ),
        )
        return WindowsUserBrowserMaterializationTarget(
            state_dir=cfg.linux_stage_root,
            controller=controller,
        )

    @staticmethod
    def _user_browser_receipt(receipt) -> dict:
        return {
            "standing": receipt.standing.value,
            "providerResource": (
                canonical_chatgpt_resource(receipt.provider_conversation_coordinate)
                if receipt.provider_conversation_coordinate
                else None
            ),
            "evidenceDigest": receipt.evidence_digest,
            "detail": receipt.detail,
            "receiptDigest": receipt.receipt_digest,
        }

    def materialize_user_browser(self, spec_path: Path, agent_id: str) -> dict:
        spec = self.context.load_spec(spec_path)
        request = self.context._materialization(spec, agent_id)
        census = campaign_census(spec, self.config.ledger)
        row = next(item for item in census["materializations"] if item["agentId"] == agent_id)
        standing = row.get("materializationStanding")
        if standing in {"bound", "ready-confirmed"}:
            return {
                "schemaVersion": 1,
                "kind": "ordivon.user-browser-materialization",
                "action": "existing-terminal",
                "agentId": agent_id,
                "effectId": request.request_id,
                "materialization": row,
                "census": census,
            }
        if standing == "human-required":
            return {
                "schemaVersion": 1,
                "kind": "ordivon.user-browser-materialization",
                "action": "existing-human-required-no-blind-resume",
                "agentId": agent_id,
                "effectId": request.request_id,
                "safeToResend": False,
                "materialization": row,
                "census": census,
            }
        if standing in {"unknown", "submit-observed"}:
            return self.reconcile_user_browser(spec_path, agent_id)
        receipt = SQLiteConversationMaterializer(
            self.config.ledger, self._user_browser_target()
        ).materialize(request)
        return {
            "schemaVersion": 1,
            "kind": "ordivon.user-browser-materialization",
            "action": "materialize",
            "agentId": agent_id,
            "effectId": request.request_id,
            "receipt": self._user_browser_receipt(receipt),
            "census": campaign_census(spec, self.config.ledger),
        }

    def reconcile_user_browser(self, spec_path: Path, agent_id: str) -> dict:
        spec = self.context.load_spec(spec_path)
        request = self.context._materialization(spec, agent_id)
        census = campaign_census(spec, self.config.ledger)
        row = next(item for item in census["materializations"] if item["agentId"] == agent_id)
        if row.get("materializationStanding") not in {"unknown", "submit-observed"}:
            return {
                "schemaVersion": 1,
                "kind": "ordivon.user-browser-reconcile",
                "action": "existing-non-ambiguous-standing",
                "agentId": agent_id,
                "effectId": request.request_id,
                "safeToResend": False,
                "materialization": row,
                "census": census,
            }
        receipt = SQLiteConversationMaterializer(
            self.config.ledger, self._user_browser_target()
        ).reconcile(request)
        return {
            "schemaVersion": 1,
            "kind": "ordivon.user-browser-reconcile",
            "action": "reconcile-existing-effect",
            "agentId": agent_id,
            "effectId": request.request_id,
            "safeToResend": False,
            "receipt": self._user_browser_receipt(receipt),
            "census": campaign_census(spec, self.config.ledger),
        }

    def materialize(
        self,
        spec_path: Path,
        agent_id: str,
        *,
        endpoint_id: str | None = None,
        provider_preflight: dict | None = None,
    ) -> dict:
        spec = self.context.load_spec(spec_path)
        materialization = self.context._materialization(spec, agent_id)
        census = campaign_census(spec, self.config.ledger)
        row = next(r for r in census["materializations"] if r["agentId"] == agent_id)
        standing = row.get("materializationStanding")
        if standing in {"bound", "ready-confirmed"}:
            return {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-materialization",
                "action": "existing-terminal",
                "materialization": row,
                "census": census,
            }
        if standing == "human-required":
            durable_handoff_path = (
                self.context._materialization_dir(materialization)
                / "durable-human-handoff"
                / f"{_suffix(materialization.request_id)}.json"
            )
            if durable_handoff_path.is_file():
                try:
                    from cft_human_materialization import load_verified_handoff
                except ModuleNotFoundError:
                    from scripts.cft_human_materialization import load_verified_handoff
                handoff = load_verified_handoff(durable_handoff_path)
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.durable-human-materialization",
                    "action": "existing-human-control-transfer",
                    "agentId": agent_id,
                    "effectId": materialization.request_id,
                    "receipt": {
                        "standing": "human-required",
                        "providerResource": None,
                        "evidenceDigest": handoff["handoffDigest"],
                        "detail": row.get("detail"),
                    },
                    "humanHandoff": handoff,
                    "census": census,
                }
            return {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-materialization",
                "action": "existing-human-required",
                "materialization": row,
                "census": census,
            }
        if standing in {"unknown", "submit-observed"}:
            binding, unavailable_reason = self.context._reconciliation_binding(materialization)
            if binding is None:
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.browserless-materialization",
                    "action": "existing-effect-unknown-no-resend",
                    "safeToResend": False,
                    "reconciliationUnavailableReason": unavailable_reason,
                    "materialization": row,
                    "census": census,
                }
            return self.reconcile(spec_path, agent_id)
        endpoint = (
            self.context._endpoint_by_id(endpoint_id)
            if endpoint_id is not None
            else self.config.browserless_pool.select(materialization.request_id)
        )
        provider_boundary_diagnosis = None
        if endpoint_id is not None:
            observation = provider_preflight
            if (
                not isinstance(observation, dict)
                or observation.get("endpointId") != endpoint.endpoint_id
            ):
                raise BrowserlessAutomationConflict(
                    "worker-selected materialization endpoint requires its exact leased provider preflight observation"
                )
            for key in (
                "providerEffectAttempted",
                "clicked",
                "composerFilled",
                "sendAttempted",
                "assistantOutputRead",
            ):
                if observation.get(key) is not False:
                    raise BrowserlessAutomationConflict(
                        f"worker provider preflight violated read-only contract: {key}"
                    )
            provider_boundary_diagnosis = diagnose_provider_preflight(observation)
            provided_diagnosis = observation.get("providerBoundaryDiagnosis")
            if (
                provided_diagnosis is not None
                and provided_diagnosis != provider_boundary_diagnosis
            ):
                raise BrowserlessAutomationConflict(
                    "worker provider preflight diagnosis disagrees with policy classifier"
                )
            if provider_boundary_diagnosis["carrierRouting"] == "FAILOVER_ALLOWED":
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.browserless-materialization",
                    "action": "carrier-pre-effect-unavailable",
                    "agentId": agent_id,
                    "effectId": materialization.request_id,
                    "endpointId": endpoint.endpoint_id,
                    "providerPreflight": observation,
                    "providerBoundaryDiagnosis": provider_boundary_diagnosis,
                    "census": census,
                }
        if (
            provider_boundary_diagnosis is not None
            and provider_boundary_diagnosis.get("providerAction") == "HUMAN_CONTROL_TRANSFER"
        ):
            handoff_path = (
                self.context._materialization_dir(materialization)
                / "durable-human-handoff"
                / f"{_suffix(materialization.request_id)}.json"
            )
            target = CftHumanRequiredTarget(
                handoff_path=handoff_path,
                session_request_id=f"materialization-auth:{materialization.request_id}",
                authority_factory=DurableSessionAuthority,
                prepare=prepare_chatgpt_human_session,
            )
            receipt = SQLiteConversationMaterializer(self.config.ledger, target).materialize(
                materialization
            )
            handoff = target.last_handoff
            if handoff is None and handoff_path.is_file():
                from cft_human_materialization import load_verified_handoff

                handoff = load_verified_handoff(handoff_path)
            if handoff is None:
                raise BrowserlessAutomationConflict(
                    "durable human materialization produced HUMAN_REQUIRED without handoff evidence"
                )
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.durable-human-materialization",
                "action": "human-control-transfer",
                "agentId": agent_id,
                "effectId": materialization.request_id,
                "receipt": {
                    "standing": receipt.standing.value,
                    "providerResource": None,
                    "evidenceDigest": receipt.evidence_digest,
                    "detail": receipt.detail,
                    "receiptDigest": receipt.receipt_digest,
                },
                "humanHandoff": handoff,
                "providerBoundaryDiagnosis": provider_boundary_diagnosis,
                "census": campaign_census(spec, self.config.ledger),
            }
            return result
        binding = self._write_binding(materialization, endpoint)
        receipt = SQLiteConversationMaterializer(
            self.config.ledger, self._target(materialization, endpoint)
        ).materialize(materialization)
        result = {
            "schemaVersion": 1,
            "kind": "ordivon.browserless-materialization",
            "action": "materialize",
            "agentId": agent_id,
            "effectId": materialization.request_id,
            "receipt": {
                "standing": receipt.standing.value,
                "providerResource": canonical_chatgpt_resource(
                    receipt.provider_conversation_coordinate
                )
                if receipt.provider_conversation_coordinate
                else None,
                "evidenceDigest": receipt.evidence_digest,
                "detail": receipt.detail,
                "receiptDigest": receipt.receipt_digest,
            },
            "census": campaign_census(spec, self.config.ledger),
        }
        if provider_boundary_diagnosis is not None:
            result["providerBoundaryDiagnosis"] = provider_boundary_diagnosis
        return result

    def resume_after_human(self, spec_path: Path, agent_id: str) -> dict:
        spec = self.context.load_spec(spec_path)
        request = self.context._materialization(spec, agent_id)
        census = campaign_census(spec, self.config.ledger)
        row = next(r for r in census["materializations"] if r["agentId"] == agent_id)
        standing = row.get("materializationStanding")
        if standing in {"unknown", "submit-observed"}:
            return self.reconcile(spec_path, agent_id)
        if standing != "human-required":
            return {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-human-resume",
                "action": "existing-non-human-standing",
                "agentId": agent_id,
                "materialization": row,
                "census": census,
            }
        durable_handoff_path = (
            self.context._materialization_dir(request)
            / "durable-human-handoff"
            / f"{_suffix(request.request_id)}.json"
        )
        if durable_handoff_path.is_file():
            target = CftAuthenticatedSendTarget(
                handoff_path=durable_handoff_path,
                state_dir=self.context._materialization_dir(request),
                playwright_python=self.config.playwright_python,
                resume_script=Path(__file__).resolve().with_name("playwright_cft_chatgpt_resume.py"),
                wait_stable_seconds=self.config.wait_stable_seconds,
            )
            receipt = SQLiteConversationMaterializer(self.config.ledger, target).resume_human(
                request
            )
            return {
                "schemaVersion": 1,
                "kind": "ordivon.durable-human-resume",
                "action": "resume-after-durable-human-auth",
                "agentId": agent_id,
                "effectId": request.request_id,
                "receipt": {
                    "standing": receipt.standing.value,
                    "providerResource": canonical_chatgpt_resource(
                        receipt.provider_conversation_coordinate
                    )
                    if receipt.provider_conversation_coordinate
                    else None,
                    "evidenceDigest": receipt.evidence_digest,
                    "detail": receipt.detail,
                    "receiptDigest": receipt.receipt_digest,
                },
                "census": campaign_census(spec, self.config.ledger),
            }
        binding = self.context._current_binding(request)
        if binding is None:
            raise BrowserlessAutomationHold(
                "human-required materialization has no durable CfT handoff or current Browserless carrier binding"
            )
        endpoint = self.context._endpoint_by_id(binding["endpointId"])
        receipt = SQLiteConversationMaterializer(
            self.config.ledger, self._target(request, endpoint)
        ).resume_human(request)
        return {
            "schemaVersion": 1,
            "kind": "ordivon.browserless-human-resume",
            "action": "resume-after-human",
            "agentId": agent_id,
            "effectId": request.request_id,
            "receipt": {
                "standing": receipt.standing.value,
                "providerResource": canonical_chatgpt_resource(
                    receipt.provider_conversation_coordinate
                )
                if receipt.provider_conversation_coordinate
                else None,
                "evidenceDigest": receipt.evidence_digest,
                "detail": receipt.detail,
                "receiptDigest": receipt.receipt_digest,
            },
            "census": campaign_census(spec, self.config.ledger),
        }

    def reconcile(self, spec_path: Path, agent_id: str) -> dict:
        spec = self.context.load_spec(spec_path)
        request = self.context._materialization(spec, agent_id)
        census = campaign_census(spec, self.config.ledger)
        row = next(r for r in census["materializations"] if r["agentId"] == agent_id)
        binding, unavailable_reason = self.context._reconciliation_binding(request)
        if binding is None:
            return {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-reconcile",
                "action": "preserved-standing-no-current-carrier-evidence",
                "agentId": agent_id,
                "safeToResend": False,
                "reconciliationUnavailableReason": unavailable_reason,
                "materialization": row,
                "census": census,
            }
        endpoint = self.context._endpoint_by_id(binding["endpointId"])
        receipt = SQLiteConversationMaterializer(
            self.config.ledger, self._target(request, endpoint)
        ).reconcile(request)
        return {
            "schemaVersion": 1,
            "kind": "ordivon.browserless-reconcile",
            "action": "current-carrier-reconcile",
            "agentId": agent_id,
            "receipt": {
                "standing": receipt.standing.value,
                "providerResource": canonical_chatgpt_resource(
                    receipt.provider_conversation_coordinate
                )
                if receipt.provider_conversation_coordinate
                else None,
                "evidenceDigest": receipt.evidence_digest,
                "detail": receipt.detail,
                "receiptDigest": receipt.receipt_digest,
            },
            "safeToResend": False,
            "census": campaign_census(spec, self.config.ledger),
        }

    def send_adopted_turn(
        self,
        spec_path: Path,
        campaign_ref: str,
        agent_id: str,
        *,
        turn_request_id: str,
        prompt: str,
    ) -> dict:
        if not isinstance(prompt, str) or not prompt or prompt != prompt.strip():
            raise ValueError("continuation prompt must be non-empty and trimmed")
        if len(prompt.encode("utf-8")) > 32768:
            raise ValueError("continuation prompt exceeds 32768 UTF-8 bytes")
        affinity = self.context.conversation_affinity(spec_path, campaign_ref, agent_id)
        if (
            affinity.get("standing") != "READY"
            or affinity.get("affinityKind") != "DURABLE_CFT_SESSION"
        ):
            raise BrowserlessAutomationHold(
                "durable CfT conversation affinity is not READY"
            )
        session_id = affinity.get("sessionId")
        if not isinstance(session_id, str):
            raise BrowserlessAutomationConflict(
                "durable CfT conversation affinity lacks session identity"
            )
        try:
            session = resolve_session(session_id)
        except Exception as error:
            raise BrowserlessAutomationHold(
                f"durable CfT session is unavailable: {error}"
            ) from error
        if session.get("standing") != "READY" or session.get("sessionId") != session_id:
            raise BrowserlessAutomationHold("durable CfT session is not READY")
        cdp_endpoint = session.get("cdpEndpoint")
        resource = affinity.get("providerResource")
        if not isinstance(cdp_endpoint, str) or not isinstance(resource, str):
            raise BrowserlessAutomationConflict(
                "durable CfT continuation lacks exact session/resource coordinates"
            )
        transient: tempfile.TemporaryDirectory[str] | None = tempfile.TemporaryDirectory(
            prefix="ordivon-cft-turn-"
        )
        effective_prompt_file = Path(transient.name) / "prompt.txt"
        effective_prompt_file.write_text(prompt, encoding="utf-8")
        os.chmod(effective_prompt_file, 0o600)
        try:
            spec = self.context.load_spec(spec_path)
            materialization = self.context._materialization(spec, agent_id)
            receipt_out = (
                self.context._materialization_dir(materialization)
                / "turns"
                / f"{_suffix(turn_request_id)}.json"
            )
            cmd = [
                str(self.config.playwright_python),
                str(self.config.turn_script),
                "--cdp-endpoint",
                cdp_endpoint,
                "--session-id",
                session_id,
                "--target-resource",
                resource,
                "--prompt-file",
                str(effective_prompt_file),
                "--turn-request-id",
                turn_request_id,
                "--ledger",
                str(self.config.turn_ledger),
                "--receipt-out",
                str(receipt_out),
            ]
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=75, check=False
            )
            if proc.returncode != 0:
                detail = (proc.stderr or "").strip().replace("\n", " ")[-1200:]
                suffix = f"; detail={detail}" if detail else ""
                raise BrowserlessAutomationHold(
                    f"CfT continuation failed closed (rc={proc.returncode}{suffix})"
                )
            try:
                return json.loads(proc.stdout.strip().splitlines()[-1])
            except Exception as error:
                raise BrowserlessAutomationConflict(
                    "CfT continuation returned no receipt"
                ) from error
        finally:
            if transient is not None:
                transient.cleanup()

    def send_turn(
        self, spec_path: Path, agent_id: str, *, turn_request_id: str, prompt: str
    ) -> dict:
        if not isinstance(prompt, str) or not prompt or prompt != prompt.strip():
            raise ValueError("continuation prompt must be non-empty and trimmed")
        if len(prompt.encode("utf-8")) > 32768:
            raise ValueError("continuation prompt exceeds 32768 UTF-8 bytes")
        transient: tempfile.TemporaryDirectory[str] | None = tempfile.TemporaryDirectory(
            prefix="ordivon-browserless-turn-"
        )
        effective_prompt_file = Path(transient.name) / "prompt.txt"
        effective_prompt_file.write_text(prompt, encoding="utf-8")
        os.chmod(effective_prompt_file, 0o600)
        try:
            spec = self.context.load_spec(spec_path)
            materialization = self.context._materialization(spec, agent_id)
            census = campaign_census(spec, self.config.ledger)
            row = next(r for r in census["materializations"] if r["agentId"] == agent_id)
            resource = row.get("providerResource")
            if row.get("materializationStanding") != "bound" or not resource:
                raise BrowserlessAutomationHold("materialization is not provider-bound")
            binding = self.context._current_binding(materialization)
            if binding is None:
                raise BrowserlessAutomationHold(
                    "provider-bound materialization has no current carrier binding"
                )
            endpoint = self.context._endpoint_by_id(binding["endpointId"])
            if isinstance(getattr(endpoint, "service_unit", None), str):
                health = self.context.ensure_endpoint_active(endpoint)
                if not health.get("healthy"):
                    raise BrowserlessAutomationHold(
                        f"Browserless carrier unavailable: {endpoint.endpoint_id}; {health.get('detail') or 'UNHEALTHY'}"
                    )
            receipt_out = (
                self.context._materialization_dir(materialization) / "turns" / f"{_suffix(turn_request_id)}.json"
            )
            cmd = [
                *endpoint.exec_prefix,
                str(self.config.playwright_python),
                str(self.config.turn_script),
                "--browserless-endpoint",
                endpoint.public_connection_endpoint,
                "--browserless-token-file",
                str(endpoint.token_file),
                "--endpoint-id",
                endpoint.endpoint_id,
                "--target-resource",
                resource,
                "--prompt-file",
                str(effective_prompt_file),
                "--turn-request-id",
                turn_request_id,
                "--ledger",
                str(self.config.turn_ledger),
                "--receipt-out",
                str(receipt_out),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=75, check=False)
            if proc.returncode != 0:
                detail = (proc.stderr or "").strip().replace("\n", " ")[-1200:]
                suffix = f"; detail={detail}" if detail else ""
                raise BrowserlessAutomationHold(
                    f"Browserless continuation failed closed (rc={proc.returncode}{suffix})"
                )
            try:
                return json.loads(proc.stdout.strip().splitlines()[-1])
            except Exception as error:
                raise BrowserlessAutomationConflict(
                    "Browserless continuation returned no receipt"
                ) from error
        finally:
            if transient is not None:
                transient.cleanup()
