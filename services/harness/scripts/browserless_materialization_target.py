#!/usr/bin/env python3
"""SQLite materialization target backed by Browserless rather than local Chromium lifecycle."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

try:
    from browserless_substrate import BrowserlessEndpoint
    from browserless_human_handoff import load_verified_handoff
    from chatgpt_provider_resource import canonical_chatgpt_resource
    from conversation_relay_carrier import CarrierMaterializationRequest, MaterializationStanding
    from sqlite_conversation_materializer import TargetMaterializationObservation
except ModuleNotFoundError:
    from scripts.browserless_substrate import BrowserlessEndpoint
    from scripts.browserless_human_handoff import load_verified_handoff
    from scripts.chatgpt_provider_resource import canonical_chatgpt_resource
    from scripts.conversation_relay_carrier import (
        CarrierMaterializationRequest,
        MaterializationStanding,
    )
    from scripts.sqlite_conversation_materializer import TargetMaterializationObservation


def _digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class BrowserlessMaterializationTarget:
    PRE_EFFECT_BLOCKED_EXIT = 42
    HUMAN_REQUIRED_EXIT = 43

    def __init__(
        self,
        *,
        endpoint: BrowserlessEndpoint,
        state_dir: Path,
        submit_script: Path,
        reconcile_script: Path,
        playwright_python: Path,
        human_resume_script: Path | None = None,
        wait_stable_seconds: int = 150,
        reconnect_ms: int = 60000,
        human_handoff_ms: int | None = None,
        human_handoff_mode: str = "self-hosted-vnc",
        session_timeout_ms: int = 480000,
    ) -> None:
        self.endpoint = endpoint
        self.state_dir = Path(state_dir)
        self.submit_script = Path(submit_script).resolve()
        self.reconcile_script = Path(reconcile_script).resolve()
        self.playwright_python = Path(os.path.abspath(os.fspath(playwright_python)))
        self.human_resume_script = (
            Path(human_resume_script).resolve()
            if human_resume_script is not None
            else Path(__file__).resolve().with_name("playwright_browserless_human_resume.py")
        )
        self.wait_stable_seconds = int(wait_stable_seconds)
        self.reconnect_ms = int(reconnect_ms)
        self.human_handoff_ms = int(
            human_handoff_ms if human_handoff_ms is not None else reconnect_ms
        )
        self.human_handoff_mode = human_handoff_mode
        self.session_timeout_ms = int(session_timeout_ms)
        if self.session_timeout_ms <= 0:
            raise ValueError("Browserless session timeout must be positive")
        if self.human_handoff_mode not in {"self-hosted-vnc", "live-url"}:
            raise ValueError("unsupported Browserless human handoff mode")

    def _paths(self, request: CarrierMaterializationRequest) -> tuple[Path, Path, Path, Path]:
        suffix = hashlib.sha256(request.request_id.encode()).hexdigest()[:24]
        prompt = self.state_dir / "prompts" / f"{suffix}.txt"
        handle = self.state_dir / "handles" / f"{suffix}.json"
        pre_effect = self.state_dir / "pre-effect" / f"{suffix}.json"
        handoff = self.state_dir / "human-handoff" / f"{suffix}.json"
        for path in (prompt, handle, pre_effect, handoff):
            path.parent.mkdir(parents=True, exist_ok=True)
        return prompt, handle, pre_effect, handoff

    @staticmethod
    def _from_handle(
        request: CarrierMaterializationRequest, handle: dict
    ) -> TargetMaterializationObservation:
        if handle.get("effectId") != request.request_id:
            raise RuntimeError("Browserless handle belongs to another request")
        evidence = handle.get("bindingDigest")
        if not isinstance(evidence, str) or not evidence.startswith("sha256:"):
            raise RuntimeError("Browserless handle lacks binding digest")
        raw_resource = handle.get("providerResource")
        if isinstance(raw_resource, str) and raw_resource:
            resource = canonical_chatgpt_resource(raw_resource)
            return TargetMaterializationObservation(
                standing=MaterializationStanding.BOUND,
                provider_conversation_coordinate=resource,
                evidence_digest=evidence,
                detail="Browserless submit observed and provider-bound",
            )
        if handle.get("generationStarted") is True and handle.get("composerCleared") is True:
            return TargetMaterializationObservation(
                standing=MaterializationStanding.SUBMIT_OBSERVED,
                evidence_digest=evidence,
                detail="Browserless submit observed without stable provider coordinate",
            )
        return TargetMaterializationObservation(
            standing=MaterializationStanding.UNKNOWN,
            evidence_digest=evidence,
            detail="Browserless handle does not prove structural submit",
        )

    @staticmethod
    def _human_required(
        request: CarrierMaterializationRequest, handoff_path: Path
    ) -> TargetMaterializationObservation:
        if not handoff_path.is_file():
            return TargetMaterializationObservation(
                standing=MaterializationStanding.UNKNOWN,
                detail="Browserless reported human-required without a durable private handoff receipt",
            )
        handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
        evidence = handoff.get("handoffDigest")
        if (
            handoff.get("effectId") != request.request_id
            or handoff.get("providerEffectAttempted") is not False
            or not isinstance(evidence, str)
            or not evidence.startswith("sha256:")
        ):
            return TargetMaterializationObservation(
                standing=MaterializationStanding.UNKNOWN,
                detail="Browserless human handoff receipt identity mismatch",
            )
        return TargetMaterializationObservation(
            standing=MaterializationStanding.HUMAN_REQUIRED,
            evidence_digest=evidence,
            detail=f"provider admission requires human verification: {handoff.get('blocker') or 'human-required'}",
        )

    @staticmethod
    def _pre_effect_failure(
        request: CarrierMaterializationRequest, pre_effect_path: Path, fallback_digest: str
    ) -> TargetMaterializationObservation:
        if not pre_effect_path.is_file():
            return TargetMaterializationObservation(
                standing=MaterializationStanding.UNKNOWN,
                evidence_digest=fallback_digest,
                detail="Browserless carrier reported pre-effect failure without receipt",
            )
        blocker = json.loads(pre_effect_path.read_text(encoding="utf-8"))
        evidence = blocker.get("evidenceDigest")
        if (
            blocker.get("effectId") != request.request_id
            or blocker.get("providerEffectAttempted") is not False
            or not isinstance(evidence, str)
        ):
            return TargetMaterializationObservation(
                standing=MaterializationStanding.UNKNOWN,
                evidence_digest=fallback_digest,
                detail="Browserless pre-effect receipt identity mismatch",
            )
        return TargetMaterializationObservation(
            standing=MaterializationStanding.PRE_EFFECT_FAILED,
            evidence_digest=evidence,
            detail=f"Browserless/ChatGPT blocked before SEND: {blocker.get('blocker')}",
        )

    def _run_observation(
        self,
        request: CarrierMaterializationRequest,
        cmd: list[str],
        *,
        handle_path: Path,
        pre_effect_path: Path,
        handoff_path: Path,
    ) -> TargetMaterializationObservation:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=max(
                self.wait_stable_seconds + 45,
                self.human_handoff_ms // 1000 + 45,
                self.session_timeout_ms // 1000 + 30,
            ),
            check=False,
        )
        attempts = self.state_dir / "attempts"
        attempts.mkdir(parents=True, exist_ok=True)
        suffix = hashlib.sha256(request.request_id.encode()).hexdigest()[:24]
        meta = {
            "schemaVersion": 1,
            "kind": "ordivon.browserless-submit-attempt",
            "requestId": request.request_id,
            "returnCode": proc.returncode,
            "stdoutDigest": _digest(proc.stdout.encode()),
            "stderrDigest": _digest(proc.stderr.encode()),
            "endpointId": self.endpoint.endpoint_id,
            "endpointIdentityDigest": self.endpoint.identity_digest,
        }
        (attempts / f"{suffix}.json").write_text(json.dumps(meta, sort_keys=True, indent=2) + "\n")
        if proc.returncode == self.HUMAN_REQUIRED_EXIT:
            return self._human_required(request, handoff_path)
        if proc.returncode == self.PRE_EFFECT_BLOCKED_EXIT:
            return self._pre_effect_failure(request, pre_effect_path, meta["stderrDigest"])
        if proc.returncode != 0:
            return TargetMaterializationObservation(
                standing=MaterializationStanding.UNKNOWN,
                evidence_digest=meta["stderrDigest"],
                detail=f"Browserless submit ended without safe completion (rc={proc.returncode})",
            )
        if not handle_path.is_file():
            return TargetMaterializationObservation(
                standing=MaterializationStanding.UNKNOWN,
                detail="Browserless submit returned without durable handle",
            )
        return self._from_handle(request, json.loads(handle_path.read_text(encoding="utf-8")))

    def materialize(
        self, request: CarrierMaterializationRequest
    ) -> TargetMaterializationObservation:
        prompt_path, handle_path, pre_effect_path, handoff_path = self._paths(request)
        raw = request.bootstrap_prompt.encode("utf-8")
        if prompt_path.exists() and prompt_path.read_bytes() != raw:
            raise RuntimeError("frozen Browserless bootstrap bytes changed")
        if not prompt_path.exists():
            prompt_path.write_bytes(raw)
            os.chmod(prompt_path, 0o600)
        cmd = [
            *self.endpoint.exec_prefix,
            str(self.playwright_python),
            str(self.submit_script),
            "--browserless-endpoint",
            self.endpoint.connection_endpoint(timeout_ms=self.session_timeout_ms),
            "--browserless-token-file",
            str(self.endpoint.token_file),
            "--endpoint-id",
            self.endpoint.endpoint_id,
            "--bootstrap-file",
            str(prompt_path),
            "--effect-id",
            request.request_id,
            "--prompt-digest",
            _digest(raw),
            "--handle-out",
            str(handle_path),
            "--pre-effect-out",
            str(pre_effect_path),
            "--human-handoff-out",
            str(handoff_path),
            "--wait-stable-seconds",
            str(self.wait_stable_seconds),
            "--reconnect-ms",
            str(self.reconnect_ms),
            "--human-handoff-ms",
            str(self.human_handoff_ms),
            "--human-handoff-mode",
            self.human_handoff_mode,
        ]
        return self._run_observation(
            request,
            cmd,
            handle_path=handle_path,
            pre_effect_path=pre_effect_path,
            handoff_path=handoff_path,
        )

    def resume_after_human(
        self, request: CarrierMaterializationRequest
    ) -> TargetMaterializationObservation:
        # Self-hosted VNC keeps the session only for the bounded in-process window. A timed-out
        # handoff still proves no SEND, so resume safely re-enters provider admission under the same
        # effect identity and persistent Browserless profile. LiveURL reconnects the exact session.
        if self.human_handoff_mode == "self-hosted-vnc":
            return self.materialize(request)
        prompt_path, handle_path, pre_effect_path, handoff_path = self._paths(request)
        raw = request.bootstrap_prompt.encode("utf-8")
        if not prompt_path.is_file() or prompt_path.read_bytes() != raw:
            raise RuntimeError("frozen Browserless bootstrap is unavailable or changed")
        if not handoff_path.is_file():
            return self.materialize(request)
        handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
        expected = handoff.get("handoffDigest")
        if not isinstance(expected, str) or not expected.startswith("sha256:"):
            raise RuntimeError("human handoff lacks digest")
        cmd = [
            *self.endpoint.exec_prefix,
            str(self.playwright_python),
            str(self.human_resume_script),
            "--handoff",
            str(handoff_path),
            "--expected-handoff-digest",
            expected,
            "--browserless-token-file",
            str(self.endpoint.token_file),
            "--endpoint-id",
            self.endpoint.endpoint_id,
            "--bootstrap-file",
            str(prompt_path),
            "--effect-id",
            request.request_id,
            "--prompt-digest",
            _digest(raw),
            "--handle-out",
            str(handle_path),
            "--pre-effect-out",
            str(pre_effect_path),
            "--human-handoff-out",
            str(handoff_path),
            "--wait-stable-seconds",
            str(self.wait_stable_seconds),
            "--reconnect-ms",
            str(self.reconnect_ms),
            "--human-handoff-ms",
            str(self.human_handoff_ms),
            "--human-handoff-mode",
            self.human_handoff_mode,
        ]
        observation = self._run_observation(
            request,
            cmd,
            handle_path=handle_path,
            pre_effect_path=pre_effect_path,
            handoff_path=handoff_path,
        )
        if observation.standing is MaterializationStanding.PRE_EFFECT_FAILED:
            return self.materialize(request)
        return observation

    def reconcile(self, request: CarrierMaterializationRequest) -> TargetMaterializationObservation:
        _, handle_path, _, handoff_path = self._paths(request)
        if not handle_path.is_file():
            # A private handoff can prove that the process was still on the pre-SEND side when it
            # disappeared. `human-verified-ready` is deliberately excluded: after that marker the
            # process may have crossed SEND before crashing, so the outcome must remain UNKNOWN.
            if handoff_path.is_file():
                try:
                    handoff = load_verified_handoff(handoff_path)
                except Exception:
                    handoff = None
                if (
                    isinstance(handoff, dict)
                    and handoff.get("effectId") == request.request_id
                    and handoff.get("providerEffectAttempted") is False
                    and (
                        handoff.get("sessionActive") is True
                        or handoff.get("sessionState") == "handoff-window-expired"
                    )
                ):
                    return TargetMaterializationObservation(
                        standing=MaterializationStanding.HUMAN_REQUIRED,
                        evidence_digest=handoff.get("handoffDigest"),
                        detail="recovered pre-SEND human-verification handoff after process loss",
                    )
            return TargetMaterializationObservation(
                standing=MaterializationStanding.UNKNOWN,
                detail="no Browserless submit handle or safe pre-SEND handoff evidence available for reconciliation",
            )
        handle = json.loads(handle_path.read_text(encoding="utf-8"))
        current = self._from_handle(request, handle)
        if current.standing is MaterializationStanding.BOUND:
            return current
        reconnect = handle.get("reconnectEndpoint")
        if not isinstance(reconnect, str) or not reconnect:
            return current
        expected = handle.get("bindingDigest")
        out = self.state_dir / "reconciled" / (handle_path.stem + ".json")
        out.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            *self.endpoint.exec_prefix,
            str(self.playwright_python),
            str(self.reconcile_script),
            "--handle",
            str(handle_path),
            "--expected-binding-digest",
            str(expected),
            "--browserless-token-file",
            str(self.endpoint.token_file),
            "--out",
            str(out),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
        if proc.returncode != 0 or not out.is_file():
            return current
        row = json.loads(out.read_text(encoding="utf-8"))
        raw_resource = row.get("providerResource")
        evidence = row.get("bindingDigest")
        if not isinstance(raw_resource, str) or not raw_resource or not isinstance(evidence, str):
            return current
        resource = canonical_chatgpt_resource(raw_resource)
        return TargetMaterializationObservation(
            standing=MaterializationStanding.BOUND,
            provider_conversation_coordinate=resource,
            evidence_digest=evidence,
            detail="Browserless reconnect reconciliation observed provider binding",
        )
