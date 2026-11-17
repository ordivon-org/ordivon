from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

from .wire_common import AdmissionWire


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


class WorkListResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-work-list"]
    works: list[dict[str, Any]]
    hasMore: bool
    nextCursor: dict[str, str] | None
    rankingApplied: Literal[False]
    truthBoundary: str
