"""Stable Host social lookup errors shared by read and write owners."""


class SpaceNotFound(RuntimeError):
    pass


class TopicNotFound(RuntimeError):
    pass


class MessageNotFound(RuntimeError):
    pass
