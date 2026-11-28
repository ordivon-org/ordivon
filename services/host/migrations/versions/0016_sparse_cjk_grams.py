"""Add a sparse CJK-only candidate index without retiring the old reader.

Revision ID: 0016
Revises: 0015

The old indexed function must never be replaced in place. Build a new
index concurrently, switch the source reader only after readiness, and
retain the old index until a separate installed-consumer retirement.
"""
from alembic import op
from sqlalchemy import text

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None

NEW_INDEX = "message_cjk_sparse_ngrams3_v1_idx"
OLD_INDEX = "message_unicode_ngrams3_idx"
_FUNCTION_BODY = """
    WITH cjk_positions AS (
        SELECT ord::integer AS i
        FROM unnest(string_to_array(input_text,NULL)) WITH ORDINALITY AS x(ch,ord)
        WHERE ascii(ch) BETWEEN 13312 AND 40959
    ), window_positions AS (
        SELECT DISTINCT pos
        FROM cjk_positions
        CROSS JOIN LATERAL generate_series(
            greatest(i-2,1),least(i,char_length(input_text)-2)
        ) AS z(pos)
    )
    SELECT ARRAY(
        SELECT gram FROM (
            SELECT DISTINCT substring(input_text FROM pos FOR 3) AS gram
            FROM window_positions
        ) AS unique_grams
        ORDER BY gram COLLATE "C"
    )
"""
_CREATE_FUNCTION = (
    "CREATE FUNCTION host_cjk_sparse_ngrams3_v1(input_text text) "
    "RETURNS text[] LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE "
    "AS $fn$" + _FUNCTION_BODY + "$fn$;"
)


def _function_exists() -> bool:
    row = op.get_bind().execute(text(
        "SELECT p.prosrc, p.provolatile='i' AND p.proisstrict "
        "AND p.proparallel='s' AND NOT p.prosecdef AND NOT p.proretset "
        "AND p.proconfig IS NULL AND p.prokind='f' "
        "AND p.prorettype='text[]'::regtype AND l.lanname='sql' "
        "FROM pg_proc p JOIN pg_language l ON l.oid=p.prolang "
        "WHERE p.oid=to_regprocedure('host_cjk_sparse_ngrams3_v1(text)')"
    )).first()
    if row is None:
        return False
    if tuple(row) != (_FUNCTION_BODY, True):
        raise RuntimeError("Conflicting sparse CJK function; refusing indexed redefinition")
    return True


def _index_state(name: str, expression: str) -> tuple[bool, bool] | None:
    row = op.get_bind().execute(
        text("SELECT i.indisvalid,i.indisready,pg_get_expr(i.indexprs,i.indrelid), "
             "i.indrelid=to_regclass('messages') AND am.amname='gin' "
             "AND i.indpred IS NULL AND NOT i.indisunique "
             "AND i.indnkeyatts=1 AND i.indnatts=1 AND opc.opcname='array_ops' "
             "FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid "
             "JOIN pg_am am ON am.oid=c.relam "
             "JOIN pg_opclass opc ON opc.oid=i.indclass[0] "
             "WHERE i.indexrelid=to_regclass(:name)"),
        {"name": name},
    ).first()
    if row is None:
        if op.get_bind().execute(
            text("SELECT to_regclass(:name) IS NOT NULL"), {"name": name}
        ).scalar():
            raise RuntimeError(f"Conflicting relation for index {name}")
        return None
    if tuple(row[2:]) != (expression, True):
        raise RuntimeError(f"Conflicting index {name}; refusing replacement")
    return bool(row[0]), bool(row[1])


def _require_old_reader() -> None:
    if _index_state(OLD_INDEX, "host_unicode_ngrams3(body)") != (True, True):
        raise RuntimeError("Original Unicode index must be valid during reader transition")


def _sparse_index_state() -> tuple[bool, bool] | None:
    return _index_state(NEW_INDEX, "host_cjk_sparse_ngrams3_v1(body)")


def _version(value: int) -> None:
    op.execute("ALTER TABLE host_v2_schema DROP CONSTRAINT host_v2_schema_schema_version_check")
    op.execute(f"UPDATE host_v2_schema SET schema_version={value} WHERE singleton")
    op.execute(
        "ALTER TABLE host_v2_schema ADD CONSTRAINT host_v2_schema_schema_version_check "
        f"CHECK (schema_version BETWEEN 1 AND {value})"
    )


def upgrade() -> None:
    # A previous interrupted concurrent build may have left an invalid index.
    # These versioned names are owned only by this migration.
    _require_old_reader()
    if not _function_exists():
        op.execute(_CREATE_FUNCTION)
    invalid = _sparse_index_state() not in (None, (True, True))
    with op.get_context().autocommit_block():
        if invalid:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {NEW_INDEX}")
        op.execute(
            f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {NEW_INDEX} "
            "ON messages USING GIN (host_cjk_sparse_ngrams3_v1(body))"
        )
    if _sparse_index_state() != (True, True):
        raise RuntimeError("Sparse CJK GIN index build did not become valid")
    _version(16)


def downgrade() -> None:
    # Operator must quiesce schema-16 readers before this downgrade.
    _require_old_reader()
    _function_exists()
    _sparse_index_state()
    with op.get_context().autocommit_block():
        op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {NEW_INDEX}")
    op.execute("DROP FUNCTION IF EXISTS host_cjk_sparse_ngrams3_v1(text)")
    _version(15)
