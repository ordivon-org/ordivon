from domains.strategy.outcome_models import OutcomeSnapshot
from domains.strategy.outcome_orm import OutcomeSnapshotORM
from domains.strategy.outcome_repository import OutcomeRepository
from domains.strategy.outcome_service import OutcomeService
from domains.strategy.outcome_models import OutcomeSnapshot as LegacyOutcomeSnapshot
from domains.strategy.outcome_orm import OutcomeSnapshotORM as LegacyOutcomeSnapshotORM
from domains.strategy.outcome_repository import OutcomeRepository as LegacyOutcomeRepository
from domains.strategy.outcome_service import OutcomeService as LegacyOutcomeService


def test_root_outcome_imports_are_available():
    assert OutcomeSnapshot is not None
    assert OutcomeSnapshotORM is not None
    assert OutcomeRepository is not None
    assert OutcomeService is not None


def test_legacy_outcome_imports_still_resolve():
    assert LegacyOutcomeSnapshot.__name__ == OutcomeSnapshot.__name__
    assert LegacyOutcomeSnapshotORM.__name__ == OutcomeSnapshotORM.__name__
    assert LegacyOutcomeRepository.__name__ == OutcomeRepository.__name__
    assert LegacyOutcomeService.__name__ == OutcomeService.__name__
