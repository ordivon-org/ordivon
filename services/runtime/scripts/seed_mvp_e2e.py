from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from domains.journal.models import Review
from domains.journal.repository import ReviewRepository
from domains.strategy.models import Recommendation
from domains.strategy.repository import RecommendationRepository
from shared.config.settings import settings
from shared.enums.domain import RecommendationStatus, ReviewStatus
from state.db.bootstrap import init_db
from state.db.session import SessionLocal, engine


SEED_RECOMMENDATION_ID = "reco_mvp_e2e_seed"
SEED_REVIEW_ID = "review_mvp_e2e_seed"


def _resolve_duckdb_path(db_url: str) -> Path | None:
    prefix = "duckdb:///"
    if not db_url.startswith(prefix):
        return None
    return Path(db_url.removeprefix(prefix)).resolve()


def _reset_database_file() -> None:
    db_path = _resolve_duckdb_path(settings.db_url)
    if db_path is None:
        return

    engine.dispose()
    for suffix in ("", ".wal"):
        target = Path(f"{db_path}{suffix}")
        if target.exists():
            target.unlink()

    db_path.parent.mkdir(parents=True, exist_ok=True)


def main() -> None:
    _reset_database_file()
    init_db()

    db = SessionLocal()
    try:
        recommendation_repo = RecommendationRepository(db)
        review_repo = ReviewRepository(db)

        if recommendation_repo.get(SEED_RECOMMENDATION_ID) is None:
            recommendation_repo.create(
                Recommendation(
                    id=SEED_RECOMMENDATION_ID,
                    title="MVP E2E Seed Recommendation",
                    summary="Seed recommendation used to verify review-workbench continuation.",
                    status=RecommendationStatus.REVIEW_PENDING,
                )
            )

        if review_repo.get(SEED_REVIEW_ID) is None:
            review_repo.create(
                Review(
                    id=SEED_REVIEW_ID,
                    recommendation_id=SEED_RECOMMENDATION_ID,
                    review_type="recommendation_postmortem",
                    status=ReviewStatus.PENDING,
                    expected_outcome="Seeded review path remains selectable from the workbench.",
                )
            )

        db.commit()
    finally:
        db.close()

    print({
        "db_url": settings.db_url,
        "seed_recommendation_id": SEED_RECOMMENDATION_ID,
        "seed_review_id": SEED_REVIEW_ID,
        "env": os.getenv("PFIOS_ENV", settings.env),
    })


if __name__ == "__main__":
    main()
