#!/usr/bin/env bash
# Toolchain fingerprint checker — ensures all dev tools meet minimum versions.
# Run: bash scripts/check_toolchain.sh
#
# This is a CandidateRule (advisory) gate. It does NOT block CI by default.
# Failures indicate version drift that should be investigated.
# Exit 0 = all tools present and above minimum; Exit 1 = one or more below minimum.
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

PASS=0
WARN=0
FAIL=0

pass() { echo -e "  ${GREEN}PASS${NC}  $1"; ((PASS++)) || true; }
warn() { echo -e "  ${YELLOW}WARN${NC}  $1"; ((WARN++)) || true; }
fail() { echo -e "  ${RED}FAIL${NC}  $1"; ((FAIL++)) || true; }

# ── Semantic version comparator ──────────────────────────────────
# Returns 0 if $1 >= $2, 1 otherwise.
# Handles MAJOR.MINOR.PATCH format; trailing segments beyond PATCH are ignored.
version_ge() {
  # Extract first MAJOR.MINOR[.PATCH] from arbitrary version string.
  local a
  a=$(echo "$1" | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1)
  local b
  b=$(echo "$2" | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1)
  [[ -z "$a" ]] && return 1
  [[ -z "$b" ]] && return 1
  IFS='.' read -ra A <<< "$a"
  IFS='.' read -ra B <<< "$b"
  local len=${#A[@]}
  [[ ${#B[@]} -gt $len ]] && len=${#B[@]}
  for ((i=0; i<len; i++)); do
    local ai=${A[i]:-0}
    local bi=${B[i]:-0}
    (( ai > bi )) && return 0
    (( ai < bi )) && return 1
  done
  return 0
}

# ── Check: tool must exist ───────────────────────────────────────
require_tool() {
  local name="$1"
  local get_version_cmd="$2"
  local min_version="$3"
  local critical="${4:-true}"   # true = fail on missing; false = warn only

  if ! command -v "$name" &>/dev/null && ! type "$name" &>/dev/null 2>&1; then
    if [[ "$critical" == "true" ]]; then
      fail "$name: not found (required)"
      return 1
    else
      warn "$name: not found (optional, skipped)"
      return 0
    fi
  fi

  local actual
  actual=$(eval "$get_version_cmd" 2>&1) || {
    fail "$name: version detection failed"
    return 1
  }

  if version_ge "$actual" "$min_version"; then
    pass "$name $actual  (>= $min_version)"
  else
    fail "$name $actual  (required >= $min_version)"
    return 1
  fi
}

# ── Main ─────────────────────────────────────────────────────────
echo "=== Toolchain Fingerprint ==="
echo ""

# --- Python (project venv) ---
echo "Python:"
PYTHON_BIN=".venv/bin/python"
if [[ -x "$PYTHON_BIN" ]]; then
  ACTUAL_PY=$("$PYTHON_BIN" --version 2>&1)
  if version_ge "$ACTUAL_PY" "3.11"; then
    pass "python $ACTUAL_PY  (>= 3.11)"
  else
    fail "python $ACTUAL_PY  (required >= 3.11)"
  fi
else
  fail "python: .venv/bin/python not found — run 'uv sync' first"
fi

# --- uv ---
echo "uv:"
require_tool uv "uv --version" "0.0.0" true
# Check uv sync status (optional)
if [[ -d .venv ]]; then
  pass ".venv exists"
else
  fail ".venv missing — run 'uv sync'"
fi

# --- pnpm ---
echo "pnpm:"
require_tool pnpm "pnpm --version" "10.33.0" true

# --- Node ---
echo "Node:"
require_tool node "node --version" "20.0.0" true

# --- pip (in project venv) ---
echo "pip:"
if [[ -x "$PYTHON_BIN" ]]; then
  ACTUAL_PIP=$("$PYTHON_BIN" -m pip --version 2>&1)
  if version_ge "$ACTUAL_PIP" "26.1"; then
    pass "pip $ACTUAL_PIP  (>= 26.1, CVE-2026-3219 patched)"
  else
    fail "pip $ACTUAL_PIP  (required >= 26.1 — CVE-2026-3219)"
  fi
else
  fail "pip: cannot check — venv not found"
fi

# --- ruff ---
echo "ruff:"
if [[ -x "$PYTHON_BIN" ]]; then
  ACTUAL_RUFF=$("$PYTHON_BIN" -m ruff --version 2>&1)
  if version_ge "$ACTUAL_RUFF" "0.12.12"; then
    pass "ruff $ACTUAL_RUFF  (>= 0.12.12)"
  else
    fail "ruff $ACTUAL_RUFF  (required >= 0.12.12)"
  fi
else
  fail "ruff: cannot check — venv not found"
fi

# --- basedpyright ---
echo "basedpyright:"
if [[ -x "$PYTHON_BIN" ]]; then
  if "$PYTHON_BIN" -m basedpyright --version &>/dev/null; then
    ACTUAL_BP=$("$PYTHON_BIN" -m basedpyright --version 2>&1 | head -1)
    pass "basedpyright $ACTUAL_BP"
  else
    fail "basedpyright: not installed in venv — run 'uv sync --extra dev'"
  fi
else
  fail "basedpyright: cannot check — venv not found"
fi

# --- git ---
echo "Git:"
require_tool git "git --version" "0.0.0" false

# --- Docker (optional) ---
echo "Docker (optional):"
if command -v docker &>/dev/null; then
  DOCKER_VER=$(docker --version 2>&1)
  pass "docker $DOCKER_VER"
else
  warn "docker: not found (optional, needed for PG regression tests)"
fi

# ── Summary ──────────────────────────────────────────────────────
echo ""
echo "──────────────────────────────────────────"
echo -e "Results: ${GREEN}${PASS} passed${NC}  ${YELLOW}${WARN} warnings${NC}  ${RED}${FAIL} failed${NC}"
echo "──────────────────────────────────────────"

if (( FAIL > 0 )); then
  echo ""
  echo "Fix: uv sync --extra dev && uv run python -m pip install --upgrade 'pip>=26.1'"
  exit 1
fi

echo -e "${GREEN}Toolchain consistent${NC}"
exit 0
