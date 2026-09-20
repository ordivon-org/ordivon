#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 5 ] && [ "$#" -ne 6 ]; then
  echo "usage: $0 ID SOURCE REVISION TARGET TARGET_ROOT [BUNDLE]" >&2
  exit 64
fi

ID="$1"
SOURCE="$2"
REVISION="$3"
TARGET="$4"
TARGET_ROOT="$5"
BACKUP_ROOT="/root/ordivon-migration-backups/2026-09-20"
DEFAULT_BUNDLE="$BACKUP_ROOT/$ID.bundle"
BUNDLE="${6:-$DEFAULT_BUNDLE}"
EXPLICIT_BUNDLE=0
if [ "$#" -eq 6 ]; then
  EXPLICIT_BUNDLE=1
fi
RECEIPT_DIR="$TARGET_ROOT/docs/migration/receipts"
TEMP_REF="refs/ordivon/import-sources/$ID"

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
test -z "$(git -C "$TARGET_ROOT" status --porcelain)"

if [ -e "$TARGET_ROOT/$TARGET" ]; then
  echo "target path already exists: $TARGET_ROOT/$TARGET" >&2
  exit 65
fi

install -d -m 0700 "$BACKUP_ROOT"
mkdir -p "$RECEIPT_DIR"

if [ "$EXPLICIT_BUNDLE" -eq 1 ]; then
  if [ ! -f "$BUNDLE" ]; then
    echo "explicit bundle does not exist: $BUNDLE" >&2
    exit 66
  fi
elif [ ! -f "$BUNDLE" ]; then
  git -C "$SOURCE" bundle create "$BUNDLE" --all
fi
git -C "$SOURCE" bundle verify "$BUNDLE" >/dev/null
BUNDLE_SHA="$(sha256sum "$BUNDLE" | awk '{print $1}')"

SOURCE_REF="$(
  git bundle list-heads "$BUNDLE" |
    awk -v revision="$REVISION" '
      $1 == revision && $2 != "HEAD" && !found {
        print $2
        found = 1
      }
    '
)"
if [ -z "$SOURCE_REF" ]; then
  echo "bundle does not advertise exact revision $REVISION; create a source ref for the accepted import revision and refresh the bundle" >&2
  exit 66
fi

if git -C "$TARGET_ROOT" show-ref --verify --quiet "$TEMP_REF"; then
  echo "temporary import ref already exists: $TEMP_REF" >&2
  exit 65
fi

cleanup_ref() {
  git -C "$TARGET_ROOT" update-ref -d "$TEMP_REF" >/dev/null 2>&1 || true
}
trap cleanup_ref EXIT

git -C "$TARGET_ROOT" fetch --no-tags "$BUNDLE" "$SOURCE_REF:$TEMP_REF" >/dev/null
FETCHED_REVISION="$(git -C "$TARGET_ROOT" rev-parse "$TEMP_REF")"
test "$FETCHED_REVISION" = "$REVISION"

TARGET_BEFORE="$(git -C "$TARGET_ROOT" rev-parse HEAD)"
git -C "$TARGET_ROOT" read-tree --reset "$TARGET_BEFORE"
git -C "$TARGET_ROOT" read-tree --prefix="$TARGET/" "$TEMP_REF^{tree}"
MERGE_TREE="$(git -C "$TARGET_ROOT" write-tree)"
MERGE_REVISION="$(
  printf 'chore: import %s identity-preserving history under %s\n' "$ID" "$TARGET" |
    git -C "$TARGET_ROOT" commit-tree "$MERGE_TREE" -p "$TARGET_BEFORE" -p "$REVISION"
)"
git -C "$TARGET_ROOT" reset --hard "$MERGE_REVISION" >/dev/null

SOURCE_TREE="$(mktemp /root/ordivon-migration-tmp/"$ID"-source-tree.XXXXXX)"
TARGET_TREE="$(mktemp /root/ordivon-migration-tmp/"$ID"-target-tree.XXXXXX)"
cleanup_all() {
  rm -f "$SOURCE_TREE" "$TARGET_TREE"
  cleanup_ref
}
trap cleanup_all EXIT

git -C "$SOURCE" ls-tree -r "$REVISION" >"$SOURCE_TREE"
git -C "$TARGET_ROOT" ls-tree -r "$MERGE_REVISION:$TARGET" >"$TARGET_TREE"
if ! cmp -s "$SOURCE_TREE" "$TARGET_TREE"; then
  echo "tree equality check failed for $ID" >&2
  diff -u "$SOURCE_TREE" "$TARGET_TREE" >&2 || true
  exit 67
fi

git -C "$TARGET_ROOT" merge-base --is-ancestor "$REVISION" "$MERGE_REVISION"

git -C "$SOURCE" rev-list "$REVISION" |
  sort |
  awk '{print $1 " " $1}' >"$RECEIPT_DIR/$ID.commit-map"

{
  printf '# Monorepo import receipt: %s\n\n' "$ID"
  printf -- '- historyMode: identity-preserving-merge\n'
  printf -- '- Source repository: %s\n' "$SOURCE"
  printf -- '- Source revision: %s\n' "$REVISION"
  printf -- '- Source advertised ref: %s\n' "$SOURCE_REF"
  printf -- '- Merge revision: %s\n' "$MERGE_REVISION"
  printf -- '- Target path: %s\n' "$TARGET"
  printf -- '- Bundle: %s\n' "$BUNDLE"
  printf -- '- Bundle SHA-256: %s\n' "$BUNDLE_SHA"
} >"$RECEIPT_DIR/$ID.md"

rm -f "$SOURCE_TREE" "$TARGET_TREE"
cleanup_ref
trap - EXIT

printf 'imported %s\nhistory_mode=identity-preserving-merge\nsource=%s\nmerge=%s\ntarget=%s\nbundle_sha256=%s\n'   "$ID" "$REVISION" "$MERGE_REVISION" "$TARGET" "$BUNDLE_SHA"
