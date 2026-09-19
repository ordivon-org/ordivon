from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import rfc8785

from agent_service.slice1 import AgentRevision, ProviderObservation


class CarrierProfileError(ValueError):
    pass


class CarrierCommandError(RuntimeError):
    pass


class CarrierRetireUnsupported(RuntimeError):
    pass


@dataclass(frozen=True)
class AgentAutomationProfile:
    campaign_id: str
    agent_id: str
    shared_prompt: str
    role_card: str

    @classmethod
    def from_revision(cls, revision: AgentRevision) -> "AgentAutomationProfile":
        raw = revision.spec.get("carrier")
        if not isinstance(raw, dict):
            raise CarrierProfileError("AgentRevision requires carrier profile")
        if raw.get("kind") != "agent-automation-browserless":
            raise CarrierProfileError("unsupported carrier kind")
        required = {"kind", "campaignId", "agentId", "sharedPrompt", "roleCard"}
        if set(raw) != required:
            raise CarrierProfileError("agent-automation carrier profile has unexpected fields")
        values = [raw["campaignId"], raw["agentId"], raw["sharedPrompt"], raw["roleCard"]]
        if any(not isinstance(v, str) or not v.strip() or v != v.strip() for v in values):
            raise CarrierProfileError("agent-automation carrier profile fields must be trimmed strings")
        return cls(
            campaign_id=raw["campaignId"],
            agent_id=raw["agentId"],
            shared_prompt=raw["sharedPrompt"],
            role_card=raw["roleCard"],
        )

    def campaign_spec(self) -> dict:
        return {
            "campaignId": self.campaign_id,
            "sharedPrompt": self.shared_prompt,
            "roster": [{"agentId": self.agent_id, "roleCard": self.role_card}],
        }


CommandRunner = Callable[[list[str]], dict]
RevisionResolver = Callable[[str], AgentRevision]


def _canonical_bytes(value: Any) -> bytes:
    return rfc8785.dumps(value)


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def _subprocess_runner(argv: list[str]) -> dict:
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=60, check=False)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().replace("\n", " ")[-1200:]
        raise CarrierCommandError(f"carrier command failed rc={proc.returncode}: {detail}")
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise CarrierCommandError("carrier command returned no machine-readable result")
    try:
        value = json.loads(lines[-1])
    except json.JSONDecodeError as error:
        raise CarrierCommandError("carrier command returned invalid JSON") from error
    if not isinstance(value, dict):
        raise CarrierCommandError("carrier command result must be a JSON object")
    return value


class AgentAutomationCarrierAdapter:
    """Bind Agent Service placement to the Workstation-stable Agent Automation carrier.

    This adapter understands only the existing public operator surface:
    `census` and `reconcile`. Browserless and Temporal remain behind that surface.
    """

    def __init__(
        self,
        *,
        revision_resolver: RevisionResolver,
        state_root: Path,
        executable: Path = Path("/root/tools/bin/agent-automation"),
        command_runner: CommandRunner = _subprocess_runner,
    ) -> None:
        self._revision_resolver = revision_resolver
        self._state_root = Path(state_root)
        self._spec_root = self._state_root / "carrier-specs" / "agent-automation"
        self._binding_root = self._state_root / "carrier-bindings" / "agent-automation"
        self._executable = Path(executable)
        self._run = command_runner

    def _profile(self, revision_id: str) -> AgentAutomationProfile:
        revision = self._revision_resolver(revision_id)
        if revision.id != revision_id:
            raise CarrierProfileError("revision resolver returned mismatched identity")
        return AgentAutomationProfile.from_revision(revision)

    def _spec_path(self, revision_id: str, profile: AgentAutomationProfile) -> Path:
        raw = _canonical_bytes(profile.campaign_spec())
        digest = hashlib.sha256(raw).hexdigest()
        path = self._spec_root / f"{revision_id}-{digest[:24]}.json"
        self._spec_root.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_bytes() != raw:
                raise CarrierProfileError("frozen carrier spec bytes changed")
        else:
            path.write_bytes(raw)
            os.chmod(path, 0o600)
        return path

    def _binding_path(self, placement_id: str) -> Path:
        if not isinstance(placement_id, str) or not placement_id.strip() or placement_id != placement_id.strip():
            raise CarrierProfileError("placement_id must be a trimmed non-empty string")
        suffix = hashlib.sha256(placement_id.encode("utf-8")).hexdigest()
        return self._binding_root / f"{suffix}.json"

    def bind_placement(self, placement_id: str, revision_id: str) -> None:
        profile = self._profile(revision_id)
        self._spec_path(revision_id, profile)
        path = self._binding_path(placement_id)
        value = {"placementId": placement_id, "revisionId": revision_id}
        raw = _canonical_bytes(value)
        self._binding_root.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_bytes() != raw:
                raise CarrierProfileError("placement is already bound to a different revision")
            return
        path.write_bytes(raw)
        os.chmod(path, 0o600)

    def _binding(self, placement_id: str) -> tuple[str, AgentAutomationProfile, Path]:
        path = self._binding_path(placement_id)
        if not path.is_file():
            raise CarrierProfileError("placement has no durable carrier binding")
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("placementId") != placement_id or not isinstance(value.get("revisionId"), str):
            raise CarrierProfileError("placement binding is malformed or mismatched")
        revision_id = value["revisionId"]
        profile = self._profile(revision_id)
        return revision_id, profile, self._spec_path(revision_id, profile)

    def _census(self, profile: AgentAutomationProfile, spec_path: Path) -> tuple[dict, dict]:
        value = self._run([str(self._executable), "census", "--spec", str(spec_path)])
        if value.get("campaignId") != profile.campaign_id:
            raise CarrierCommandError("carrier census campaign identity mismatch")
        rows = value.get("materializations")
        if not isinstance(rows, list):
            raise CarrierCommandError("carrier census has no materialization list")
        matches = [row for row in rows if isinstance(row, dict) and row.get("agentId") == profile.agent_id]
        if len(matches) != 1:
            raise CarrierCommandError("carrier census does not identify exactly one agent materialization")
        return value, matches[0]

    def ensure(self, placement_id: str, agent_instance_id: str, revision_id: str) -> None:
        del agent_instance_id
        self.bind_placement(placement_id, revision_id)
        profile = self._profile(revision_id)
        spec_path = self._spec_path(revision_id, profile)
        _, row = self._census(profile, spec_path)
        standing = row.get("materializationStanding")
        if standing in {"bound", "human-required", "ready-confirmed"}:
            return
        if standing in {None, "pre-effect-failed", "unknown", "submit-observed"}:
            self._run(
                [
                    str(self._executable),
                    "reconcile",
                    "--spec",
                    str(spec_path),
                    "--agent-id",
                    profile.agent_id,
                ]
            )
            return
        raise CarrierCommandError(f"unsupported carrier standing: {standing!r}")

    def retire(self, placement_id: str, agent_instance_id: str) -> None:
        del placement_id, agent_instance_id
        raise CarrierRetireUnsupported(
            "current Workstation Agent Automation surface does not own provider conversation retirement"
        )

    def observe(self, placement_id: str) -> ProviderObservation:
        _, profile, spec_path = self._binding(placement_id)
        census, row = self._census(profile, spec_path)
        standing = row.get("materializationStanding")
        provider_resource = row.get("providerResource")
        state = {
            None: "UNRECORDED",
            "prepared": "PROVISIONING",
            "unknown": "AMBIGUOUS",
            "submit-observed": "AMBIGUOUS",
            "pre-effect-failed": "PRE_EFFECT_FAILED",
            "human-required": "HUMAN_REQUIRED",
            "bound": "READY",
            "ready-confirmed": "READY",
        }.get(standing)
        if state is None:
            raise CarrierCommandError(f"unsupported carrier standing: {standing!r}")
        evidence = {
            "campaignId": profile.campaign_id,
            "agentId": profile.agent_id,
            "standing": standing,
            "providerResource": provider_resource,
            "censusDigest": _digest(census),
        }
        return ProviderObservation(
            placement_id=placement_id,
            state=state,
            evidence_ref="agent-automation:census:" + _digest(evidence),
        )
