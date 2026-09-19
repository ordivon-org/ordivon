from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

TaskStateWire = Literal["open", "completed", "abandoned"]


class TaskSummaryWire(TypedDict):
    task_id: str
    goal_id: str | None
    revision: int
    state: TaskStateWire
    checkpoint_digest: str
    writer_label: str | None


class TaskWire(TaskSummaryWire):
    checkpoint: dict[str, Any]


class DoctorCheckWire(TypedDict):
    name: str
    status: Literal["ok", "error"]
    detail: str


class DoctorWire(TypedDict):
    healthy: bool
    checks: list[DoctorCheckWire]


class HostInterfaceWire(TypedDict):
    surfaceVersion: int
    toolCount: int
    toolNames: list[str]
    readTools: list[str]
    writeTools: list[str]
    runtimeProxy: bool


class HostAuthorityWire(TypedDict):
    journalBackend: Literal["postgresql"]
    journalSchema: int
    events: int
    tasks: int
    terminalTasks: int
    tasksByState: dict[str, int]
    leases: int


class HostStatusResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-status"]
    observedAtMs: int
    detail: Literal["summary", "integrity", "history"]
    interface: HostInterfaceWire
    authority: HostAuthorityWire
    board: dict[str, Any]
    deployment: dict[str, Any]
    continuity: dict[str, int]
    recentActivity: list[dict[str, Any]]
    doctor: DoctorWire | None
    truthBoundary: dict[str, str]


class BoardMessageWire(TypedDict):
    sequence: int
    clientMessageId: str
    authorLabel: str
    authorIdentityRole: Literal["self-asserted-label"]
    messageKind: Literal["note", "question", "proposal", "warning", "reply"]
    topic: str | None
    message: str
    replyToClientMessageId: str | None
    taskId: str | None
    recordedAtMs: int
    messageDigest: str
    truthRole: Literal["coordination-message-not-domain-truth"]


class BoardPostResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-board-post-receipt"]
    admission: Literal["committed", "existing"]
    message: BoardMessageWire
    truthBoundary: str


class BoardListResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-board-list"]
    scope: str
    selectionMode: Literal["latest-window", "incremental-page"]
    requestedAfterSequence: int | None
    requestedLimit: int
    messages: list[BoardMessageWire]
    lastSequence: int
    nextAfterSequence: int
    hasMore: bool
    truthBoundary: str
    topic: NotRequired[str]
    clientMessageId: NotRequired[str]
    replyToClientMessageId: NotRequired[str]
    replyToAuthorLabel: NotRequired[str]


class BoardSearchResultWire(TypedDict):
    sequence: int
    clientMessageId: str


class BoardSearchResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-board-search"]
    scope: str
    truthRole: str
    sourceSnapshotHighWater: int
    liveHighWater: int
    negativeResultAuthoritative: bool
    requiresExactSourceReentry: bool
    results: list[BoardSearchResultWire]


class AttentionFenceWire(TypedDict):
    requestedAfterSequence: int
    lastSequence: int
    nextAfterSequence: int
    hasMore: bool
    completeThroughNextAfterSequence: bool


class AttentionSummaryWire(TypedDict):
    newMessageCount: int
    infrastructureMessageCount: int
    routedTaskCount: int
    routedMessageCount: int
    unroutedMessageCount: int
    missingTaskRouteCount: int


class AttentionResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-current-attention-delta"]
    truthRole: str
    boardFence: AttentionFenceWire
    summary: AttentionSummaryWire
    routedTasks: list[dict[str, Any]]
    missingTaskRoutes: list[dict[str, Any]]
    unroutedMessages: list[dict[str, Any]]
    truthBoundary: str



class TaskMutationResponse(TypedDict):
    schemaVersion: int
    kind: Literal[
        "ordivon.host-external-continuity-adopt",
        "ordivon.host-external-continuity-checkpoint",
    ]
    admission: Literal["committed", "existing"]
    task: TaskSummaryWire
    checkpoint: dict[str, Any]
    writerLabel: str | None


class TaskResumeResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-external-continuity-resume"]
    task: TaskSummaryWire
    checkpoint: dict[str, Any]
    writerLabel: str | None
    truthBoundary: str


class TaskObserveResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-task-observation"]
    task: TaskWire
    recentEvents: list[dict[str, Any]]
    truthBoundary: str


class TaskListResponse(TypedDict):
    schemaVersion: int
    kind: Literal["ordivon.host-task-list"]
    itemView: Literal["basic"]
    tasks: list[TaskSummaryWire]
    hasMore: bool
    nextCursor: str | None
    truthBoundary: str
