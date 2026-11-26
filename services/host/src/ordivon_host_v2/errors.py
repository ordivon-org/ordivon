class HostV2Error(RuntimeError):
    pass


class ConflictError(HostV2Error):
    pass


class WorkRevisionUnavailable(ConflictError):
    """Observed missing revision refined by the Work row in the same transaction.

    Never assert a historical retention policy, future commit or external effect.
    """

    def __init__(self, work_ref: str, requested_revision: int, current_revision: int) -> None:
        self.work_ref = work_ref
        self.requested_revision = requested_revision
        self.current_revision = current_revision
        if requested_revision > current_revision:
            self.reason = "revision_ahead_of_current"
        elif requested_revision < current_revision:
            self.reason = "historical_snapshot_absent"
        else:
            self.reason = "current_snapshot_missing"
        super().__init__(f"work {work_ref} has no revision {requested_revision}")


class WorkNotFound(RuntimeError):
    pass


class ActorRefNotFound(RuntimeError):
    pass
