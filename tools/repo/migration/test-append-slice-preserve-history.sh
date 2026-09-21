#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
HELPER="$SCRIPT_DIR/append-slice-preserve-history.sh"
TMP="$(mktemp -d /root/ordivon-migration-tmp/append-slice-test.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

SOURCE="$TMP/source"
TARGET="$TMP/target"
COLLISION_TARGET="$TMP/collision-target"
BUNDLE="$TMP/source.bundle"

git init -q -b main "$SOURCE"
git -C "$SOURCE" config user.name test
git -C "$SOURCE" config user.email test@example.invalid
mkdir -p "$SOURCE/artifacts/library" "$SOURCE/scripts"
printf 'slice\n' >"$SOURCE/artifacts/library/a.json"
printf 'code\n' >"$SOURCE/scripts/a.py"
git -C "$SOURCE" add .
git -C "$SOURCE" commit -q -m slice
SOURCE_HEAD="$(git -C "$SOURCE" rev-parse HEAD)"
git -C "$SOURCE" bundle create "$BUNDLE" refs/heads/main

git init -q -b main "$TARGET"
git -C "$TARGET" config user.name test
git -C "$TARGET" config user.email test@example.invalid
mkdir -p "$TARGET/capabilities/media" "$TARGET/docs/migration/receipts"
printf 'host\n' >"$TARGET/capabilities/media/host.txt"
printf '# root\n' >"$TARGET/README.md"
git -C "$TARGET" add .
git -C "$TARGET" commit -q -m root
BEFORE="$(git -C "$TARGET" rev-parse HEAD)"
HOST_BLOB="$(git -C "$TARGET" rev-parse HEAD:capabilities/media/host.txt)"

"$HELPER" sample "$BUNDLE" refs/heads/main "$SOURCE_HEAD" capabilities/media "$TARGET"

AFTER="$(git -C "$TARGET" rev-parse HEAD)"
git -C "$TARGET" merge-base --is-ancestor "$SOURCE_HEAD" "$AFTER"
git -C "$TARGET" merge-base --is-ancestor "$BEFORE" "$AFTER"
test "$(git -C "$TARGET" rev-parse HEAD:capabilities/media/host.txt)" = "$HOST_BLOB"
test "$(cat "$TARGET/capabilities/media/artifacts/library/a.json")" = slice
test "$(cat "$TARGET/capabilities/media/scripts/a.py")" = code
test -s "$TARGET/docs/migration/receipts/sample.slice.md"
test -s "$TARGET/docs/migration/receipts/sample.slice.commit-map"
grep -F 'historyMode: identity-preserving-append-only-slice' "$TARGET/docs/migration/receipts/sample.slice.md" >/dev/null
grep -F "$SOURCE_HEAD $SOURCE_HEAD" "$TARGET/docs/migration/receipts/sample.slice.commit-map" >/dev/null

git -C "$TARGET" add docs/migration/receipts
git -C "$TARGET" commit -q -m receipt

git init -q -b main "$COLLISION_TARGET"
git -C "$COLLISION_TARGET" config user.name test
git -C "$COLLISION_TARGET" config user.email test@example.invalid
mkdir -p "$COLLISION_TARGET/capabilities/media/artifacts/library" "$COLLISION_TARGET/docs/migration/receipts"
printf 'already here\n' >"$COLLISION_TARGET/capabilities/media/artifacts/library/a.json"
printf '# root\n' >"$COLLISION_TARGET/README.md"
git -C "$COLLISION_TARGET" add .
git -C "$COLLISION_TARGET" commit -q -m root
COLLISION_BEFORE="$(git -C "$COLLISION_TARGET" rev-parse HEAD)"

set +e
"$HELPER" collision "$BUNDLE" refs/heads/main "$SOURCE_HEAD" capabilities/media "$COLLISION_TARGET" \
  >"$TMP/collision.out" 2>"$TMP/collision.err"
rc=$?
set -e
test "$rc" -eq 68
test "$(git -C "$COLLISION_TARGET" rev-parse HEAD)" = "$COLLISION_BEFORE"
grep -F 'slice path collision: capabilities/media/artifacts/library/a.json' "$TMP/collision.err" >/dev/null

echo 'PASS identity-preserving append-only slice smoke'
