from __future__ import annotations
from datetime import datetime
from enum import Enum

class ExecutionStage(Enum):
    INIT = "initialization"
    CONTEXT_LOADED = "context_loaded"
    REASONING_DONE = "reasoning_done"
    RISK_VERIFIED = "risk_verified"
    PERSISTED = "persisted"
    COMPLETED = "completed"
    FAILED = "failed"

class ExecutionState:
    """单次执行状态记录 (Orchestration Support)"""

    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self.stage = ExecutionStage.INIT
        self.history = []
        self.start_time = datetime.now()

    def update_stage(self, stage: ExecutionStage, metadata: dict = None):
        self.stage = stage
        self.history.append({
            "stage": stage.value,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })

    def to_dict(self):
        return {
            "trace_id": self.trace_id,
            "current_stage": self.stage.value,
            "history": self.history,
            "duration": (datetime.now() - self.start_time).total_seconds()
        }
