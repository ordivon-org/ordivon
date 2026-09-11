from __future__ import annotations

import re
import time
from typing import Any

import psycopg
from psycopg.rows import dict_row

from .canonical import canonical_digest
from .errors import ConflictError

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _now_ms() -> int:
    return time.time_ns() // 1_000_000


class NewsStore:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def publish(
        self,
        *,
        client_publish_id: str,
        edition_id: str,
        expected_revision: int,
        edition: dict[str, Any],
    ) -> dict[str, Any]:
        if not client_publish_id or client_publish_id != client_publish_id.strip():
            raise ValueError("clientPublishId is invalid")
        if not edition_id.startswith("news:") or edition_id != edition_id.strip():
            raise ValueError("editionId must start with news:")
        if expected_revision < 0:
            raise ValueError("expectedRevision must be non-negative")
        if edition.get("editionId") != edition_id:
            raise ValueError("edition.editionId differs from editionId")
        edition_date = edition.get("editionDate")
        if not isinstance(edition_date, str) or _DATE_RE.fullmatch(edition_date) is None:
            raise ValueError("editionDate must use YYYY-MM-DD")
        digest = canonical_digest(edition)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            existing = conn.execute(
                "SELECT * FROM news_publications WHERE client_publish_id=%s FOR UPDATE",
                (client_publish_id,),
            ).fetchone()
            if existing is not None:
                if (
                    existing["edition_digest"] != digest
                    or existing["edition_id"] != edition_id
                    or int(existing["expected_revision"]) != expected_revision
                ):
                    raise ConflictError("clientPublishId is already bound to different content")
                return self._receipt("existing", existing)
            conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (edition_id,))
            current_row = conn.execute(
                "SELECT COALESCE(max(revision),0) AS value FROM news_publications WHERE edition_id=%s",
                (edition_id,),
            ).fetchone()
            assert current_row is not None
            current = current_row["value"]
            if int(current) != expected_revision:
                raise ConflictError(
                    f"expected news revision {expected_revision}, current revision is {current}"
                )
            revision = expected_revision + 1
            row = conn.execute(
                "INSERT INTO news_publications(client_publish_id,edition_id,edition_date,expected_revision,revision,edition_digest,edition,recorded_at_ms) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,%s) RETURNING *",
                (
                    client_publish_id,
                    edition_id,
                    edition_date,
                    expected_revision,
                    revision,
                    digest,
                    psycopg.types.json.Jsonb(edition),
                    _now_ms(),
                ),
            ).fetchone()
            assert row is not None
            conn.execute(
                "INSERT INTO activity_log(activity_kind,subject_id,payload) VALUES ('news.publish',%s,%s::jsonb)",
                (edition_id, psycopg.types.json.Jsonb({"revision": revision})),
            )
            return self._receipt("committed", row)

    def read(
        self,
        *,
        edition_id: str | None = None,
        revision: int | None = None,
        sections: list[str] | None = None,
        categories: list[str] | None = None,
        thread_keys: list[str] | None = None,
        include_rendered_brief: bool = False,
    ) -> dict[str, Any]:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            if edition_id is None:
                row = conn.execute(
                    "SELECT * FROM news_publications ORDER BY sequence DESC LIMIT 1"
                ).fetchone()
            elif revision is None:
                row = conn.execute(
                    "SELECT * FROM news_publications WHERE edition_id=%s ORDER BY revision DESC LIMIT 1",
                    (edition_id,),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM news_publications WHERE edition_id=%s AND revision=%s",
                    (edition_id, revision),
                ).fetchone()
            if row is None:
                raise KeyError("news edition does not exist")
            edition = dict(row["edition"])
            items = list(edition.get("items") or [])
            section_set, category_set, thread_set = (
                set(sections or []),
                set(categories or []),
                set(thread_keys or []),
            )
            edition["items"] = [
                item
                for item in items
                if (not section_set or item.get("section") in section_set)
                and (not category_set or item.get("category") in category_set)
                and (not thread_set or item.get("threadKey") in thread_set)
            ]
            if not include_rendered_brief and "renderedBrief" in edition:
                edition["renderedBrief"] = None
            edition["revision"] = int(row["revision"])
            edition["editionDigest"] = row["edition_digest"]
            edition["recordedAtMs"] = int(row["recorded_at_ms"])
            return {
                "schemaVersion": 2,
                "kind": "ordivon.host-news-read",
                "edition": edition,
                "truthBoundary": "retained external-news projection only; source claims remain externally revalidatable",
            }

    def list(
        self, *, limit: int = 30, from_date: str | None = None, to_date: str | None = None
    ) -> dict[str, Any]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be in [1,100]")
        clauses, params = [], []
        if from_date is not None:
            clauses.append("edition_date >= %s")
            params.append(from_date)
        if to_date is not None:
            clauses.append("edition_date <= %s")
            params.append(to_date)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(limit)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            rows = conn.execute(
                f"SELECT * FROM news_publications {where} ORDER BY edition_date DESC, edition_id DESC, revision DESC LIMIT %s",
                params,
            ).fetchall()
            return {
                "schemaVersion": 2,
                "kind": "ordivon.host-news-list",
                "scope": "daily-external-news-editions",
                "editions": [self._publication(row) for row in rows],
                "hasMore": False,
                "nextCursor": None,
                "truthBoundary": "publication inventory only; not external-world truth",
            }

    def _receipt(self, admission: str, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "schemaVersion": 2,
            "kind": "ordivon.host-news-publish-receipt",
            "admission": admission,
            "publication": self._publication(row),
            "truthBoundary": "Host owns publication persistence/revision only; external claims do not become world truth",
        }

    @staticmethod
    def _publication(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "sequence": int(row["sequence"]),
            "clientPublishId": row["client_publish_id"],
            "editionId": row["edition_id"],
            "expectedRevision": int(row["expected_revision"]),
            "revision": int(row["revision"]),
            "editionDigest": row["edition_digest"],
            "recordedAtMs": int(row["recorded_at_ms"]),
        }
