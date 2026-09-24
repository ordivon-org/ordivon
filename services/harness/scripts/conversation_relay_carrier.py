#!/usr/bin/env python3
"""Carrier-neutral materialization contract for ConversationRelay.

The relay owns successor identity and lifecycle semantics. A carrier owns only the mechanical
attempt to obtain/bind a provider conversation and submit the fixed bootstrap. The carrier must
never decide research work, invent a new successor generation, or treat rendered assistant output
as relay state.

This module is effect-free and contains only deterministic request/receipt validation plus a
minimal reconciliation reducer. Browser/P16, another supported UI surface, or a future native
conversation surface may implement the same protocol outside this module.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath
from typing import Protocol


class CarrierConflict(RuntimeError):
    pass


class MaterializationStanding(str, Enum):
    PREPARED = "prepared"
    SUBMIT_OBSERVED = "submit-observed"
    BOUND = "bound"
    READY_CONFIRMED = "ready-confirmed"
    PRE_EFFECT_FAILED = "pre-effect-failed"
    HUMAN_REQUIRED = "human-required"
    UNKNOWN = "unknown"


def _text(value: str, label: str, *, max_bytes: int = 4096) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty and trimmed")
    if len(value.encode("utf-8")) > max_bytes:
        raise ValueError(f"{label} exceeds {max_bytes} UTF-8 bytes")
    return value


def _digest(value: str, label: str) -> str:
    _text(value, label, max_bytes=256)
    if not value.startswith("sha256:") or len(value) != 71:
        raise ValueError(f"{label} must be sha256:<64 lowercase hex>")
    try:
        int(value[7:], 16)
    except ValueError as error:
        raise ValueError(f"{label} is not hexadecimal") from error
    if value[7:] != value[7:].lower():
        raise ValueError(f"{label} must use lowercase hex")
    return value


def _canonical_digest(value: object) -> str:
    import rfc8785

    return "sha256:" + hashlib.sha256(rfc8785.dumps(value)).hexdigest()


@dataclass(frozen=True, slots=True)
class CarrierAttachment:
    staging_relative_path: str
    digest: str
    media_type: str
    presentation_name: str

    def __post_init__(self) -> None:
        _text(self.staging_relative_path, "attachment staging relative path", max_bytes=1024)
        path = PurePosixPath(self.staging_relative_path)
        if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
            raise ValueError("attachment staging path must be a normal relative POSIX path")
        if "\\" in self.staging_relative_path:
            raise ValueError("attachment staging path must use POSIX separators")
        _digest(self.digest, "attachment digest")
        _text(self.media_type, "attachment media type", max_bytes=256)
        if "/" not in self.media_type or any(ch.isspace() for ch in self.media_type):
            raise ValueError("attachment media type must be one MIME type")
        _text(self.presentation_name, "attachment presentation name", max_bytes=255)
        if PurePosixPath(self.presentation_name).name != self.presentation_name:
            raise ValueError("attachment presentation name must be one basename")

    def canonical(self) -> dict[str, str]:
        return {
            "stagingRelativePath": self.staging_relative_path,
            "digest": self.digest,
            "mediaType": self.media_type,
            "presentationName": self.presentation_name,
        }


@dataclass(frozen=True, slots=True)
class CarrierMaterializationRequest:
    request_id: str
    preparation_digest: str
    bootstrap_prompt: str
    attachments: tuple[CarrierAttachment, ...] = ()

    def __post_init__(self) -> None:
        _text(self.request_id, "materialization request identity")
        _digest(self.preparation_digest, "preparation digest")
        _text(self.bootstrap_prompt, "bootstrap prompt", max_bytes=16384)
        if len(self.attachments) > 1:
            raise ValueError("materialization supports at most one attachment")
        if any(not isinstance(item, CarrierAttachment) for item in self.attachments):
            raise ValueError("materialization attachments must use CarrierAttachment")
        paths = [item.staging_relative_path for item in self.attachments]
        names = [item.presentation_name for item in self.attachments]
        if len(paths) != len(set(paths)) or len(names) != len(set(names)):
            raise ValueError("materialization attachment paths and presentation names must be unique")

    @property
    def attachment_digest(self) -> str | None:
        if not self.attachments:
            return None
        return _canonical_digest([item.canonical() for item in self.attachments])

    @property
    def request_digest(self) -> str:
        value = {
            "schemaVersion": 2,
            "kind": "ordivon.conversation-carrier-materialization-request",
            "requestId": self.request_id,
            "preparationDigest": self.preparation_digest,
            "bootstrapPromptDigest": _canonical_digest(self.bootstrap_prompt),
        }
        if self.attachments:
            value["schemaVersion"] = 3
            value["attachments"] = [item.canonical() for item in self.attachments]
        return _canonical_digest(value)



@dataclass(frozen=True, slots=True)
class CarrierMaterializationReceipt:
    request_id: str
    request_digest: str
    standing: MaterializationStanding
    provider_conversation_coordinate: str | None = None
    evidence_digest: str | None = None
    detail: str | None = None

    def __post_init__(self) -> None:
        _text(self.request_id, "materialization request identity")
        _digest(self.request_digest, "materialization request digest")
        if not isinstance(self.standing, MaterializationStanding):
            raise ValueError("materialization standing is invalid")
        if self.provider_conversation_coordinate is not None:
            _text(self.provider_conversation_coordinate, "provider conversation coordinate")
        if self.evidence_digest is not None:
            _digest(self.evidence_digest, "materialization evidence digest")
        if self.detail is not None:
            _text(self.detail, "materialization detail", max_bytes=2048)
        if self.standing is MaterializationStanding.BOUND:
            if self.provider_conversation_coordinate is None or self.evidence_digest is None:
                raise ValueError("BOUND requires provider coordinate and evidence")
        elif self.provider_conversation_coordinate is not None:
            raise ValueError("only BOUND may expose provider conversation coordinate")
        if (
            self.standing
            in {
                MaterializationStanding.SUBMIT_OBSERVED,
                MaterializationStanding.READY_CONFIRMED,
                MaterializationStanding.PRE_EFFECT_FAILED,
                MaterializationStanding.HUMAN_REQUIRED,
            }
            and self.evidence_digest is None
        ):
            raise ValueError(f"{self.standing.value} requires evidence")
        if self.standing is MaterializationStanding.UNKNOWN and self.detail is None:
            raise ValueError("UNKNOWN requires detail")

    @property
    def receipt_digest(self) -> str:
        return _canonical_digest(
            {
                "schemaVersion": 1,
                "kind": "ordivon.conversation-carrier-materialization-receipt",
                "requestId": self.request_id,
                "requestDigest": self.request_digest,
                "standing": self.standing.value,
                "providerConversationCoordinate": self.provider_conversation_coordinate,
                "evidenceDigest": self.evidence_digest,
                "detail": self.detail,
            }
        )


class ConversationSuccessorMaterializer(Protocol):
    """Mechanical carrier protocol; implementations must be idempotent by request_id."""

    def materialize(
        self, request: CarrierMaterializationRequest
    ) -> CarrierMaterializationReceipt: ...

    def reconcile(
        self, request: CarrierMaterializationRequest
    ) -> CarrierMaterializationReceipt: ...


def validate_receipt(
    request: CarrierMaterializationRequest,
    receipt: CarrierMaterializationReceipt,
) -> CarrierMaterializationReceipt:
    if receipt.request_id != request.request_id:
        raise CarrierConflict("carrier receipt belongs to another materialization request")
    if receipt.request_digest != request.request_digest:
        raise CarrierConflict("carrier receipt request digest differs from exact request")
    return receipt


def choose_reconciled_receipt(
    request: CarrierMaterializationRequest,
    first: CarrierMaterializationReceipt,
    reconciled: CarrierMaterializationReceipt,
) -> CarrierMaterializationReceipt:
    """Combine one ambiguous attempt with one reconciliation without redispatch semantics.

    BOUND and PRE_EFFECT_FAILED are terminal. UNKNOWN may advance only by reconciliation to a
    terminal or stronger observed standing. Conflicting terminal claims fail closed.
    """
    first = validate_receipt(request, first)
    reconciled = validate_receipt(request, reconciled)
    terminal = {
        MaterializationStanding.BOUND,
        MaterializationStanding.READY_CONFIRMED,
        MaterializationStanding.PRE_EFFECT_FAILED,
    }
    if first.standing in terminal:
        if reconciled.receipt_digest != first.receipt_digest:
            raise CarrierConflict("terminal materialization receipt changed during reconciliation")
        return first
    if reconciled.standing is MaterializationStanding.PREPARED:
        raise CarrierConflict("reconciliation cannot regress to PREPARED")
    if (
        first.standing is MaterializationStanding.SUBMIT_OBSERVED
        and reconciled.standing is MaterializationStanding.PRE_EFFECT_FAILED
    ):
        raise CarrierConflict("post-submit observation cannot reconcile to pre-effect failure")
    return reconciled
