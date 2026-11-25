#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 PRIMARY_REPOSITORY" >&2
  exit 64
fi

REPO="$1"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/primary-git-context.sh"
qualify_primary_git_context "$REPO"
# Qualification reads the existing index and object graph. Do not create a
# tree from a rejected index, refresh the index, or fetch promised objects.
export GIT_OPTIONAL_LOCKS=0 GIT_NO_LAZY_FETCH=1

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

# The index/tree relation is not a source-bytes proof while Git is instructed
# to suppress worktree checks via assume-unchanged or skip-worktree. Reject
# these exact native index states; neither mutating the index to clear them nor
# treating a clean porcelain/diff response as proof would be sound.
tracked_modes="$(git -C "$REPO" ls-files -v --)" || fail "cannot inspect tracked index flags"
if printf '%s\n' "$tracked_modes" | LC_ALL=C grep -E '^[a-zS]' >/dev/null; then
  fail "tracked source index hides worktree bytes via assume-unchanged/skip-worktree"
fi

# Native index-to-commit comparison checks paths, modes, object identity,
# and unmerged entries without write-tree's object/index materialization.
# Explicit submodule handling prevents ignore configuration from masking a
# staged gitlink change. External diff helpers are outside this contract.
git -C "$REPO" diff-index --cached --quiet --no-ext-diff --ignore-submodules=none "$HEAD_REVISION" -- ||
  fail "index differs from HEAD"
git -C "$REPO" diff --quiet --no-ext-diff --ignore-submodules=none -- ||
  fail "tracked worktree bytes differ from index"
[ -z "$(git -C "$REPO" ls-files --others --exclude-standard)" ] || fail "untracked paths are present"

printf 'primary_main_status=PASS\nhead=%s\ntree=%s\n' "$HEAD_REVISION" "$HEAD_TREE"
