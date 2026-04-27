#!/bin/bash
# Schema drift check: detects ORM model vs database schema differences.
# Fails if Alembic autogenerate would produce a non-empty migration.
set -euo pipefail

echo "=== Schema Drift Check ==="

# Generate a temporary migration to detect drift
# (ignore exit code — alembic may fail if no changes exist)
uv run alembic revision --autogenerate -m "drift_check" --rev-id drift_check_temp > /dev/null 2>&1 || true

# Find the generated temp migration (use find instead of ls to handle no-match gracefully)
DRIFT_FILE=$(find alembic/versions -maxdepth 1 -name 'drift_check_temp_*.py' -print -quit 2>/dev/null)

if [ -z "$DRIFT_FILE" ]; then
    echo "✅ No schema drift detected"
    exit 0
fi

# Check if the generated migration contains actual DDL operations.
# A real schema drift produces op.add_column / op.create_table / etc.
# A boilerplate-only migration (pass in upgrade/downgrade) means ORM = DB.
HAS_REAL_DRIFT=$(grep -cE 'op\.(create_table|drop_table|add_column|drop_column|alter_column|create_index|drop_index|create_unique_constraint|create_foreign_key|execute|batch_alter_table|rename_table|bulk_insert)' "$DRIFT_FILE" 2>/dev/null || true)

# Clean up temp file
rm -f "$DRIFT_FILE"

# Normalize: if grep returned empty or non-numeric, treat as 0
case "$HAS_REAL_DRIFT" in
    ''|*[!0-9]*) HAS_REAL_DRIFT=0 ;;
esac

if [ "$HAS_REAL_DRIFT" -eq 0 ]; then
    echo "✅ No schema drift detected (ORM = DB)"
    exit 0
else
    echo "❌ SCHEMA DRIFT DETECTED ($HAS_REAL_DRIFT DDL operation(s) needed)"
    echo "Run: alembic revision --autogenerate -m 'describe_change'"
    echo "Then review and commit the new migration."
    exit 1
fi
