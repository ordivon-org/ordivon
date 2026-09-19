#!/usr/bin/env python3
"""Content-addressed registry for current CampaignSpec v2 objects only."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import rfc8785
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

try:
    from campaign_materialization import CampaignLaunchSpec
except ModuleNotFoundError:
    from scripts.campaign_materialization import CampaignLaunchSpec


class AgentAutomationRegistryError(RuntimeError):
    pass


ROOT = Path(__file__).resolve().parents[1]
CURRENT_SCHEMA_PATH = ROOT / "schemas" / "agent-automation" / "campaign-spec-v2.schema.json"
CURRENT_MEDIA_TYPE = "application/vnd.ordivon.agent-campaign.v2+json"
CURRENT_SCHEMA_ID = "urn:ordivon:schema:agent-campaign-spec:2"


def _load_current_schema() -> dict[str, Any]:
    try:
        value = json.loads(CURRENT_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(value)
    except Exception as error:
        raise AgentAutomationRegistryError(
            f"CampaignSpec JSON Schema is unavailable or invalid: {type(error).__name__}: {error}"
        ) from error
    if value.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise AgentAutomationRegistryError(
            "CampaignSpec schema must declare JSON Schema Draft 2020-12"
        )
    if value.get("$id") != CURRENT_SCHEMA_ID:
        raise AgentAutomationRegistryError("CampaignSpec schema $id changed unexpectedly")
    return value


_CURRENT_SCHEMA = _load_current_schema()
_CURRENT_VALIDATOR = Draft202012Validator(_CURRENT_SCHEMA)


def _validate_current(value: dict[str, Any]) -> None:
    errors = sorted(
        _CURRENT_VALIDATOR.iter_errors(value), key=lambda error: list(error.absolute_path)
    )
    if not errors:
        return
    error: ValidationError = errors[0]
    path = "/" + "/".join(str(part) for part in error.absolute_path) if error.absolute_path else "/"
    raise AgentAutomationRegistryError(
        f"CampaignSpec JSON Schema validation failed at {path}: {error.message}"
    )


def _jcs_bytes(value: dict[str, Any]) -> bytes:
    try:
        return rfc8785.dumps(value)
    except Exception as error:
        raise AgentAutomationRegistryError(
            f"RFC 8785 canonicalization failed: {type(error).__name__}: {error}"
        ) from error


def _sha256_descriptor(raw: bytes) -> dict[str, Any]:
    return {
        "mediaType": CURRENT_MEDIA_TYPE,
        "digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "size": len(raw),
    }


def _write_atomic_private(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def current_spec_dict(spec: CampaignLaunchSpec) -> dict[str, Any]:
    return {
        "campaignId": spec.campaign_id,
        "sharedPrompt": spec.shared_prompt,
        "roster": [{"agentId": role.agent_id, "roleCard": role.role_card} for role in spec.roster],
    }


class CampaignRegistry:
    PREFIX = "sha256:"

    def __init__(self, state_root: Path) -> None:
        self.root = Path(state_root) / "campaign-registry"
        self.blob_root = self.root / "blobs" / "sha256"
        self.blob_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _digest_hex(value: str) -> str:
        if len(value) != 64 or value != value.lower():
            raise AgentAutomationRegistryError(
                "campaignRef must contain one lowercase SHA-256 digest"
            )
        try:
            int(value, 16)
        except ValueError as error:
            raise AgentAutomationRegistryError("campaignRef digest is not hexadecimal") from error
        return value

    @classmethod
    def _parse_ref(cls, campaign_ref: str) -> str:
        if not isinstance(campaign_ref, str) or not campaign_ref.startswith(cls.PREFIX):
            raise AgentAutomationRegistryError("campaignRef must be sha256:<digest>")
        return cls._digest_hex(campaign_ref.removeprefix(cls.PREFIX))

    @staticmethod
    def _registration_view(
        spec: CampaignLaunchSpec, *, campaign_ref: str, disposition: str, descriptor: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "campaignRef": campaign_ref,
            "campaignId": spec.campaign_id,
            "requested": len(spec.roster),
            "disposition": disposition,
            "schema": CURRENT_SCHEMA_ID,
            "canonicalization": "RFC8785",
            "descriptor": descriptor,
        }

    def register(self, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise AgentAutomationRegistryError("CampaignSpec must be a JSON object")
        _validate_current(value)
        try:
            spec = CampaignLaunchSpec.from_dict(value)
        except Exception as error:
            raise AgentAutomationRegistryError(
                f"CampaignSpec domain validation failed: {type(error).__name__}: {error}"
            ) from error
        normalized = current_spec_dict(spec)
        _validate_current(normalized)
        raw = _jcs_bytes(normalized)
        descriptor = _sha256_descriptor(raw)
        digest_hex = descriptor["digest"].removeprefix("sha256:")
        path = self.blob_root / digest_hex
        if path.exists():
            if path.is_symlink() or not path.is_file():
                raise AgentAutomationRegistryError("CampaignSpec CAS target is not a regular file")
            if path.read_bytes() != raw:
                raise AgentAutomationRegistryError(
                    "CampaignSpec descriptor collides with different bytes"
                )
            disposition = "existing"
        else:
            _write_atomic_private(path, raw)
            disposition = "created"
        self._resolve(digest_hex)
        return self._registration_view(
            spec, campaign_ref=descriptor["digest"], disposition=disposition, descriptor=descriptor
        )

    def _resolve(self, digest_hex: str) -> Path:
        path = self.blob_root / digest_hex
        if not path.is_file() or path.is_symlink():
            raise AgentAutomationRegistryError("campaignRef is not registered")
        raw = path.read_bytes()
        descriptor = _sha256_descriptor(raw)
        if descriptor["digest"] != "sha256:" + digest_hex:
            raise AgentAutomationRegistryError(
                "CampaignSpec OCI descriptor digest no longer matches content"
            )
        try:
            value = json.loads(raw)
        except Exception as error:
            raise AgentAutomationRegistryError(
                f"registered CampaignSpec JSON is unreadable: {type(error).__name__}: {error}"
            ) from error
        _validate_current(value)
        if _jcs_bytes(value) != raw:
            raise AgentAutomationRegistryError(
                "registered CampaignSpec bytes are not RFC 8785 canonical JSON"
            )
        try:
            spec = CampaignLaunchSpec.from_dict(value)
        except Exception as error:
            raise AgentAutomationRegistryError(
                f"registered CampaignSpec domain validation failed: {type(error).__name__}: {error}"
            ) from error
        if current_spec_dict(spec) != value:
            raise AgentAutomationRegistryError(
                "registered CampaignSpec is not in normalized domain form"
            )
        return path

    def resolve(self, campaign_ref: str) -> Path:
        return self._resolve(self._parse_ref(campaign_ref))

    def inspect(self, campaign_ref: str) -> dict[str, Any]:
        digest_hex = self._parse_ref(campaign_ref)
        path = self._resolve(digest_hex)
        spec = CampaignLaunchSpec.from_dict(json.loads(path.read_text(encoding="utf-8")))
        return self._registration_view(
            spec,
            campaign_ref=campaign_ref,
            disposition="observed",
            descriptor=_sha256_descriptor(path.read_bytes()),
        )

    def list_registered(self) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        issues: list[dict[str, str]] = []
        for path in sorted(self.blob_root.iterdir()):
            if not path.is_file() or path.is_symlink():
                continue
            ref = self.PREFIX + path.name
            try:
                rows.append(self.inspect(ref))
            except Exception as error:
                issues.append({"campaignRef": ref, "error": f"{type(error).__name__}: {error}"})
        return {
            "schemaVersion": 1,
            "kind": "ordivon.agent-automation-campaign-registry-census",
            "registered": len(rows),
            "campaigns": rows,
            "issues": issues,
        }
