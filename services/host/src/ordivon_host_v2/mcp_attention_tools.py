from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from mcp.server import MCPServer

from .mcp_domain_errors import _project_domain_errors
from .social_attention import AttentionStore
from .social_contracts import (
    AttentionAckResponse,
    AttentionDeltaResponse,
    AttentionReentryResponse,
    SubscriptionListResponse,
    SubscriptionResponse,
)


def register_attention_tools(
    mcp: MCPServer,
    attention: AttentionStore,
    request_id: Callable[[str, object], str],
) -> None:
    """Register actor-scoped subscription and attention tools via their native store."""

    @mcp.tool(name="subscription.follow")
    @_project_domain_errors
    def subscription_follow(
        actorRef: str,
        targetKind: Literal["work", "space", "topic"],
        targetRef: str,
    ) -> SubscriptionResponse:
        request = {"actorRef": actorRef, "targetKind": targetKind, "targetRef": targetRef}
        return attention.follow(
            actor_ref=actorRef,
            target_kind=targetKind,
            target_ref=targetRef,
            client_request_id=request_id("subscription-follow", request),
        )

    @mcp.tool(name="subscription.list")
    @_project_domain_errors
    def subscription_list(
        actorRef: str,
        targetKind: Literal["work", "space", "topic"] | None = None,
        afterTargetKind: str | None = None,
        afterTargetRef: str | None = None,
        limit: int = 200,
        maxBytes: int = 262_144,
    ) -> SubscriptionListResponse:
        return attention.list_subscriptions(
            actorRef,
            target_kind=targetKind,
            after_target_kind=afterTargetKind,
            after_target_ref=afterTargetRef,
            limit=limit,
            max_bytes=maxBytes,
        )

    @mcp.tool(name="subscription.unfollow")
    @_project_domain_errors
    def subscription_unfollow(
        actorRef: str,
        targetKind: Literal["work", "space", "topic"],
        targetRef: str,
    ) -> SubscriptionResponse:
        request = {"actorRef": actorRef, "targetKind": targetKind, "targetRef": targetRef}
        return attention.unfollow(
            actor_ref=actorRef,
            target_kind=targetKind,
            target_ref=targetRef,
            client_request_id=request_id("subscription-unfollow", request),
        )

    @mcp.tool(name="attention.get")
    @_project_domain_errors
    def attention_get(
        actorRef: str, limit: int = 100, maxBytes: int = 262_144
    ) -> AttentionDeltaResponse:
        return attention.get(actorRef, limit=limit, max_bytes=maxBytes)

    @mcp.tool(name="attention.delta")
    @_project_domain_errors
    def attention_delta(
        actorRef: str, afterSequence: int, limit: int = 100, maxBytes: int = 262_144
    ) -> AttentionDeltaResponse:
        return attention.delta(
            actorRef, after_sequence=afterSequence, limit=limit, max_bytes=maxBytes
        )

    @mcp.tool(name="attention.reentry")
    @_project_domain_errors
    def attention_reentry(
        actorRef: str,
        afterSequence: int | None = None,
        limit: int = 100,
        maxBytes: int = 262_144,
    ) -> AttentionReentryResponse:
        return attention.reentry(
            actorRef, after_sequence=afterSequence, limit=limit, max_bytes=maxBytes
        )

    @mcp.tool(name="attention.ack")
    @_project_domain_errors
    def attention_ack(actorRef: str, cursor: int) -> AttentionAckResponse:
        request = {"actorRef": actorRef, "cursor": cursor}
        return attention.ack(
            actorRef,
            cursor=cursor,
            client_request_id=request_id("attention-ack", request),
        )
