from __future__ import annotations


class RuntimeExecutionError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        task_type: str | None = None,
        retryable: bool = False,
        status_code: int | None = None,
        task_id: str | None = None,
        trace_id: str | None = None,
        request_payload: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.task_type = task_type
        self.retryable = retryable
        self.status_code = status_code
        self.task_id = task_id
        self.trace_id = trace_id
        self.request_payload = request_payload


class RuntimeUnavailableError(RuntimeExecutionError):
    pass


class RuntimeTaskError(RuntimeExecutionError):
    pass
