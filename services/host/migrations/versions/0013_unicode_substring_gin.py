"""Use GIN array_ops for lossless Unicode codepoint substring candidates.

Revision ID: 0013
Revises: 0012

The deployed pg_trgm index had zero extracted CJK keys under C locale.
Use a codepoint-gram expression index with exact strpos verification.
A concurrent index build leaves message writes available.
"""
from alembic import op
from sqlalchemy import text

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

NEW_INDEX = "message_unicode_ngrams3_idx"
OLD_INDEX = "message_body_trgm_idx"

_CREATE_FUNCTION = """
CREATE OR REPLACE FUNCTION host_unicode_ngrams3(input_text text)
RETURNS text[]
LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE
AS $fn$
    SELECT ARRAY(
        SELECT gram FROM (
            SELECT DISTINCT substring(input_text FROM n FOR 3) AS gram
            FROM generate_series(1, greatest(char_length(input_text) - 2, 0)) AS ord(n)
        ) AS unique_grams
        ORDER BY gram COLLATE "C"
    )
$fn$;
"""


def _index_state(name: str) -> tuple[bool, bool] | None:
    row = op.get_bind().execute(
        text("SELECT i.indisvalid, i.indisready FROM pg_index i "
             "WHERE i.indexrelid=to_regclass(:index_name)"),
        {"index_name": name},
    ).first()
    return None if row is None else (bool(row[0]), bool(row[1]))


def upgrade() -> None:
    op.execute(_CREATE_FUNCTION)
    invalid = _index_state(NEW_INDEX) not in (None, (True, True))
    with op.get_context().autocommit_block():
        if invalid:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {NEW_INDEX}")
        op.execute(
            f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {NEW_INDEX} "
            "ON messages USING GIN (host_unicode_ngrams3(body))"
        )
    if _index_state(NEW_INDEX) != (True, True):
        raise RuntimeError("Unicode GIN index build did not become valid")
    with op.get_context().autocommit_block():
        op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {OLD_INDEX}")
    op.execute("ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS "
               "host_v2_schema_schema_version_check")
    op.execute("ALTER TABLE host_v2_schema ADD CONSTRAINT "
               "host_v2_schema_schema_version_check "
               "CHECK (schema_version BETWEEN 1 AND 13)")
    op.execute("UPDATE host_v2_schema SET schema_version=13 WHERE singleton")


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(
            f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {OLD_INDEX} "
            "ON messages USING GIN (body gin_trgm_ops)"
        )
        op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {NEW_INDEX}")
    op.execute("DROP FUNCTION IF EXISTS host_unicode_ngrams3(text)")
    op.execute("UPDATE host_v2_schema SET schema_version=12 WHERE singleton")
    op.execute("ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS "
               "host_v2_schema_schema_version_check")
    op.execute("ALTER TABLE host_v2_schema ADD CONSTRAINT "
               "host_v2_schema_schema_version_check "
               "CHECK (schema_version BETWEEN 1 AND 12)")
