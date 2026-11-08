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

class HostNativePoolStatsWire(TypedDict):
    """Exact bounded Psycopg counters; omitted upstream zeroes are zero-filled."""

    pool_min: int
    pool_max: int
    pool_size: int
    pool_available: int
    requests_waiting: int
    usage_ms: int
    requests_num: int
    requests_queued: int
    requests_wait_ms: int
    requests_errors: int
    returns_bad: int
    connections_num: int
    connections_ms: int
    connections_errors: int
    connections_lost: int


class HostPoolStatsResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-pool-stats"]
    observedAtMs: int
    connectionMode: Literal["pooled", "direct"]
    stats: HostNativePoolStatsWire | None
    truthBoundary: str
