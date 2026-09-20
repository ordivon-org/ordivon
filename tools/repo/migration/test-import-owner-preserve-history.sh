#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
IMPORTER="$SCRIPT_DIR/import-owner-preserve-history.sh"
TMP_ROOT="$(mktemp -d /root/ordivon-migration-tmp/preserve-history-test.XXXXXX)"
SOURCE="$TMP_ROOT/source"
TARGET_ROOT="$TMP_ROOT/target"
BACKUP="/root/ordivon-migration-backups/2026-09-20/preserve-sample.bundle"

cleanup() {
  rm -rf "$TMP_ROOT"
  rm -f "$BACKUP"
}
trap cleanup EXIT

git init -b main "$SOURCE" >/dev/null
git -C "$SOURCE" config user.name "Ordivon Migration Test"
git -C "$SOURCE" config user.email "migration-test@localhost"
printf 'alpha\n' >"$SOURCE/a.txt"
git -C "$SOURCE" add a.txt
git -C "$SOURCE" commit -m "add alpha" >/dev/null
OLD_SHA="$(git -C "$SOURCE" rev-parse HEAD)"
mkdir -p "$SOURCE/nested"
printf 'beta\n' >"$SOURCE/nested/b.txt"
printf '%s\n' "$OLD_SHA" >"$SOURCE/evidence.sha"
git -C "$SOURCE" add nested/b.txt evidence.sha
git -C "$SOURCE" commit -m "add beta and evidence binding" >/dev/null
SOURCE_HEAD="$(git -C "$SOURCE" rev-parse HEAD)"

git init -b main "$TARGET_ROOT" >/dev/null
git -C "$TARGET_ROOT" config user.name "Ordivon Migration Test"
git -C "$TARGET_ROOT" config user.email "migration-test@localhost"
mkdir -p "$TARGET_ROOT/docs/migration/receipts"
printf '# target\n' >"$TARGET_ROOT/README.md"
git -C "$TARGET_ROOT" add README.md
git -C "$TARGET_ROOT" commit -m "initialize target" >/dev/null
TARGET_BEFORE="$(git -C "$TARGET_ROOT" rev-parse HEAD)"

"$IMPORTER" preserve-sample "$SOURCE" "$SOURCE_HEAD" services/sample "$TARGET_ROOT"

TARGET_AFTER="$(git -C "$TARGET_ROOT" rev-parse HEAD)"
test "$TARGET_AFTER" != "$TARGET_BEFORE"
test "$(git -C "$TARGET_ROOT" rev-list --parents -n1 "$TARGET_AFTER" | awk '{print NF}')" -eq 3
git -C "$TARGET_ROOT" merge-base --is-ancestor "$SOURCE_HEAD" "$TARGET_AFTER"
git -C "$TARGET_ROOT" merge-base --is-ancestor "$OLD_SHA" "$TARGET_AFTER"
test "$(git -C "$TARGET_ROOT" show "$OLD_SHA:a.txt")" = "alpha"

test -f "$TARGET_ROOT/services/sample/a.txt"
test -f "$TARGET_ROOT/services/sample/nested/b.txt"
test "$(cat "$TARGET_ROOT/services/sample/evidence.sha")" = "$OLD_SHA"
test ! -e "$TARGET_ROOT/a.txt"

git -C "$SOURCE" ls-tree -r "$SOURCE_HEAD" >"$TMP_ROOT/source.tree"
git -C "$TARGET_ROOT" ls-tree -r "$TARGET_AFTER:services/sample" >"$TMP_ROOT/imported.tree"
cmp "$TMP_ROOT/source.tree" "$TMP_ROOT/imported.tree"

git -C "$SOURCE" bundle verify "$BACKUP" >/dev/null
RECEIPT="$TARGET_ROOT/docs/migration/receipts/preserve-sample.md"
MAP="$TARGET_ROOT/docs/migration/receipts/preserve-sample.commit-map"
test -s "$RECEIPT"
test -s "$MAP"
grep -F "$SOURCE_HEAD $SOURCE_HEAD" "$MAP" >/dev/null
grep -F "$SOURCE_HEAD" "$RECEIPT" >/dev/null
grep -F 'historyMode: identity-preserving-merge' "$RECEIPT" >/dev/null

echo "PASS preserve-history import smoke"
