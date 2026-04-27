#!/usr/bin/env bash
# CI Quality Gates — enforces code quality before commit/merge.
# Run: bash scripts/ci-quality-gates.sh
# Fails fast on first violation.

set -euo pipefail
cd "$(dirname "$0")/.."

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; exit 1; }

echo "════════════════════════════════════════════"
echo "CI Quality Gates"
echo "════════════════════════════════════════════"

# ── Gate 1: Type checking ──────────────────────────────────
echo ""
echo "── Gate 1/7: basedpyright type check ──"
if unset VIRTUAL_ENV && uv run basedpyright --level error .; then
    pass "basedpyright"
else
    fail "basedpyright — type errors found. Run: uv run basedpyright --level error ."
fi

# ── Gate 2: Lint ──────────────────────────────────────────
echo ""
echo "── Gate 2/7: ruff lint ──"
uv run ruff check . && pass "ruff lint" || fail "ruff lint"

# ── Gate 3: Import sorting ────────────────────────────────
echo ""
echo "── Gate 3/7: ruff format (imports) ──"
uv run ruff format --check . && pass "ruff format" || fail "ruff format"

# ── Gate 4: Architecture boundaries ───────────────────────
echo ""
echo "── Gate 4/7: architecture tests ──"
uv run pytest tests/architecture/ -q --no-header && pass "architecture" || fail "architecture"

# ── Gate 5: Unit tests (no DB) ────────────────────────────
echo ""
echo "── Gate 5/7: unit tests (DuckDB in-memory) ──"
uv run pytest tests/unit/ -q --no-header && pass "unit" || fail "unit"

# ── Gate 6: Full regression (requires PG) ─────────────────
echo ""
echo "── Gate 6/7: full regression (PostgreSQL) ──"
PG_URL="postgresql://pfios:pfios@127.0.0.1:5432/pfios_test"
if pg_isready -h 127.0.0.1 -p 5432 -U pfios -d pfios_test >/dev/null 2>&1; then
    PFIOS_DB_URL="$PG_URL" uv run pytest tests/ -q --no-header && pass "full regression" || fail "full regression"
else
    echo "  ⚠ PostgreSQL not available — skipping full regression"
    echo "  Start with: docker compose up postgres -d --wait"
fi

# ── Gate 7: Coverage threshold ────────────────────────────
echo ""
echo "── Gate 7/7: coverage (≥80%) ──"
if pg_isready -h 127.0.0.1 -p 5432 -U pfios -d pfios_test >/dev/null 2>&1; then
    PFIOS_DB_URL="$PG_URL" uv run pytest tests/ -q --no-header \
        --cov=. --cov-report=term --cov-fail-under=80 \
        2>&1 | tail -20
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        pass "coverage ≥80%"
    else
        fail "coverage below 80%"
    fi
else
    echo "  ⚠ PostgreSQL not available — skipping coverage"
fi

echo ""
echo "════════════════════════════════════════════"
echo -e "${GREEN}ALL GATES PASSED${NC}"
echo "════════════════════════════════════════════"
