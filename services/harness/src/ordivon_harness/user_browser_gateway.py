from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .gateway_execution_port import GatewayExecutionPort, GatewayExecutionRequest


def _digest_text(value: str) -> str:
    return 'sha256:' + hashlib.sha256(value.encode('utf-8')).hexdigest()


@dataclass(frozen=True, slots=True)
class UserBrowserGatewayConfig:
    workspace_id: str
    powershell_path: str
    driver_path: str
    proxy_url: str
    linux_stage_root: str
    windows_stage_root: str
    timeout_ms: int = 150_000

    def __post_init__(self) -> None:
        for value, label in (
            (self.workspace_id, 'workspace id'),
            (self.powershell_path, 'PowerShell path'),
            (self.driver_path, 'driver path'),
            (self.proxy_url, 'proxy URL'),
            (self.linux_stage_root, 'Linux stage root'),
            (self.windows_stage_root, 'Windows stage root'),
        ):
            if not value or value != value.strip():
                raise ValueError(f'UserBrowser {label} must be non-empty and trimmed')
        if not self.proxy_url.startswith('http://127.0.0.1:'):
            raise ValueError('UserBrowser proxy must remain loopback HTTP')
        if type(self.timeout_ms) is not int or not 1 <= self.timeout_ms <= 900_000:
            raise ValueError('UserBrowser timeout must be between 1 and 900000 ms')

    def windows_prompt_path(self, prompt_path: str) -> str:
        from pathlib import Path

        root = Path(self.linux_stage_root).resolve(strict=False)
        candidate = Path(prompt_path).resolve(strict=False)
        try:
            relative = candidate.relative_to(root)
        except ValueError as error:
            raise ValueError('UserBrowser prompt path is outside the configured staging root') from error
        suffix = '\\'.join(relative.parts)
        return self.windows_stage_root.rstrip('\\/') + ('\\' + suffix if suffix else '')


class UserBrowserGatewayController:
    def __init__(self, port: GatewayExecutionPort, config: UserBrowserGatewayConfig) -> None:
        self.port = port
        self.config = config

    @staticmethod
    def _request_id(
        mode: str,
        effect_id: str,
        request_digest: str,
        prompt_digest: str,
        attachment_manifest_digest: str | None = None,
    ) -> str:
        parts = [mode, effect_id, request_digest, prompt_digest]
        if attachment_manifest_digest is not None:
            parts.append(attachment_manifest_digest)
        suffix = _digest_text('|'.join(parts))[7:39]
        return f'user-browser:{mode}:{suffix}'

    @staticmethod
    def _parse_payload(raw: str, *, effect_id: str) -> dict:
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if not lines:
            raise RuntimeError('Windows user-browser execution returned no JSON receipt')
        try:
            payload = json.loads(lines[-1])
        except json.JSONDecodeError as error:
            raise RuntimeError('Windows user-browser execution returned invalid JSON') from error
        if not isinstance(payload, dict):
            raise RuntimeError('Windows user-browser receipt must be an object')
        if payload.get('kind') != 'ordivon.windows-user-browser-attempt':
            raise RuntimeError('Windows user-browser receipt kind is invalid')
        if payload.get('effectId') != effect_id:
            raise RuntimeError('Windows user-browser effect identity mismatch')
        if payload.get('schemaVersion') != 1:
            raise RuntimeError('Windows user-browser receipt schema is invalid')
        standing = payload.get('standing')
        if standing not in {
            'bound', 'submit-observed', 'pre-effect-failed', 'human-required', 'unknown'
        }:
            raise RuntimeError('Windows user-browser standing is invalid')
        attempted = payload.get('providerEffectAttempted')
        if not isinstance(attempted, bool):
            raise RuntimeError('Windows user-browser receipt omitted providerEffectAttempted')
        evidence = payload.get('evidenceDigest')
        if not isinstance(evidence, str) or not evidence.startswith('sha256:') or len(evidence) != 71:
            raise RuntimeError('Windows user-browser evidence digest is invalid')
        detail = payload.get('detail')
        if not isinstance(detail, str) or not detail or detail != detail.strip():
            raise RuntimeError('Windows user-browser detail is invalid')
        resource = payload.get('providerResource')
        if standing == 'bound':
            if not attempted or not isinstance(resource, str) or not resource.startswith('https://chatgpt.com/c/'):
                raise RuntimeError('Windows user-browser BOUND receipt is incomplete')
        elif resource is not None:
            raise RuntimeError('Only BOUND user-browser receipt may expose providerResource')
        if standing in {'pre-effect-failed', 'human-required'} and attempted:
            raise RuntimeError('Pre-effect user-browser receipt cannot report SEND attempted')
        return payload

    def _active_user_admission(self) -> tuple[bool, str, str, tuple[str, ...]]:
        try:
            standing = self.port.capability_standing('execution.windows')
        except Exception:
            detail = 'execution.windows capability projection unavailable; active_user effect held'
            evidence = _digest_text(
                json.dumps(
                    {
                        'capability': 'execution.windows',
                        'requiredContext': 'active_user',
                        'standing': 'PROJECTION_UNAVAILABLE',
                    },
                    sort_keys=True,
                    separators=(',', ':'),
                )
            )
            return False, evidence, detail, ()
        if standing.supports_context('active_user'):
            return True, standing.projection_digest, 'active_user available', standing.contexts
        detail = 'execution.windows active_user context unavailable; provider effect held pre-effect'
        evidence = _digest_text(
            json.dumps(
                {
                    'available': standing.available,
                    'capability': standing.capability,
                    'configured': standing.configured,
                    'contexts': list(standing.contexts),
                    'projectionDigest': standing.projection_digest,
                    'requiredContext': 'active_user',
                },
                sort_keys=True,
                separators=(',', ':'),
            )
        )
        return False, evidence, detail, standing.contexts

    def _run(
        self,
        mode: str,
        *,
        effect_id: str,
        request_digest: str,
        prompt_path: str,
        prompt_digest: str,
        attachment_manifest_path: str | None = None,
        attachment_manifest_digest: str | None = None,
    ) -> dict:
        if mode == 'materialize':
            admitted, evidence, detail, contexts = self._active_user_admission()
            if not admitted:
                return {
                    'schemaVersion': 1,
                    'kind': 'ordivon.windows-user-browser-attempt',
                    'effectId': effect_id,
                    'standing': 'pre-effect-failed',
                    'providerResource': None,
                    'evidenceDigest': evidence,
                    'detail': detail,
                    'providerEffectAttempted': False,
                    'requiredContext': 'active_user',
                    'observedContexts': list(contexts),
                }
        args_list = [
            '-NoProfile',
            '-NonInteractive',
            '-File',
            self.config.driver_path,
            '-Mode',
            mode,
            '-EffectId',
            effect_id,
            '-RequestDigest',
            request_digest,
            '-PromptPath',
            self.config.windows_prompt_path(prompt_path),
            '-PromptDigest',
            prompt_digest,
            '-ProxyUrl',
            self.config.proxy_url,
        ]
        if (attachment_manifest_path is None) != (attachment_manifest_digest is None):
            raise ValueError('attachment manifest path and digest must be supplied together')
        if attachment_manifest_path is not None and attachment_manifest_digest is not None:
            args_list.extend(
                [
                    '-AttachmentManifestPath',
                    self.config.windows_prompt_path(attachment_manifest_path),
                    '-AttachmentManifestDigest',
                    attachment_manifest_digest,
                    '-StageRoot',
                    self.config.windows_stage_root,
                ]
            )
        args = tuple(args_list)
        result = self.port.execute(
            GatewayExecutionRequest(
                capability='execution.windows',
                request_id=self._request_id(
                    mode,
                    effect_id,
                    request_digest,
                    prompt_digest,
                    attachment_manifest_digest,
                ),
                workspace_id=self.config.workspace_id,
                executable=self.config.powershell_path,
                args=args,
                cwd_relative='.',
                context='active_user',
                timeout_ms=self.config.timeout_ms,
            )
        )
        if result.recovery_required:
            raise RuntimeError('Windows user-browser execution requires Runtime recovery')
        if result.exit_code != 0:
            raise RuntimeError(f'Windows user-browser execution failed with exit code {result.exit_code}')
        return self._parse_payload(self.port.read_stdout(result), effect_id=effect_id)


    @staticmethod
    def _parse_classification(raw: str) -> dict:
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if not lines:
            raise RuntimeError('Windows user-browser classification returned no JSON receipt')
        try:
            payload = json.loads(lines[-1])
        except json.JSONDecodeError as error:
            raise RuntimeError('Windows user-browser classification returned invalid JSON') from error
        if not isinstance(payload, dict):
            raise RuntimeError('Windows user-browser classification must be an object')
        if payload.get('schemaVersion') != 1 or payload.get('kind') != 'ordivon.windows-user-browser-classification':
            raise RuntimeError('Windows user-browser classification identity is invalid')
        if payload.get('standing') not in {
            'READY',
            'AUTH_REQUIRED',
            'CHALLENGE_GATED',
            'BUSY',
            'CONTEXT_UNAVAILABLE',
            'UNKNOWN',
        }:
            raise RuntimeError('Windows user-browser classification standing is invalid')
        if payload.get('providerEffectAttempted') is not False:
            raise RuntimeError('Windows user-browser classification must remain pre-effect')
        detail = payload.get('detail')
        if not isinstance(detail, str) or not detail or detail != detail.strip():
            raise RuntimeError('Windows user-browser classification detail is invalid')
        return payload

    def classify(self) -> dict:
        admitted, evidence, detail, contexts = self._active_user_admission()
        if not admitted:
            return {
                'schemaVersion': 1,
                'kind': 'ordivon.windows-user-browser-classification',
                'standing': 'CONTEXT_UNAVAILABLE',
                'detail': detail,
                'providerEffectAttempted': False,
                'requiredContext': 'active_user',
                'observedContexts': list(contexts),
                'capabilityEvidenceDigest': evidence,
            }
        request_id = 'user-browser:classify:' + _digest_text(
            '|'.join((self.config.workspace_id, self.config.driver_path, self.config.proxy_url))
        )[7:39]
        result = self.port.execute(
            GatewayExecutionRequest(
                capability='execution.windows',
                request_id=request_id,
                workspace_id=self.config.workspace_id,
                executable=self.config.powershell_path,
                args=(
                    '-NoProfile','-NonInteractive','-File',self.config.driver_path,
                    '-Mode','classify','-ProxyUrl',self.config.proxy_url,
                ),
                cwd_relative='.',
                context='active_user',
                timeout_ms=self.config.timeout_ms,
            )
        )
        if result.recovery_required:
            raise RuntimeError('Windows user-browser classification requires Runtime recovery')
        if result.exit_code != 0:
            raise RuntimeError(f'Windows user-browser classification failed with exit code {result.exit_code}')
        return self._parse_classification(self.port.read_stdout(result))

    def materialize(self, **kwargs) -> dict:
        return self._run('materialize', **kwargs)

    def reconcile(self, **kwargs) -> dict:
        return self._run('reconcile', **kwargs)


__all__ = ['UserBrowserGatewayConfig', 'UserBrowserGatewayController']
