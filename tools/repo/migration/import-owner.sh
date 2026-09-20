#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 5 ]; then
  echo "usage: $0 ID SOURCE REVISION TARGET TARGET_ROOT" >&2
  exit 64
fi

ID="$1"
SOURCE="$2"
REVISION="$3"
TARGET="$4"
TARGET_ROOT="$5"
BACKUP_ROOT="/root/ordivon-migration-backups/2026-09-20"
TMP_ROOT="/root/ordivon-migration-tmp"
BUNDLE="$BACKUP_ROOT/$ID.bundle"
DISPOSABLE="$TMP_ROOT/import-$ID"
RECEIPT_DIR="$TARGET_ROOT/docs/migration/receipts"
REMOTE="import-$ID"

case "$ID" in
  *[!A-Za-z0-9._-]*|'')
    echo "invalid ID: $ID" >&2
    exit 64
    ;;
esac

case "$TARGET" in
  /*|''|../*|*/../*|*/..)
    echo "TARGET must be a non-empty repository-relative path without '..': $TARGET" >&2
    exit 64
    ;;
esac

git -C "$TARGET_ROOT" rev-parse --is-inside-work-tree >/dev/null
git -C "$SOURCE" cat-file -e "$REVISION^{commit}"

if [ -e "$TARGET_ROOT/$TARGET" ]; then
  echo "target path already exists: $TARGET_ROOT/$TARGET" >&2
  exit 65
fi

install -d -m 0700 "$BACKUP_ROOT" "$TMP_ROOT"
mkdir -p "$RECEIPT_DIR"

if [ ! -f "$BUNDLE" ]; then
  git -C "$SOURCE" bundle create "$BUNDLE" --all
fi
git -C "$SOURCE" bundle verify "$BUNDLE" >/dev/null
BUNDLE_SHA="$(sha256sum "$BUNDLE" | awk '{print $1}')"

rm -rf "$DISPOSABLE"
git clone --no-local --no-tags "$SOURCE" "$DISPOSABLE" >/dev/null
git -C "$DISPOSABLE" branch -f import-main "$REVISION"
git -C "$DISPOSABLE" remote remove origin
git -C "$DISPOSABLE" filter-repo   --refs refs/heads/import-main   --to-subdirectory-filter "$TARGET"   --force >/dev/null

REWRITTEN_REVISION="$(git -C "$DISPOSABLE" rev-parse import-main)"
COMMIT_MAP="$DISPOSABLE/.git/filter-repo/commit-map"
test -s "$COMMIT_MAP"
cp "$COMMIT_MAP" "$RECEIPT_DIR/$ID.commit-map"

if git -C "$TARGET_ROOT" remote get-url "$REMOTE" >/dev/null 2>&1; then
  echo "temporary remote already exists: $REMOTE" >&2
  exit 65
fi

remote_added=0
cleanup_remote() {
  if [ "$remote_added" -eq 1 ]; then
    git -C "$TARGET_ROOT" remote remove "$REMOTE" >/dev/null 2>&1 || true
  fi
}
trap cleanup_remote EXIT

git -C "$TARGET_ROOT" remote add "$REMOTE" "$DISPOSABLE"
remote_added=1
git -C "$TARGET_ROOT" fetch "$REMOTE" import-main >/dev/null
FETCHED_REVISION="$(git -C "$TARGET_ROOT" rev-parse FETCH_HEAD)"
test "$FETCHED_REVISION" = "$REWRITTEN_REVISION"

git -C "$TARGET_ROOT" merge   --allow-unrelated-histories   --no-ff   "$REWRITTEN_REVISION"   -m "chore: import $ID history under $TARGET" >/dev/null
MERGE_REVISION="$(git -C "$TARGET_ROOT" rev-parse HEAD)"

SOURCE_TREE="$(mktemp "$TMP_ROOT/$ID-source-tree.XXXXXX")"
TARGET_TREE="$(mktemp "$TMP_ROOT/$ID-target-tree.XXXXXX")"
cleanup_trees() {
  rm -f "$SOURCE_TREE" "$TARGET_TREE"
  cleanup_remote
}
trap cleanup_trees EXIT

git -C "$SOURCE" ls-tree -r "$REVISION" >"$SOURCE_TREE"
git -C "$TARGET_ROOT" ls-tree -r "$REWRITTEN_REVISION:$TARGET" >"$TARGET_TREE"
if ! cmp -s "$SOURCE_TREE" "$TARGET_TREE"; then
  echo "tree equality check failed for $ID" >&2
  diff -u "$SOURCE_TREE" "$TARGET_TREE" >&2 || true
  exit 66
fi

{
  printf '# Monorepo import receipt: %s\n\n' "$ID"
  printf -- '- Source repository: %s\n' "$SOURCE"
  printf -- '- Source revision: %s\n' "$REVISION"
  printf -- '- Rewritten revision: %s\n' "$REWRITTEN_REVISION"
  printf -- '- Merge revision: %s\n' "$MERGE_REVISION"
  printf -- '- Target path: %s\n' "$TARGET"
  printf -- '- Bundle: %s\n' "$BUNDLE"
  printf -- '- Bundle SHA-256: %s\n' "$BUNDLE_SHA"
} >"$RECEIPT_DIR/$ID.md"

git -C "$TARGET_ROOT" remote remove "$REMOTE"
remote_added=0
rm -f "$SOURCE_TREE" "$TARGET_TREE"
trap - EXIT

printf 'imported %s\nsource=%s\nrewritten=%s\nmerge=%s\ntarget=%s\nbundle_sha256=%s\n'   "$ID" "$REVISION" "$REWRITTEN_REVISION" "$MERGE_REVISION" "$TARGET" "$BUNDLE_SHA"
