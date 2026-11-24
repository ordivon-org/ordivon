"""Stable Host social lookup and horizon errors shared by read and write owners."""

from .errors import ConflictError


class SpaceNotFound(RuntimeError):
    pass


class TopicNotFound(RuntimeError):
    pass


class MessageNotFound(RuntimeError):
    pass


class TopicResumeCursorAhead(ConflictError):
    """The requested Topic message cursor exceeds the same-snapshot Topic horizon.

    A different cursor domain, stale client, or corrupt caller state can cause
    this. The query cannot choose which cause without external consumer facts.
    """

    def __init__(self, topic_ref: str, after_sequence: int, topic_high: int) -> None:
        self.topic_ref = topic_ref
        self.after_sequence = after_sequence
        self.topic_high = topic_high
        super().__init__(
            f"topic resume cursor {after_sequence} exceeds topic message high {topic_high}"
        )
