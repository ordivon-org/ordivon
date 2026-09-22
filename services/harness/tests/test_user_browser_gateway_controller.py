from __future__ import annotations

import json
from pathlib import Path

import pytest

from ordivon_harness.gateway_execution_port import GatewayExecutionResult
from ordivon_harness.user_browser_gateway import (
    UserBrowserGatewayConfig,
    UserBrowserGatewayController,
)


class FakePort:
    def __init__(self, payload: dict):
        self.payload = payload
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return GatewayExecutionResult(
            operation_ref='ordivon-exec:v1:runtime.windows:job-1',
            native_id='job-1',
            state='succeeded',
            exit_code=0,
            artifact_ids=('attempt-1.stdout',),
            recovery_required=False,
        )

    def read_stdout(self, _result):
        return json.dumps(self.payload, sort_keys=True) + '\n'


def config():
    return UserBrowserGatewayConfig(
        workspace_id='ws-user-browser-prod',
        powershell_path=r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
        driver_path=r'C:\ProgramData\Ordivon\chat-ingress\windows_user_browser_chatgpt.ps1',
        proxy_url='http://127.0.0.1:19081',
        linux_stage_root='/mnt/c/ProgramData/Ordivon/chat-ingress',
        windows_stage_root=r'C:\ProgramData\Ordivon\chat-ingress',
    )


def test_materialize_is_fixed_to_active_user_windows_execution():
    payload = {
        'schemaVersion': 1,
        'kind': 'ordivon.windows-user-browser-attempt',
        'effectId': 'effect-1',
        'standing': 'bound',
        'providerResource': 'https://chatgpt.com/c/abc',
        'evidenceDigest': 'sha256:' + '2' * 64,
        'detail': 'provider-bound',
        'providerEffectAttempted': True,
    }
    port = FakePort(payload)
    controller = UserBrowserGatewayController(port, config())
    result = controller.materialize(
        effect_id='effect-1',
        request_digest='sha256:' + '1' * 64,
        prompt_path='/mnt/c/ProgramData/Ordivon/chat-ingress/prompts/p.txt',
        prompt_digest='sha256:' + '3' * 64,
    )
    assert result == payload
    req = port.requests[0]
    assert req.capability == 'execution.windows'
    assert req.context == 'active_user'
    assert req.workspace_id == 'ws-user-browser-prod'
    assert req.executable.endswith('powershell.exe')
    assert '-Mode' in req.args and 'materialize' in req.args
    i=req.args.index('-PromptPath')
    assert req.args[i+1] == r'C:\ProgramData\Ordivon\chat-ingress\prompts\p.txt'
    assert req.request_id.startswith('user-browser:materialize:')


def test_effect_identity_mismatch_fails_closed():
    payload = {
        'schemaVersion': 1,
        'kind': 'ordivon.windows-user-browser-attempt',
        'effectId': 'other-effect',
        'standing': 'pre-effect-failed',
        'providerResource': None,
        'evidenceDigest': 'sha256:' + '2' * 64,
        'detail': 'hold',
        'providerEffectAttempted': False,
    }
    controller = UserBrowserGatewayController(FakePort(payload), config())
    with pytest.raises(RuntimeError, match='effect identity'):
        controller.materialize(
            effect_id='effect-1',
            request_digest='sha256:' + '1' * 64,
            prompt_path='/mnt/c/ProgramData/Ordivon/chat-ingress/prompts/p.txt',
            prompt_digest='sha256:' + '3' * 64,
        )


def test_windows_driver_declares_no_cookie_or_challenge_bypass_surface():
    script = (Path(__file__).resolve().parents[1] / 'scripts' / 'windows_user_browser_chatgpt.ps1').read_text()
    lower = script.lower()
    assert 'prompt-textarea' in script
    assert 'InvokePattern' in script
    assert 'providerEffectAttempted' in script
    assert 'CHALLENGE_GATED' in script
    for forbidden in (
        'cookies',
        'cookie',
        'user-data-dir=',
        'remote-debugging-port',
        'captcha',
        'turnstile',
        'click challenge',
        'verify you are human".invoke',
    ):
        assert forbidden not in lower


def test_classify_uses_active_user_without_prompt_or_provider_effect():
    payload = {
        'schemaVersion': 1,
        'kind': 'ordivon.windows-user-browser-classification',
        'standing': 'READY',
        'detail': 'authenticated ChatGPT composer available',
        'providerEffectAttempted': False,
    }
    port = FakePort(payload)
    controller = UserBrowserGatewayController(port, config())
    result = controller.classify()
    assert result['standing'] == 'READY'
    req = port.requests[0]
    assert req.capability == 'execution.windows'
    assert req.context == 'active_user'
    assert '-Mode' in req.args and 'classify' in req.args
    assert '-PromptPath' not in req.args
    assert '-PromptDigest' not in req.args


def test_classify_driver_does_not_require_effect_identity_parameters():
    script = (Path(__file__).resolve().parents[1] / 'scripts' / 'windows_user_browser_chatgpt.ps1').read_text()
    assert '[Parameter(Mandatory=$true)][string]$EffectId' not in script
    assert '[Parameter(Mandatory=$true)][string]$RequestDigest' not in script
    assert "if($Mode -ne 'classify'" in script
    assert 'EffectId and RequestDigest are required outside classify mode' in script
