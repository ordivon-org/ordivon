#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
IMPORTER="$SCRIPT_DIR/import-owner.sh"
TMP_ROOT="$(mktemp -d /root/ordivon-migration-tmp/import-owner-test.XXXXXX)"
SOURCE="$TMP_ROOT/source"
TARGET_ROOT="$TMP_ROOT/target"
BACKUP="/root/ordivon-migration-backups/2026-09-20/sample.bundle"
DISPOSABLE="/root/ordivon-migration-tmp/import-sample"

cleanup() {
  rm -rf "$TMP_ROOT" "$DISPOSABLE"
  rm -f "$BACKUP"
}
trap cleanup EXIT

git init -b main "$SOURCE" >/dev/null
git -C "$SOURCE" config user.name "Ordivon Migration Test"
git -C "$SOURCE" config user.email "migration-test@localhost"
printf 'alpha\n' >"$SOURCE/a.txt"
git -C "$SOURCE" add a.txt
git -C "$SOURCE" commit -m "add alpha" >/dev/null
mkdir -p "$SOURCE/nested"
printf 'beta\n' >"$SOURCE/nested/b.txt"
git -C "$SOURCE" add nested/b.txt
git -C "$SOURCE" commit -m "add beta" >/dev/null
SOURCE_HEAD="$(git -C "$SOURCE" rev-parse HEAD)"

git init -b main "$TARGET_ROOT" >/dev/null
git -C "$TARGET_ROOT" config user.name "Ordivon Migration Test"
git -C "$TARGET_ROOT" config user.email "migration-test@localhost"
mkdir -p "$TARGET_ROOT/docs/migration/receipts"
printf '# target\n' >"$TARGET_ROOT/README.md"
git -C "$TARGET_ROOT" add README.md
git -C "$TARGET_ROOT" commit -m "initialize target" >/dev/null

"$IMPORTER" sample "$SOURCE" "$SOURCE_HEAD" platform/sample "$TARGET_ROOT"

test -f "$TARGET_ROOT/platform/sample/a.txt"
test -f "$TARGET_ROOT/platform/sample/nested/b.txt"
test ! -e "$TARGET_ROOT/a.txt"
test ! -e "$TARGET_ROOT/nested/b.txt"

REWRITTEN="$(git -C "$DISPOSABLE" rev-parse import-main)"
git -C "$SOURCE" ls-tree -r "$SOURCE_HEAD" >"$TMP_ROOT/source.tree"
git -C "$TARGET_ROOT" ls-tree -r "$REWRITTEN:platform/sample" >"$TMP_ROOT/rewritten.tree"
cmp "$TMP_ROOT/source.tree" "$TMP_ROOT/rewritten.tree"

git -C "$SOURCE" bundle verify "$BACKUP" >/dev/null

RECEIPT="$TARGET_ROOT/docs/migration/receipts/sample.md"
test -s "$TARGET_ROOT/docs/migration/receipts/sample.commit-map"
grep -F "$SOURCE_HEAD" "$RECEIPT" >/dev/null
grep -F "$REWRITTEN" "$RECEIPT" >/dev/null
grep -F "$(git -C "$TARGET_ROOT" rev-parse HEAD)" "$RECEIPT" >/dev/null
grep -F 'platform/sample' "$RECEIPT" >/dev/null
grep -F "$(sha256sum "$BACKUP" | awk '{print $1}')" "$RECEIPT" >/dev/null

echo "PASS import-owner smoke"
