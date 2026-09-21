#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 PRIMARY_REPOSITORY" >&2
  exit 64
fi

REPO="$1"
git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null

fail() {
  echo "primary checkout is not synchronized with main: $*" >&2
  exit 65
}

BRANCH="$(git -C "$REPO" symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
[ "$BRANCH" = "main" ] || fail "checked-out branch is '${BRANCH:-DETACHED}', expected main"

HEAD_REVISION="$(git -C "$REPO" rev-parse HEAD)"
MAIN_REVISION="$(git -C "$REPO" rev-parse refs/heads/main)"
[ "$HEAD_REVISION" = "$MAIN_REVISION" ] || fail "HEAD=$HEAD_REVISION main=$MAIN_REVISION"

HEAD_TREE="$(git -C "$REPO" rev-parse "HEAD^{tree}")"
if ! INDEX_TREE="$(git -C "$REPO" write-tree 2>/dev/null)"; then
  fail "index cannot be materialized as a tree"
fi
[ "$INDEX_TREE" = "$HEAD_TREE" ] || fail "index_tree=$INDEX_TREE head_tree=$HEAD_TREE"

git -C "$REPO" diff --quiet -- || fail "tracked worktree bytes differ from index"
git -C "$REPO" diff --cached --quiet -- || fail "index differs from HEAD"
[ -z "$(git -C "$REPO" ls-files --others --exclude-standard)" ] || fail "untracked paths are present"

printf 'primary_main_status=PASS\nhead=%s\ntree=%s\n' "$HEAD_REVISION" "$HEAD_TREE"
