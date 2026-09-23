#!/usr/bin/env python3
"""Carrier-neutral materialization target for an already-authorized Windows user browser."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

try:
    from chatgpt_provider_resource import canonical_chatgpt_resource
    from conversation_relay_carrier import CarrierMaterializationRequest, MaterializationStanding
    from sqlite_conversation_materializer import TargetMaterializationObservation
except ModuleNotFoundError:
    from scripts.chatgpt_provider_resource import canonical_chatgpt_resource
    from scripts.conversation_relay_carrier import (
        CarrierMaterializationRequest,
        MaterializationStanding,
    )
    from scripts.sqlite_conversation_materializer import TargetMaterializationObservation


def _digest(raw: bytes) -> str:
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class UserBrowserAttemptResult:
    standing: str
    provider_resource: str | None
    evidence_digest: str
    detail: str
    provider_effect_attempted: bool

    def __post_init__(self) -> None:
        allowed = {
            MaterializationStanding.BOUND.value,
            MaterializationStanding.SUBMIT_OBSERVED.value,
            MaterializationStanding.PRE_EFFECT_FAILED.value,
            MaterializationStanding.HUMAN_REQUIRED.value,
            MaterializationStanding.UNKNOWN.value,
        }
        if self.standing not in allowed:
            raise ValueError('unsupported user-browser materialization standing')
        if not self.evidence_digest.startswith('sha256:') or len(self.evidence_digest) != 71:
            raise ValueError('user-browser evidence digest must be canonical SHA-256')
        if not self.detail or self.detail != self.detail.strip():
            raise ValueError('user-browser detail must be non-empty and trimmed')
        if self.standing == MaterializationStanding.BOUND.value:
            if not self.provider_effect_attempted or self.provider_resource is None:
                raise ValueError('BOUND requires an attempted effect and provider resource')
        elif self.provider_resource is not None:
            raise ValueError('only BOUND may expose a provider resource')
        if self.standing in {
            MaterializationStanding.PRE_EFFECT_FAILED.value,
            MaterializationStanding.HUMAN_REQUIRED.value,
        } and self.provider_effect_attempted:
            raise ValueError('pre-effect/human-required standing cannot follow provider SEND')


class UserBrowserController(Protocol):
    def materialize(self, **kwargs) -> UserBrowserAttemptResult: ...
    def reconcile(self, **kwargs) -> UserBrowserAttemptResult: ...


class WindowsUserBrowserMaterializationTarget:
    def __init__(self, *, state_dir: Path, controller: UserBrowserController) -> None:
        self.state_dir = Path(state_dir)
        self.controller = controller

    @staticmethod
    def prompt_digest(request: CarrierMaterializationRequest) -> str:
        return _digest(request.bootstrap_prompt.encode('utf-8'))

    def _prompt_path(self, request: CarrierMaterializationRequest) -> Path:
        suffix = hashlib.sha256(request.request_id.encode('utf-8')).hexdigest()[:24]
        return self.state_dir / 'user-browser' / 'prompts' / f'{suffix}.txt'

    def _freeze_prompt(self, request: CarrierMaterializationRequest) -> Path:
        path = self._prompt_path(request)
        raw = request.bootstrap_prompt.encode('utf-8')
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_bytes() != raw:
                raise RuntimeError('frozen user-browser bootstrap bytes changed')
        else:
            path.write_bytes(raw)
            os.chmod(path, 0o600)
        return path

    def _attachment_manifest_path(self, request: CarrierMaterializationRequest) -> Path:
        suffix = hashlib.sha256(request.request_id.encode('utf-8')).hexdigest()[:24]
        return self.state_dir / 'user-browser' / 'attachment-manifests' / f'{suffix}.json'

    def _freeze_attachment_manifest(
        self, request: CarrierMaterializationRequest
    ) -> tuple[Path | None, str | None]:
        if not request.attachments:
            return None, None
        root = self.state_dir.resolve(strict=False)
        total = 0
        for attachment in request.attachments:
            candidate = (root / attachment.staging_relative_path).resolve(strict=True)
            try:
                candidate.relative_to(root)
            except ValueError as error:
                raise RuntimeError('attachment escapes configured user-browser staging root') from error
            if not candidate.is_file() or candidate.is_symlink():
                raise RuntimeError('attachment must be one regular non-symlink staging file')
            size = candidate.stat().st_size
            total += size
            if size > 100 * 1024 * 1024 or total > 200 * 1024 * 1024:
                raise RuntimeError('attachment set exceeds user-browser size limit')
            observed = _digest(candidate.read_bytes())
            if observed != attachment.digest:
                raise RuntimeError('staged attachment digest differs from materialization request')
        value = {
            'schemaVersion': 1,
            'kind': 'ordivon.user-browser-attachment-manifest',
            'attachmentSetDigest': request.attachment_digest,
            'attachments': [item.canonical() for item in request.attachments],
        }
        raw = json.dumps(
            value, sort_keys=True, separators=(',', ':'), ensure_ascii=False
        ).encode('utf-8')
        path = self._attachment_manifest_path(request)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_bytes() != raw:
                raise RuntimeError('frozen user-browser attachment manifest changed')
        else:
            path.write_bytes(raw)
            os.chmod(path, 0o600)
        return path, _digest(raw)

    @staticmethod
    def _coerce_result(result) -> UserBrowserAttemptResult:
        if isinstance(result, UserBrowserAttemptResult):
            return result
        if isinstance(result, dict):
            return UserBrowserAttemptResult(
                standing=result.get('standing'),
                provider_resource=result.get('providerResource'),
                evidence_digest=result.get('evidenceDigest'),
                detail=result.get('detail'),
                provider_effect_attempted=result.get('providerEffectAttempted'),
            )
        raise TypeError('user-browser controller returned an unsupported receipt type')

    @classmethod
    def _observation(cls, result) -> TargetMaterializationObservation:
        value = cls._coerce_result(result)
        standing = MaterializationStanding(value.standing)
        resource = (
            canonical_chatgpt_resource(value.provider_resource)
            if value.provider_resource is not None
            else None
        )
        return TargetMaterializationObservation(
            standing=standing,
            provider_conversation_coordinate=resource,
            evidence_digest=value.evidence_digest,
            detail=value.detail,
        )

    def _kwargs(self, request: CarrierMaterializationRequest) -> dict:
        prompt = self._freeze_prompt(request)
        manifest, manifest_digest = self._freeze_attachment_manifest(request)
        return {
            'effect_id': request.request_id,
            'request_digest': request.request_digest,
            'prompt_path': str(prompt),
            'prompt_digest': self.prompt_digest(request),
            'attachment_manifest_path': str(manifest) if manifest is not None else None,
            'attachment_manifest_digest': manifest_digest,
        }

    def materialize(self, request: CarrierMaterializationRequest) -> TargetMaterializationObservation:
        return self._observation(self.controller.materialize(**self._kwargs(request)))

    def reconcile(self, request: CarrierMaterializationRequest) -> TargetMaterializationObservation:
        return self._observation(self.controller.reconcile(**self._kwargs(request)))

    def resume_after_human(
        self, request: CarrierMaterializationRequest
    ) -> TargetMaterializationObservation:
        raise RuntimeError('Windows user-browser carrier does not implement blind human-resume')
