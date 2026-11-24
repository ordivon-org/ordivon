from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

from .wire_common import AdmissionWire, NonnegativeHostInteger, PositiveHostInteger


class SpaceResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-space"]
    admission: NotRequired[AdmissionWire]
    spaceRef: str
    purpose: str
    createdByActorRef: str
    createdAt: str
    subjectRefs: list[str]
    subjectCount: int
    subjectHasMore: bool
    participants: list[dict[str, Any]]
    participantCount: int
    participantHasMore: bool
    topics: list[dict[str, Any]]
    topicCount: int
    topicHasMore: bool
    truthBoundary: str


class SpaceSubjectsResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-space-subject-list"]
    spaceRef: str
    subjectRefs: list[str]
    hasMore: bool
    nextAfterSubjectRef: str | None
    rankingApplied: Literal[False]
    truthBoundary: str


class ParticipationResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-participation"]
    spaceRef: str
    actorRef: str
    standing: Literal["joined", "left", "observer"]
    updatedAt: str
    truthBoundary: str


class ParticipationListResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-participation-list"]
    spaceRef: str
    participants: list[dict[str, Any]]
    hasMore: bool
    nextAfterActorRef: str | None
    rankingApplied: Literal[False]
    truthBoundary: str


class TopicResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-topic"]
    admission: AdmissionWire
    topicRef: str
    spaceRef: str
    title: str
    state: Literal["open", "closed", "archived"]
    createdByActorRef: str
    createdAt: str
    updatedAt: str
    # Pre-epoch-9 topic.create receipts remain exact historical evidence.
    changeSequence: NotRequired[PositiveHostInteger]
    truthBoundary: str


class TopicListResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-topic-list"]
    spaceRef: str
    topics: list[dict[str, Any]]
    hasMore: bool
    nextAfterTopicRef: str | None
    rankingApplied: Literal[False]
    truthBoundary: str


class TopicResumeCoordinate(TypedDict):
    topicRef: str
    spaceRef: str
    title: str
    state: Literal["open", "closed", "archived"]
    changeSequence: PositiveHostInteger
    topicHighSequence: NonnegativeHostInteger


class TopicResumeResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-topic-resume"]
    topic: TopicResumeCoordinate
    messages: list[dict[str, Any]]
    hasMore: bool
    nextAfterSequence: int
    truthBoundary: str


class TopicCursorResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-topic-cursor", "ordivon.host-topic-cursor-ack"]
    actorRef: str
    topicRef: str
    cursor: int
    topicHighSequence: int
    previousCursor: NotRequired[int]
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


class MessageReadResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-message-read"]
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


class MessageRelationsResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-message-relation-list"]
    messageRef: str
    direction: Literal["outgoing", "incoming", "both"]
    relations: list[dict[str, Any]]
    hasMore: bool
    nextAfterChangeSequence: int
    rankingApplied: Literal[False]
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
