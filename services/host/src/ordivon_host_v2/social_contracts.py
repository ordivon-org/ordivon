from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

AdmissionWire = Literal["committed", "existing"]


class ActorRefResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-actor-ref"]
    admission: AdmissionWire
    actorRef: str
    actorKind: Literal["unknown", "human", "agent", "service", "organization"]
    createdAt: str
    truthBoundary: str


class WorkResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-work"]
    admission: NotRequired[AdmissionWire]
    workRef: str
    workKind: str
    state: str
    revision: int
    snapshotDigest: str
    snapshot: dict[str, Any]
    writerActorRef: str
    createdByActorRef: str
    createdAt: str
    updatedAt: str
    truthBoundary: str


class WorkRelationResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-work-relation"]
    admission: AdmissionWire
    sourceWorkRef: str
    relation: Literal["parent_of", "depends_on", "blocks", "relates_to"]
    targetWorkRef: str
    createdByActorRef: str
    createdAt: str
    truthBoundary: str


class WorkRelationsResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-work-relations"]
    workRef: str
    relations: list[dict[str, Any]]
    truthBoundary: str


class SpaceResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-space"]
    admission: NotRequired[AdmissionWire]
    spaceRef: str
    purpose: str
    createdByActorRef: str
    createdAt: str
    subjectRefs: list[str]
    participants: list[dict[str, Any]]
    topics: list[dict[str, Any]]
    truthBoundary: str


class ParticipationResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-participation"]
    spaceRef: str
    actorRef: str
    standing: Literal["joined", "left", "observer"]
    updatedAt: str
    truthBoundary: str


class TopicResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-topic"]
    admission: AdmissionWire
    topicRef: str
    spaceRef: str
    title: str
    state: Literal["open", "closed"]
    createdByActorRef: str
    createdAt: str
    updatedAt: str
    truthBoundary: str


class TopicResumeResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-topic-resume"]
    topic: dict[str, Any]
    messages: list[dict[str, Any]]
    hasMore: bool
    nextAfterSequence: int
    truthBoundary: str


class MessageResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-message"]
    admission: AdmissionWire
    sequence: int
    messageRef: str
    spaceRef: str
    topicRef: str
    authorActorRef: str
    messageKind: Literal["note", "question", "proposal", "warning", "finding", "handoff"]
    body: str
    messageDigest: str
    recordedAtMs: int
    createdAt: str
    truthBoundary: str


class MessageRelationResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-message-relation"]
    admission: AdmissionWire
    sourceMessageRef: str
    relation: Literal["reply_to", "mentions", "references", "acknowledges", "supersedes", "about"]
    targetRef: str
    createdByActorRef: str
    createdAt: str
    truthBoundary: str


class CoordinationIntentResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-coordination-intent"]
    admission: AdmissionWire
    intentRef: str
    actorRef: str
    subjectRef: str
    workRef: str | None
    spaceRef: str | None
    operation: str
    standing: Literal["active", "released"]
    observedAtMs: int
    expiresAtMs: int | None
    updatedAt: str
    truthBoundary: str


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


class WorkListResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-work-list"]
    works: list[dict[str, Any]]
    hasMore: bool
    nextCursor: dict[str, str] | None
    rankingApplied: Literal[False]
    truthBoundary: str


class SpaceListResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-space-list"]
    spaces: list[dict[str, Any]]
    hasMore: bool
    nextCursor: dict[str, str] | None
    rankingApplied: Literal[False]
    truthBoundary: str


class MessageSearchResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-message-search"]
    query: str
    messages: list[dict[str, Any]]
    hasMore: bool
    nextBeforeSequence: int | None
    rankingApplied: Literal[False]
    ordering: Literal["sequence_desc"]
    truthBoundary: str


class SubscriptionListResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-subscription-list"]
    actorRef: str
    subscriptions: list[dict[str, Any]]
    hasMore: bool
    truncated: bool
    rankingApplied: Literal[False]
    truthBoundary: str
