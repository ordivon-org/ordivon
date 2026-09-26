from __future__ import annotations

from typing import Literal, TypedDict


class DoctorCheckWire(TypedDict):
    name: str
    status: Literal["ok", "error"]
    detail: str


class DoctorWire(TypedDict):
    healthy: bool
    checks: list[DoctorCheckWire]


class HostAuthorityWire(TypedDict):
    journalBackend: Literal["postgresql"]
    journalSchema: int
    actorRefs: int
    works: int
    worksByState: dict[str, int]
    workSnapshots: int
    spaces: int
    topics: int
    messages: int
    subscriptions: int
    changeHighSequence: int


class HostStatusResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-status"]
    observedAtMs: int
    detail: Literal["summary", "integrity", "history"]
    authority: HostAuthorityWire
    doctor: DoctorWire | None
    truthBoundary: dict[str, str]
