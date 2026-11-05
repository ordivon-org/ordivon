class HostV2Error(RuntimeError):
    pass


class ConflictError(HostV2Error):
    pass


class WorkNotFound(RuntimeError):
    pass


class ActorRefNotFound(RuntimeError):
    pass
