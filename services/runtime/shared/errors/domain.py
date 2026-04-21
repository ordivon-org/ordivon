class DomainError(Exception):
    pass


class InvalidStateTransition(DomainError):
    pass


class DomainNotFound(DomainError):
    pass
