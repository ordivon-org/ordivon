from datetime import UTC, datetime, timedelta

from ordivon_host_v2.lifecycle_report import TRUTH_BOUNDARY, build_report


def _row(ref: str, kind: str, age_days: int) -> dict:
    now = datetime(2026, 10, 3, 4, 0, tzinfo=UTC)
    return {
        "work_ref": ref,
        "kind": kind,
        "current_revision": 3,
        "current_snapshot_digest": "sha256:" + "0" * 64,
        "updated_at": now - timedelta(days=age_days),
        "payload": {"unresolved": ["x"], "nextActions": ["y"]},
    }


def test_lifecycle_report_separates_legacy_aged_and_recent_without_disposition() -> None:
    observed = datetime(2026, 10, 3, 4, 0, tzinfo=UTC)
    report = build_report(
        [
            _row("work:legacy-task:a", "legacy-task", 1),
            _row("work:native:old", "research", 9),
            _row("work:native:new", "research", 2),
        ],
        observed_at=observed,
        stale_days=7,
    )

    assert report["openCount"] == 3
    assert report["classes"] == {
        "legacy-migration-review": 1,
        "aged-native-review": 1,
        "recent-open": 1,
    }
    assert "do not establish semantic completion" in TRUTH_BOUNDARY
    assert all("disposition" not in item for item in report["items"])
