#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CHECKER="$SCRIPT_DIR/check-primary-main.sh"
INTEGRATOR="$SCRIPT_DIR/integrate-main.sh"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/ordivon-integrate-main-test.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

configure_repo() {
  git -C "$1" config user.name "Ordivon Integration Test"
  git -C "$1" config user.email "integration-test@localhost"
}

make_repo() {
  local repo="$1"
  git init -b main "$repo" >/dev/null
  configure_repo "$repo"
  printf 'base\n' >"$repo/state.txt"
  git -C "$repo" add state.txt
  git -C "$repo" commit -m "base" >/dev/null
}

# 1. Clean primary + descendant candidate integrates and leaves primary exactly synchronized.
repo="$TMP_ROOT/ff"
candidate_wt="$TMP_ROOT/ff-candidate"
make_repo "$repo"
base="$(git -C "$repo" rev-parse HEAD)"
git -C "$repo" worktree add -b candidate "$candidate_wt" "$base" >/dev/null
configure_repo "$candidate_wt"
printf 'candidate\n' >"$candidate_wt/candidate.txt"
git -C "$candidate_wt" add candidate.txt
git -C "$candidate_wt" commit -m "candidate" >/dev/null
candidate="$(git -C "$candidate_wt" rev-parse HEAD)"
"$INTEGRATOR" "$repo" refs/heads/candidate "$base" >"$TMP_ROOT/integrate-main-ff.out"
test "$(git -C "$repo" rev-parse main)" = "$candidate"
"$CHECKER" "$repo" >/dev/null
test -z "$(git -C "$repo" status --porcelain)"

# 2. External ref advancement with a stale primary index/worktree is fail-closed.
stale="$TMP_ROOT/stale"
stale_candidate_wt="$TMP_ROOT/stale-candidate"
make_repo "$stale"
stale_base="$(git -C "$stale" rev-parse HEAD)"
git -C "$stale" worktree add -b candidate "$stale_candidate_wt" "$stale_base" >/dev/null
configure_repo "$stale_candidate_wt"
printf 'advanced\n' >"$stale_candidate_wt/advanced.txt"
git -C "$stale_candidate_wt" add advanced.txt
git -C "$stale_candidate_wt" commit -m "advance elsewhere" >/dev/null
advanced="$(git -C "$stale_candidate_wt" rev-parse HEAD)"
git -C "$stale" update-ref refs/heads/main "$advanced"

set +e
"$CHECKER" "$stale" >"$TMP_ROOT/check-primary-stale.out" 2>&1
checker_rc=$?
"$INTEGRATOR" "$stale" refs/heads/candidate "$advanced" >"$TMP_ROOT/integrate-main-stale.out" 2>&1
integrator_rc=$?
set -e
test "$checker_rc" -ne 0
test "$integrator_rc" -ne 0
grep -F "primary checkout is not synchronized with main" "$TMP_ROOT/check-primary-stale.out" >/dev/null
grep -F "primary checkout is not synchronized with main" "$TMP_ROOT/integrate-main-stale.out" >/dev/null
test ! -e "$stale/advanced.txt"

# 3. A conflict-free precondition is required; conflict leaves current main unchanged and clean.
conflict="$TMP_ROOT/conflict"
conflict_candidate_wt="$TMP_ROOT/conflict-candidate"
make_repo "$conflict"
split="$(git -C "$conflict" rev-parse HEAD)"
git -C "$conflict" worktree add -b candidate "$conflict_candidate_wt" "$split" >/dev/null
configure_repo "$conflict_candidate_wt"
printf 'candidate-side\n' >"$conflict_candidate_wt/state.txt"
git -C "$conflict_candidate_wt" add state.txt
git -C "$conflict_candidate_wt" commit -m "candidate side" >/dev/null
printf 'main-side\n' >"$conflict/state.txt"
git -C "$conflict" add state.txt
git -C "$conflict" commit -m "main side" >/dev/null
conflict_main="$(git -C "$conflict" rev-parse HEAD)"

set +e
"$INTEGRATOR" "$conflict" refs/heads/candidate "$conflict_main" >"$TMP_ROOT/integrate-main-conflict.out" 2>&1
conflict_rc=$?
set -e
test "$conflict_rc" -ne 0
grep -F "candidate does not merge cleanly into current main" "$TMP_ROOT/integrate-main-conflict.out" >/dev/null
test "$(git -C "$conflict" rev-parse HEAD)" = "$conflict_main"
test -z "$(git -C "$conflict" status --porcelain)"
"$CHECKER" "$conflict" >/dev/null

echo "PASS integrate-main smoke"
