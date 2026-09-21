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

FIRST_UPDATE_RECEIPT_SHA="$(sha256sum "$TARGET/docs/migration/receipts/sample.update.md" | awk '{print $1}')"
FIRST_UPDATE_MAP_SHA="$(sha256sum "$TARGET/docs/migration/receipts/sample.update.commit-map" | awk '{print $1}')"
git -C "$TARGET" add docs/migration/receipts/sample.update.md docs/migration/receipts/sample.update.commit-map
git -C "$TARGET" commit -q -m update-receipt

# A second linear update appends a deterministic content-addressed receipt
# without overwriting the legacy first-update evidence.
printf 'three\n' >"$SOURCE/a.txt"
printf 'gamma\n' >"$SOURCE/nested/c.txt"
git -C "$SOURCE" add a.txt nested/c.txt
git -C "$SOURCE" commit -q -m three
THIRD="$(git -C "$SOURCE" rev-parse HEAD)"
SECOND_BUNDLE="$TMP/source-second.bundle"
git -C "$SOURCE" bundle create "$SECOND_BUNDLE" refs/heads/main

"$UPDATER" sample "$SECOND_BUNDLE" refs/heads/main "$THIRD" "$CURRENT" services/sample "$TARGET"

SECOND_RECEIPT="$TARGET/docs/migration/receipts/sample.update-$THIRD.md"
SECOND_MAP="$TARGET/docs/migration/receipts/sample.update-$THIRD.commit-map"
test -s "$SECOND_RECEIPT"
test -s "$SECOND_MAP"
grep -F 'historyMode: identity-preserving-update' "$SECOND_RECEIPT" >/dev/null
grep -F "$CURRENT" "$SECOND_RECEIPT" >/dev/null
grep -F "$THIRD" "$SECOND_RECEIPT" >/dev/null
grep -F "$THIRD $THIRD" "$SECOND_MAP" >/dev/null
test "$(git -C "$TARGET" rev-parse HEAD:services/sample)" = "$(git -C "$SOURCE" rev-parse "$THIRD^{tree}")"
test "$(cat "$TARGET/services/sample/a.txt")" = three
test "$(cat "$TARGET/services/sample/nested/c.txt")" = gamma
test "$(sha256sum "$TARGET/docs/migration/receipts/sample.update.md" | awk '{print $1}')" = "$FIRST_UPDATE_RECEIPT_SHA"
test "$(sha256sum "$TARGET/docs/migration/receipts/sample.update.commit-map" | awk '{print $1}')" = "$FIRST_UPDATE_MAP_SHA"

git -C "$TARGET" add "$SECOND_RECEIPT" "$SECOND_MAP"
git -C "$TARGET" commit -q -m second-update-receipt

# Exact replay of the same second update collides with deterministic receipt
# identity instead of overwriting evidence or inventing r3 naming.
set +e
"$UPDATER" sample "$SECOND_BUNDLE" refs/heads/main "$THIRD" "$CURRENT" services/sample "$TARGET"   >"$TMP/replay.out" 2>"$TMP/replay.err"
replay_rc=$?
set -e
test "$replay_rc" -eq 69
grep -F "update receipt already exists: $SECOND_RECEIPT" "$TMP/replay.err" >/dev/null

# Divergence still fails on owner-tree identity before emitting a new receipt.
printf 'four\n' >"$SOURCE/a.txt"
git -C "$SOURCE" add a.txt
git -C "$SOURCE" commit -q -m four
FOURTH="$(git -C "$SOURCE" rev-parse HEAD)"
THIRD_BUNDLE="$TMP/source-third.bundle"
git -C "$SOURCE" bundle create "$THIRD_BUNDLE" refs/heads/main

printf 'local divergence\n' >"$TARGET/services/sample/a.txt"
git -C "$TARGET" add services/sample/a.txt
git -C "$TARGET" commit -q -m diverge
set +e
"$UPDATER" sample "$THIRD_BUNDLE" refs/heads/main "$FOURTH" "$THIRD" services/sample "$TARGET"   >"$TMP/diverge.out" 2>"$TMP/diverge.err"
rc=$?
set -e
test "$rc" -eq 68
grep -F 'target subtree diverged from previous source tree' "$TMP/diverge.err" >/dev/null

echo 'PASS repeatable identity-preserving owner update smoke'
