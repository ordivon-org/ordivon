#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
HELPER="$SCRIPT_DIR/supersede-owner-preserve-history.sh"
ROOT="$(mktemp -d /root/ordivon-migration-tmp/supersession-test.XXXXXX)"
trap 'rm -rf "$ROOT"' EXIT
SOURCE="$ROOT/source"
TARGET="$ROOT/target"
BUNDLE="$ROOT/current.bundle"

git init -q -b main "$SOURCE"
git -C "$SOURCE" config user.name test
git -C "$SOURCE" config user.email test@example.invalid
printf 'base\n' >"$SOURCE/a.txt"
git -C "$SOURCE" add a.txt
git -C "$SOURCE" commit -q -m base
BASE="$(git -C "$SOURCE" rev-parse HEAD)"

git -C "$SOURCE" switch -q -c migration
printf 'migration\n' >"$SOURCE/a.txt"
git -C "$SOURCE" commit -qam migration
PREVIOUS="$(git -C "$SOURCE" rev-parse HEAD)"

git -C "$SOURCE" switch -q main
printf 'current\n' >"$SOURCE/a.txt"
mkdir "$SOURCE/new"
printf 'value\n' >"$SOURCE/new/b.txt"
git -C "$SOURCE" add a.txt new/b.txt
git -C "$SOURCE" commit -q -m current
CURRENT="$(git -C "$SOURCE" rev-parse HEAD)"
git -C "$SOURCE" bundle create "$BUNDLE" --all

git init -q -b main "$TARGET"
git -C "$TARGET" config user.name test
git -C "$TARGET" config user.email test@example.invalid
printf '# root\n' >"$TARGET/README.md"
git -C "$TARGET" add README.md
git -C "$TARGET" commit -q -m root
ROOT_BEFORE="$(git -C "$TARGET" rev-parse HEAD)"
git -C "$TARGET" fetch -q "$BUNDLE" "refs/heads/migration:refs/ordivon/import-sources/sample"
git -C "$TARGET" read-tree --reset "$ROOT_BEFORE"
git -C "$TARGET" read-tree --prefix=services/sample/ "$PREVIOUS^{tree}"
IMPORT_TREE="$(git -C "$TARGET" write-tree)"
IMPORT_COMMIT="$(
  printf 'import migration branch\n' |
    git -C "$TARGET" commit-tree "$IMPORT_TREE" -p "$ROOT_BEFORE" -p "$PREVIOUS"
)"
git -C "$TARGET" reset --hard -q "$IMPORT_COMMIT"
git -C "$TARGET" update-ref -d refs/ordivon/import-sources/sample
mkdir -p "$TARGET/docs/migration/receipts"
printf '# original receipt\n' >"$TARGET/docs/migration/receipts/sample.md"
git -C "$TARGET" add docs/migration/receipts/sample.md
git -C "$TARGET" commit -q -m receipt
ORIGINAL_RECEIPT_SHA="$(sha256sum "$TARGET/docs/migration/receipts/sample.md" | awk '{print $1}')"

"$HELPER" sample "$BUNDLE" refs/heads/main "$CURRENT" "$PREVIOUS" "$BASE" services/sample "$TARGET" \
  >"$ROOT/success.out" 2>"$ROOT/success.err"
if grep -E '(^|[[:space:]])(fatal|error):' "$ROOT/success.err" >/dev/null; then
  cat "$ROOT/success.err" >&2
  exit 1
fi
cat "$ROOT/success.out"

AFTER="$(git -C "$TARGET" rev-parse HEAD)"
git -C "$TARGET" merge-base --is-ancestor "$PREVIOUS" "$AFTER"
git -C "$TARGET" merge-base --is-ancestor "$CURRENT" "$AFTER"
git -C "$TARGET" merge-base --is-ancestor "$BASE" "$AFTER"
test "$(git -C "$TARGET" rev-parse HEAD:services/sample)" = "$(git -C "$SOURCE" rev-parse "$CURRENT^{tree}")"
test "$(cat "$TARGET/services/sample/a.txt")" = current
test "$(cat "$TARGET/services/sample/new/b.txt")" = value
test "$(cat "$TARGET/README.md")" = '# root'
test "$(sha256sum "$TARGET/docs/migration/receipts/sample.md" | awk '{print $1}')" = "$ORIGINAL_RECEIPT_SHA"
grep -F 'historyMode: identity-preserving-supersession' "$TARGET/docs/migration/receipts/sample.supersession.md" >/dev/null
grep -F "$PREVIOUS" "$TARGET/docs/migration/receipts/sample.supersession.md" >/dev/null
grep -F "$CURRENT" "$TARGET/docs/migration/receipts/sample.supersession.md" >/dev/null
grep -F "$BASE" "$TARGET/docs/migration/receipts/sample.supersession.md" >/dev/null

git -C "$TARGET" add docs/migration/receipts/sample.supersession.md docs/migration/receipts/sample.supersession.commit-map
git -C "$TARGET" commit -q -m supersession-receipt

printf 'diverged\n' >"$TARGET/services/sample/a.txt"
git -C "$TARGET" add services/sample/a.txt
git -C "$TARGET" commit -q -m diverge
set +e
"$HELPER" sample "$BUNDLE" refs/heads/main "$CURRENT" "$PREVIOUS" "$BASE" services/sample "$TARGET" \
  >"$ROOT/diverge.out" 2>"$ROOT/diverge.err"
RC=$?
set -e
test "$RC" -ne 0

# A linear update must be rejected as a supersession.
LINEAR_BUNDLE="$ROOT/linear.bundle"
git -C "$SOURCE" branch linear "$CURRENT"
git -C "$SOURCE" bundle create "$LINEAR_BUNDLE" refs/heads/linear
set +e
"$HELPER" sample "$LINEAR_BUNDLE" refs/heads/linear "$CURRENT" "$BASE" "$BASE" services/sample "$TARGET" \
  >"$ROOT/linear.out" 2>"$ROOT/linear.err"
LINEAR_RC=$?
set -e
test "$LINEAR_RC" -ne 0

echo 'PASS identity-preserving owner supersession smoke'
