"""Existing Host actor.declare response contract, separate from Work wire."""
from __future__ import annotations

from typing import Literal, TypedDict

from ..wire_common import AdmissionWire


class ActorRefResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-actor-ref"]
    admission: AdmissionWire
    actorRef: str
    actorKind: Literal["unknown", "human", "agent", "service", "organization"]
    createdAt: str
    truthBoundary: str
