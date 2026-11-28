from __future__ import annotations

class HarnessStoreError(RuntimeError):
    pass


class HarnessRevisionConflict(HarnessStoreError):
    pass


class HarnessEventConflict(HarnessStoreError):
    pass


class HarnessLeaseHeld(HarnessStoreError):
    pass


class HarnessLeaseConflict(HarnessStoreError):
    pass


class HarnessJournalCorruption(HarnessStoreError):
    pass


class HarnessObjectMissing(HarnessStoreError):
    pass


class HarnessObjectCorrupt(HarnessStoreError):
    pass


class HarnessUnsupportedLegacyRepresentation(HarnessStoreError):
    """An intact historical representation is not a current executable Contract."""


class HarnessTerminalConflict(HarnessStoreError):
    pass
