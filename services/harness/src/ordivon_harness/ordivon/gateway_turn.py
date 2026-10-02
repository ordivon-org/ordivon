"""Minimal Harness Adapter for one DeepSeek call through a local AI gateway.

The gateway remains a data-plane provider. This module does not select Provider
credentials, choose Network routes, retry/fallback upstream requests, or infer
gateway-internal attempt lineage. Those authorities remain with their natural
owners and are represented only by HarnessGatewayProviderBinding evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
from typing import Protocol

from anc_canonical import JsonValue, canonical_digest

from .control import ExecutionControl
from .deepseek import (
    DEFAULT_DEEPSEEK_BASE_URL,
    DeepSeekPostHandle,
    DeepSeekSettings,
    DeepSeekTurnAdapter,
    HttpClientDeepSeekTransport,
)
from .gateway_provider import HarnessGatewayProviderBinding
from .model import AgentTurnAdapterError, AgentTurnRequest, AgentTurnResult


_CODEC_SENTINEL = "ordivon-gateway-codec-not-a-provider-secret"


class GatewayTransportDelegate(Protocol):
    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes,
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> bytes: ...

    def start_post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes,
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> DeepSeekPostHandle: ...


def _gateway_error(error: AgentTurnAdapterError) -> AgentTurnAdapterError:
    mapped = AgentTurnAdapterError(
        f"Gateway-backed DeepSeek call failed: {error}",
        failure_code=error.failure_code,
        dispatch_safety=error.dispatch_safety,
    )
    mapped.__cause__ = error
    return mapped


class _GatewayPostHandle:
    def __init__(self, delegate: DeepSeekPostHandle) -> None:
        self._delegate = delegate

    def poll(self, timeout_seconds: float) -> bytes | None:
        try:
            return self._delegate.poll(timeout_seconds)
        except AgentTurnAdapterError as error:
            raise _gateway_error(error) from error

    def cancel(self) -> None:
        self._delegate.cancel()


class _GatewayDeepSeekTransport:
    """Rewrite one codec-produced DeepSeek request to one bound loopback gateway.

    The codec sentinel is asserted and removed before physical dispatch, so a
    Provider credential cannot accidentally cross this Harness seam.
    """

    def __init__(
        self,
        binding: HarnessGatewayProviderBinding,
        *,
        gateway_access_token: str | None,
        delegate: GatewayTransportDelegate | None = None,
    ) -> None:
        self.binding = binding
        if gateway_access_token is not None:
            if (
                not gateway_access_token
                or gateway_access_token != gateway_access_token.strip()
                or any(character.isspace() for character in gateway_access_token)
                or len(gateway_access_token.encode("utf-8")) > 16_384
            ):
                raise ValueError("gateway access token is invalid")
        self._gateway_access_token = gateway_access_token
        self._delegate = delegate or HttpClientDeepSeekTransport()
        self._provider_url = f"{DEFAULT_DEEPSEEK_BASE_URL}/chat/completions"
        self.gateway_url = binding.endpoint.rstrip("/") + "/v1/chat/completions"

    def _rewrite(
        self, url: str, headers: dict[str, str]
    ) -> tuple[str, dict[str, str]]:
        if url != self._provider_url:
            raise ValueError("gateway codec attempted an unexpected Provider endpoint")
        rewritten = dict(headers)
        expected = f"Bearer {_CODEC_SENTINEL}"
        if rewritten.pop("Authorization", None) != expected:
            raise ValueError("gateway codec Provider credential sentinel changed")
        if self._gateway_access_token is not None:
            rewritten["Authorization"] = f"Bearer {self._gateway_access_token}"
        rewritten["User-Agent"] = "ordivon-harness-gateway/1"
        return self.gateway_url, rewritten

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes,
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> bytes:
        gateway_url, gateway_headers = self._rewrite(url, headers)
        try:
            return self._delegate.post(
                gateway_url,
                headers=gateway_headers,
                body=body,
                timeout_seconds=timeout_seconds,
                max_response_bytes=max_response_bytes,
            )
        except AgentTurnAdapterError as error:
            raise _gateway_error(error) from error

    def start_post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes,
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> DeepSeekPostHandle:
        gateway_url, gateway_headers = self._rewrite(url, headers)
        start_post = getattr(self._delegate, "start_post", None)
        if not callable(start_post):
            raise AgentTurnAdapterError(
                "Gateway transport delegate does not expose a cancellable call handle"
            )
        try:
            return _GatewayPostHandle(
                start_post(
                    gateway_url,
                    headers=gateway_headers,
                    body=body,
                    timeout_seconds=timeout_seconds,
                    max_response_bytes=max_response_bytes,
                )
            )
        except AgentTurnAdapterError as error:
            raise _gateway_error(error) from error


class GatewayBackedDeepSeekTurnAdapter:
    """Compose the existing DeepSeek codec with one evidence-bound local gateway.

    This Adapter is intentionally narrow: only DeepSeek over the OpenAI Chat
    ingress is admitted. Provider credentials and Network realization are not
    constructor inputs; they remain outside Harness.
    """

    adapter_id = "ordivon.gateway.deepseek.openai-chat.v1"
    supports_call_handle = False

    def __init__(
        self,
        binding: HarnessGatewayProviderBinding,
        *,
        gateway_access_token: str | None = None,
        transport: GatewayTransportDelegate | None = None,
        completion_contract: Mapping[str, JsonValue] | None = None,
        timeout_seconds: float = 90.0,
        max_response_bytes: int = 4_194_304,
        max_output_tokens: int = 8_192,
    ) -> None:
        if binding.ingress_protocol != "openai-chat":
            raise ValueError("DeepSeek gateway Adapter requires openai-chat ingress")
        if binding.requested_provider != "deepseek":
            raise ValueError("DeepSeek gateway Adapter requires requested Provider deepseek")
        if binding.direct_fallback:
            raise ValueError("DeepSeek gateway Adapter requires directFallback=false")
        if binding.allowed_effective_providers != ("deepseek",):
            raise ValueError(
                "DeepSeek gateway Adapter requires exactly one allowed effective Provider: deepseek"
            )
        if binding.credential_name_ref is None:
            raise ValueError("DeepSeek gateway binding requires an opaque credential name ref")
        if binding.network_egress_profile_ref is None:
            raise ValueError("DeepSeek gateway binding requires a Network egress profile ref")

        self.binding = binding
        self.model_id = binding.requested_model
        self._transport = _GatewayDeepSeekTransport(
            binding,
            gateway_access_token=gateway_access_token,
            delegate=transport,
        )
        self._codec = DeepSeekTurnAdapter(
            DeepSeekSettings(
                api_key=_CODEC_SENTINEL,
                model=binding.requested_model,
                timeout_seconds=timeout_seconds,
                max_response_bytes=max_response_bytes,
                max_output_tokens=max_output_tokens,
            ),
            transport=self._transport,
            completion_contract=completion_contract,
        )
        self.structured_completion_contract_digest = (
            self._codec.structured_completion_contract_digest
        )

    def provider_request_digest(self, request: AgentTurnRequest) -> str:
        """Bind exact non-secret gateway request semantics before dispatch."""

        _, _provider_url, headers, body = self._codec._prepare_request(request)
        semantic_headers = {
            name: value
            for name, value in headers.items()
            if name.lower() != "authorization"
        }
        return canonical_digest(
            {
                "schemaVersion": 1,
                "kind": "ordivon.gateway-backed-provider-request",
                "adapterId": self.adapter_id,
                "requestedModelId": self.model_id,
                "bindingDigest": self.binding.digest,
                "codecAdapterId": self._codec.adapter_id,
                "agentDispatchDigest": request.dispatch_digest,
                "method": "POST",
                "gatewayPath": "/v1/chat/completions",
                "headers": semantic_headers,
                "bodyDigest": "sha256:" + hashlib.sha256(body).hexdigest(),
            }
        )

    gateway_request_digest = provider_request_digest

    def request_token_upper_bound(self, request: AgentTurnRequest) -> int:
        return self._codec.request_token_upper_bound(request)

    def accepts_effective_model_id(self, model_id: str) -> bool:
        return self._codec.accepts_effective_model_id(model_id)

    def invoke(self, request: AgentTurnRequest) -> AgentTurnResult:
        return self._codec.invoke(request)

    def invoke_with_control(
        self, request: AgentTurnRequest, control: ExecutionControl
    ) -> AgentTurnResult:
        return self._codec.invoke_with_control(request, control)


__all__ = ["GatewayBackedDeepSeekTurnAdapter", "GatewayTransportDelegate"]
