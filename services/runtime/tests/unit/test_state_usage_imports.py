from state.usage.models import UsageSnapshot as LegacyUsageSnapshot
from state.usage.orm import UsageSnapshotORM as LegacyUsageSnapshotORM
from state.usage.repository import (
    UsageSnapshotRepository as LegacyUsageSnapshotRepository,
)
from state.usage.service import UsageService as LegacyUsageService
from state.usage.models import UsageSnapshot
from state.usage.orm import UsageSnapshotORM
from state.usage.repository import UsageSnapshotRepository
from state.usage.service import UsageService


def test_root_state_usage_imports_are_available():
    assert UsageSnapshot is not None
    assert UsageSnapshotORM is not None
    assert UsageSnapshotRepository is not None
    assert UsageService is not None


def test_legacy_usage_imports_still_resolve():
    assert LegacyUsageSnapshot.__name__ == UsageSnapshot.__name__
    assert LegacyUsageSnapshotORM.__name__ == UsageSnapshotORM.__name__
    assert LegacyUsageSnapshotRepository.__name__ == UsageSnapshotRepository.__name__
    assert LegacyUsageService.__name__ == UsageService.__name__
