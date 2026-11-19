from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

from .wire_common import AdmissionWire


class SubscriptionResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-subscription", "ordivon.host-subscription-unfollow"]
    admission: AdmissionWire
    actorRef: str
    targetKind: Literal["work", "space", "topic"]
    targetRef: str
    createdAt: NotRequired[str]
    changeSequence: NotRequired[int]
    truthBoundary: str


class AttentionEventWire(TypedDict):
    changeSequence: int
    eventKind: str
    sourceRef: str
    contextRef: str
    reasons: list[str]
    navigationKind: Literal["work", "space", "topic", "subject"]
    navigationRef: str


class AttentionDeltaResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-attention-delta-r1"]
    actorRef: str
    afterSequence: int
    snapshotHighSequence: int
    events: list[AttentionEventWire]
    hasMore: bool
    nextAfterSequence: int
    rankingApplied: Literal[False]
    truthBoundary: str


class AttentionAckResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-attention-ack"]
    actorRef: str
    previousCursor: int
    cursor: int
    truthBoundary: str


class AttentionReentryResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-attention-reentry-r1"]
    actorRef: str
    afterSequence: int
    snapshotHighSequence: int
    items: list[dict[str, Any]]
    rawEventCount: int
    hasMore: bool
    nextAfterSequence: int
    rankingApplied: Literal[False]
    truthBoundary: str


class SubscriptionListResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-subscription-list"]
    actorRef: str
    subscriptions: list[dict[str, Any]]
    hasMore: bool
    truncated: bool
    nextAfterTargetKind: str | None
    nextAfterTargetRef: str | None
    rankingApplied: Literal[False]
    truthBoundary: str
