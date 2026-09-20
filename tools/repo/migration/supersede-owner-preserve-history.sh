#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 8 ]; then
  echo "usage: $0 ID BUNDLE SOURCE_REF NEW_REVISION PREVIOUS_IMPORTED_REVISION COMMON_BASE TARGET TARGET_ROOT" >&2
  exit 64
fi

ID=$1
BUNDLE=$2
SOURCE_REF=$3
NEW_REVISION=$4
PREVIOUS_IMPORTED_REVISION=$5
COMMON_BASE=$6
TARGET=$7
TARGET_ROOT=$8
TEMP_REF="refs/ordivon/supersession-sources/$ID"
RECEIPT_DIR="$TARGET_ROOT/docs/migration/receipts"

case "$ID" in
  *[!A-Za-z0-9._-]*|'') echo "invalid ID: $ID" >&2; exit 64 ;;
esac
case "$TARGET" in
  /*|''|../*|*/../*|*/..) echo "invalid TARGET: $TARGET" >&2; exit 64 ;;
esac
case "$SOURCE_REF" in
  refs/*) SOURCE_REF_FULL="$SOURCE_REF" ;;
  *) SOURCE_REF_FULL="refs/heads/$SOURCE_REF" ;;
esac

git -C "$TARGET_ROOT" rev-parse --is-inside-work-tree >/dev/null
test -z "$(git -C "$TARGET_ROOT" status --porcelain)" || {
  echo "target repository must be clean" >&2
  exit 65
}
test -d "$TARGET_ROOT/$TARGET" || {
  echo "target path does not exist: $TARGET_ROOT/$TARGET" >&2
  exit 65
}
test -f "$BUNDLE" || {
  echo "verified bundle is required: $BUNDLE" >&2
  exit 66
}
git -C "$TARGET_ROOT" bundle verify "$BUNDLE" >/dev/null 2>&1
BUNDLE_HEAD="$(git bundle list-heads "$BUNDLE" "$SOURCE_REF_FULL" | awk 'NR == 1 { print $1 }')"
test "$BUNDLE_HEAD" = "$NEW_REVISION" || {
  echo "bundle ref mismatch: ref=$SOURCE_REF_FULL expected=$NEW_REVISION actual=$BUNDLE_HEAD" >&2
  exit 66
}

git -C "$TARGET_ROOT" cat-file -e "$PREVIOUS_IMPORTED_REVISION^{commit}"
git -C "$TARGET_ROOT" cat-file -e "$COMMON_BASE^{commit}"
git -C "$TARGET_ROOT" merge-base --is-ancestor "$PREVIOUS_IMPORTED_REVISION" HEAD || {
  echo "previous imported revision is not retained by current monorepo history" >&2
  exit 67
}

if git -C "$TARGET_ROOT" merge-base --is-ancestor "$PREVIOUS_IMPORTED_REVISION" "$NEW_REVISION"; then
  echo "previous revision is an ancestor of new revision; use identity-preserving update, not supersession" >&2
  exit 67
fi
if git -C "$TARGET_ROOT" merge-base --is-ancestor "$NEW_REVISION" "$PREVIOUS_IMPORTED_REVISION"; then
  echo "new revision is already an ancestor of previous revision; supersession would move backward" >&2
  exit 67
fi
git -C "$TARGET_ROOT" merge-base --is-ancestor "$COMMON_BASE" "$PREVIOUS_IMPORTED_REVISION" || {
  echo "common base is not an ancestor of previous imported revision" >&2
  exit 67
}

if git -C "$TARGET_ROOT" show-ref --verify --quiet "$TEMP_REF"; then
  echo "temporary supersession ref already exists: $TEMP_REF" >&2
  exit 65
fi

cleanup() {
  git -C "$TARGET_ROOT" update-ref -d "$TEMP_REF" >/dev/null 2>&1 || true
  [ -z "${INDEX_FILE:-}" ] || rm -f "$INDEX_FILE"
}
trap cleanup EXIT

git -C "$TARGET_ROOT" fetch --no-tags "$BUNDLE" "$SOURCE_REF_FULL:$TEMP_REF" >/dev/null
test "$(git -C "$TARGET_ROOT" rev-parse "$TEMP_REF")" = "$NEW_REVISION"
git -C "$TARGET_ROOT" merge-base --is-ancestor "$COMMON_BASE" "$NEW_REVISION" || {
  echo "common base is not an ancestor of new revision" >&2
  exit 67
}

PREVIOUS_TREE="$(git -C "$TARGET_ROOT" rev-parse "$PREVIOUS_IMPORTED_REVISION^{tree}")"
CURRENT_SUBTREE="$(git -C "$TARGET_ROOT" rev-parse "HEAD:$TARGET")"
test "$CURRENT_SUBTREE" = "$PREVIOUS_TREE" || {
  echo "target subtree diverged from previous imported revision" >&2
  echo "target=$CURRENT_SUBTREE previous=$PREVIOUS_TREE" >&2
  exit 68
}

NEW_TREE="$(git -C "$TARGET_ROOT" rev-parse "$NEW_REVISION^{tree}")"
TARGET_BEFORE="$(git -C "$TARGET_ROOT" rev-parse HEAD)"
INDEX_FILE="$(mktemp /root/ordivon-migration-tmp/supersession-index.XXXXXX)"
rm -f "$INDEX_FILE"
GIT_INDEX_FILE="$INDEX_FILE" git -C "$TARGET_ROOT" read-tree "$TARGET_BEFORE"
GIT_INDEX_FILE="$INDEX_FILE" git -C "$TARGET_ROOT" rm -r --cached -q -- "$TARGET"
GIT_INDEX_FILE="$INDEX_FILE" git -C "$TARGET_ROOT" read-tree --prefix="$TARGET/" "$TEMP_REF^{tree}"
MERGE_TREE="$(GIT_INDEX_FILE="$INDEX_FILE" git -C "$TARGET_ROOT" write-tree)"
SUPERSESSION_REVISION="$(
  printf 'chore: supersede %s identity-preserving source under %s\n' "$ID" "$TARGET" |
    git -C "$TARGET_ROOT" commit-tree "$MERGE_TREE" -p "$TARGET_BEFORE" -p "$NEW_REVISION"
)"

test "$(git -C "$TARGET_ROOT" rev-parse "$SUPERSESSION_REVISION:$TARGET")" = "$NEW_TREE"
git -C "$TARGET_ROOT" merge-base --is-ancestor "$PREVIOUS_IMPORTED_REVISION" "$SUPERSESSION_REVISION"
git -C "$TARGET_ROOT" merge-base --is-ancestor "$NEW_REVISION" "$SUPERSESSION_REVISION"
git -C "$TARGET_ROOT" merge-base --is-ancestor "$COMMON_BASE" "$SUPERSESSION_REVISION"

mkdir -p "$RECEIPT_DIR"
BUNDLE_SHA="$(sha256sum "$BUNDLE" | awk '{print $1}')"
RECEIPT="$RECEIPT_DIR/$ID.supersession.md"
MAP="$RECEIPT_DIR/$ID.supersession.commit-map"
test ! -e "$RECEIPT" || {
  echo "supersession receipt already exists: $RECEIPT" >&2
  exit 69
}
test ! -e "$MAP" || {
  echo "supersession commit map already exists: $MAP" >&2
  exit 69
}

git -C "$TARGET_ROOT" reset --hard "$SUPERSESSION_REVISION" >/dev/null
git -C "$TARGET_ROOT" rev-list "$NEW_REVISION" | sort | awk '{print $1 " " $1}' >"$MAP"
cat >"$RECEIPT" <<EOF
# Monorepo identity-preserving supersession receipt: $ID

- historyMode: identity-preserving-supersession
- Previous imported revision: $PREVIOUS_IMPORTED_REVISION
- Superseding source revision: $NEW_REVISION
- Common base: $COMMON_BASE
- Source advertised ref: $SOURCE_REF_FULL
- Supersession revision: $SUPERSESSION_REVISION
- Target path: $TARGET
- Previous source tree: $PREVIOUS_TREE
- Superseding source tree: $NEW_TREE
- Bundle: $BUNDLE
- Bundle SHA-256: $BUNDLE_SHA
- Previous import receipt retained at: docs/migration/receipts/$ID.md
- Production cutover: NOT PERFORMED
EOF

cleanup
trap - EXIT

printf 'superseded %s\nprevious=%s\nsource=%s\ncommon_base=%s\nmerge=%s\ntarget=%s\nbundle_sha256=%s\n' \
  "$ID" "$PREVIOUS_IMPORTED_REVISION" "$NEW_REVISION" "$COMMON_BASE" \
  "$SUPERSESSION_REVISION" "$TARGET" "$BUNDLE_SHA"
