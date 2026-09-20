#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
UPDATER="$SCRIPT_DIR/update-owner-preserve-history.sh"
TMP="$(mktemp -d /root/ordivon-migration-tmp/update-owner-test.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
SOURCE="$TMP/source"
TARGET="$TMP/target"
BUNDLE="$TMP/source.bundle"

git init -q -b main "$SOURCE"
git -C "$SOURCE" config user.name test
git -C "$SOURCE" config user.email test@example.invalid
printf 'one\n' >"$SOURCE/a.txt"
git -C "$SOURCE" add a.txt
git -C "$SOURCE" commit -q -m one
PREVIOUS="$(git -C "$SOURCE" rev-parse HEAD)"
printf 'two\n' >"$SOURCE/a.txt"
mkdir "$SOURCE/nested"
printf 'beta\n' >"$SOURCE/nested/b.txt"
git -C "$SOURCE" add a.txt nested/b.txt
git -C "$SOURCE" commit -q -m two
CURRENT="$(git -C "$SOURCE" rev-parse HEAD)"
git -C "$SOURCE" bundle create "$BUNDLE" refs/heads/main

git init -q -b main "$TARGET"
git -C "$TARGET" config user.name test
git -C "$TARGET" config user.email test@example.invalid
printf '# root\n' >"$TARGET/README.md"
git -C "$TARGET" add README.md
git -C "$TARGET" commit -q -m root
ROOT_BEFORE="$(git -C "$TARGET" rev-parse HEAD)"
git -C "$TARGET" fetch -q "$BUNDLE" "$PREVIOUS:refs/ordivon/import-sources/sample"
git -C "$TARGET" read-tree --reset "$ROOT_BEFORE"
git -C "$TARGET" read-tree --prefix=services/sample/ "$PREVIOUS^{tree}"
IMPORT_TREE="$(git -C "$TARGET" write-tree)"
IMPORT_COMMIT="$(
  printf 'import sample\n' |
    git -C "$TARGET" commit-tree "$IMPORT_TREE" -p "$ROOT_BEFORE" -p "$PREVIOUS"
)"
git -C "$TARGET" reset --hard -q "$IMPORT_COMMIT"
git -C "$TARGET" update-ref -d refs/ordivon/import-sources/sample
mkdir -p "$TARGET/docs/migration/receipts"
printf '# original receipt\n' >"$TARGET/docs/migration/receipts/sample.md"
printf '%s %s\n' "$PREVIOUS" "$PREVIOUS" >"$TARGET/docs/migration/receipts/sample.commit-map"
git -C "$TARGET" add docs/migration/receipts/sample.md docs/migration/receipts/sample.commit-map
git -C "$TARGET" commit -q -m receipt
ORIGINAL_RECEIPT_SHA="$(sha256sum "$TARGET/docs/migration/receipts/sample.md" | awk '{print $1}')"
ORIGINAL_MAP_SHA="$(sha256sum "$TARGET/docs/migration/receipts/sample.commit-map" | awk '{print $1}')"

"$UPDATER" sample "$BUNDLE" refs/heads/main "$CURRENT" "$PREVIOUS" services/sample "$TARGET"

UPDATED="$(git -C "$TARGET" rev-parse HEAD)"
git -C "$TARGET" merge-base --is-ancestor "$PREVIOUS" "$UPDATED"
git -C "$TARGET" merge-base --is-ancestor "$CURRENT" "$UPDATED"
test "$(git -C "$TARGET" rev-parse HEAD:services/sample)" = "$(git -C "$SOURCE" rev-parse "$CURRENT^{tree}")"
test "$(cat "$TARGET/services/sample/a.txt")" = two
test "$(cat "$TARGET/services/sample/nested/b.txt")" = beta
test "$(cat "$TARGET/README.md")" = '# root'
test "$(sha256sum "$TARGET/docs/migration/receipts/sample.md" | awk '{print $1}')" = "$ORIGINAL_RECEIPT_SHA"
test "$(sha256sum "$TARGET/docs/migration/receipts/sample.commit-map" | awk '{print $1}')" = "$ORIGINAL_MAP_SHA"
test -s "$TARGET/docs/migration/receipts/sample.update.md"
test -s "$TARGET/docs/migration/receipts/sample.update.commit-map"
grep -F 'historyMode: identity-preserving-update' "$TARGET/docs/migration/receipts/sample.update.md" >/dev/null
grep -F "$PREVIOUS" "$TARGET/docs/migration/receipts/sample.update.md" >/dev/null
grep -F "$CURRENT" "$TARGET/docs/migration/receipts/sample.update.md" >/dev/null
grep -F "$CURRENT $CURRENT" "$TARGET/docs/migration/receipts/sample.update.commit-map" >/dev/null

git -C "$TARGET" add docs/migration/receipts/sample.update.md docs/migration/receipts/sample.update.commit-map
git -C "$TARGET" commit -q -m update-receipt

printf 'local divergence\n' >"$TARGET/services/sample/a.txt"
git -C "$TARGET" add services/sample/a.txt
git -C "$TARGET" commit -q -m diverge
set +e
"$UPDATER" sample "$BUNDLE" refs/heads/main "$CURRENT" "$PREVIOUS" services/sample "$TARGET"   >"$TMP/diverge.out" 2>"$TMP/diverge.err"
rc=$?
set -e
test "$rc" -ne 0

echo 'PASS identity-preserving owner update smoke'
