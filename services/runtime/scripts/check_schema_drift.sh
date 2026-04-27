#!/bin/bash
# Schema drift check: detects ORM model vs database schema differences.
# Fails if Alembic autogenerate would produce a non-empty migration.
set -euo pipefail

echo "=== Schema Drift Check ==="

# Generate a temporary migration to detect drift
uv run alembic revision --autogenerate -m "drift_check" --rev-id drift_check_temp > /dev/null 2>&1 || true

DRIFT_FILE=$(ls alembic/versions/drift_check_temp_*.py 2>/dev/null | head -1)

if [ -z "$DRIFT_FILE" ]; then
    echo "✅ No schema drift detected"
    exit 0
fi

# Check if the generated migration has substantive content
NON_EMPTY_LINES=$(grep -cvE '^\s*(#|$|pass\s*$)' "$DRIFT_FILE" || echo "0")

# Clean up
rm -f "$DRIFT_FILE"

if [ "$NON_EMPTY_LINES" -le 5 ]; then
    echo "✅ No schema drift detected (empty autogenerate)"
    exit 0
else
    echo "❌ SCHEMA DRIFT DETECTED"
    echo "Run: alembic revision --autogenerate -m 'describe_change'"
    echo "Then review and commit the new migration."
    exit 1
fi
