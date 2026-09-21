#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
  echo "usage: $0 PRIMARY_REPOSITORY CANDIDATE [EXPECTED_MAIN]" >&2
  exit 64
fi

REPO="$1"
CANDIDATE_INPUT="$2"
EXPECTED_MAIN="${3:-}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CHECKER="$SCRIPT_DIR/check-primary-main.sh"

git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null
COMMON_DIR="$(git -C "$REPO" rev-parse --git-common-dir)"
case "$COMMON_DIR" in
  /*) ;;
  *) COMMON_DIR="$REPO/$COMMON_DIR" ;;
esac
COMMON_DIR="$(realpath "$COMMON_DIR")"

exec 9>"$COMMON_DIR/ordivon-main-integration.lock"
if ! flock -n 9; then
  echo "main integration lock is already held: $COMMON_DIR/ordivon-main-integration.lock" >&2
  exit 75
fi

# Re-check only after the lock has been acquired. Never auto-stash/reset a shared checkout.
"$CHECKER" "$REPO" >/dev/null

CURRENT_MAIN="$(git -C "$REPO" rev-parse refs/heads/main)"
if [ -n "$EXPECTED_MAIN" ]; then
  EXPECTED_MAIN_REVISION="$(git -C "$REPO" rev-parse "${EXPECTED_MAIN}^{commit}")"
  if [ "$CURRENT_MAIN" != "$EXPECTED_MAIN_REVISION" ]; then
    echo "main moved since qualification: expected=$EXPECTED_MAIN_REVISION current=$CURRENT_MAIN" >&2
    exit 67
  fi
fi

CANDIDATE="$(git -C "$REPO" rev-parse "${CANDIDATE_INPUT}^{commit}")"

if git -C "$REPO" merge-base --is-ancestor "$CANDIDATE" "$CURRENT_MAIN"; then
  "$CHECKER" "$REPO" >/dev/null
  printf 'integration=ALREADY_PRESENT\nmain=%s\ncandidate=%s\n' "$CURRENT_MAIN" "$CANDIDATE"
  exit 0
fi

MODE=""
if git -C "$REPO" merge-base --is-ancestor "$CURRENT_MAIN" "$CANDIDATE"; then
  MODE="FAST_FORWARD"
else
  merge_preview="$(mktemp)"
  cleanup() { rm -f "$merge_preview"; }
  trap cleanup EXIT
  set +e
  git -C "$REPO" merge-tree --write-tree "$CURRENT_MAIN" "$CANDIDATE" >"$merge_preview" 2>&1
  preview_rc=$?
  set -e
  if [ "$preview_rc" -ne 0 ]; then
    echo "candidate does not merge cleanly into current main" >&2
    cat "$merge_preview" >&2
    exit 68
  fi
  MODE="MERGE_COMMIT"
fi

# Narrow stale-ref fence for writers that do not yet honor this lock.
"$CHECKER" "$REPO" >/dev/null
[ "$(git -C "$REPO" rev-parse refs/heads/main)" = "$CURRENT_MAIN" ] || {
  echo "main moved during integration qualification" >&2
  exit 69
}

if [ "$MODE" = "FAST_FORWARD" ]; then
  git -C "$REPO" merge --ff-only "$CANDIDATE" >/dev/null
else
  GIT_MERGE_AUTOEDIT=no git -C "$REPO" merge --no-ff --no-edit "$CANDIDATE" >/dev/null
fi

"$CHECKER" "$REPO" >/dev/null
FINAL_MAIN="$(git -C "$REPO" rev-parse refs/heads/main)"
git -C "$REPO" merge-base --is-ancestor "$CANDIDATE" "$FINAL_MAIN"

printf 'integration=%s\nprevious_main=%s\ncandidate=%s\nmain=%s\n'   "$MODE" "$CURRENT_MAIN" "$CANDIDATE" "$FINAL_MAIN"
