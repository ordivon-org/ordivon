#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 7 ]; then
  echo "usage: $0 ID BUNDLE SOURCE_REF REVISION PREVIOUS_REVISION TARGET TARGET_ROOT" >&2
  exit 64
fi

ID=$1
BUNDLE=$2
SOURCE_REF=$3
REVISION=$4
PREVIOUS_REVISION=$5
TARGET=$6
TARGET_ROOT=$7
TEMP_REF="refs/ordivon/update-sources/$ID"
RECEIPT_DIR="$TARGET_ROOT/docs/migration/receipts"
INDEX_FILE=""

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
test "$BUNDLE_HEAD" = "$REVISION" || {
  echo "bundle ref mismatch: ref=$SOURCE_REF_FULL expected=$REVISION actual=$BUNDLE_HEAD" >&2
  exit 66
}
if git -C "$TARGET_ROOT" show-ref --verify --quiet "$TEMP_REF"; then
  echo "temporary update ref already exists: $TEMP_REF" >&2
  exit 65
fi

ORIGINAL_RECEIPT="$RECEIPT_DIR/$ID.md"
ORIGINAL_MAP="$RECEIPT_DIR/$ID.commit-map"
LEGACY_UPDATE_RECEIPT="$RECEIPT_DIR/$ID.update.md"
LEGACY_UPDATE_MAP="$RECEIPT_DIR/$ID.update.commit-map"
test -f "$ORIGINAL_RECEIPT" || {
  echo "original import receipt is required: $ORIGINAL_RECEIPT" >&2
  exit 69
}

# Preserve the historical first-update filename for compatibility. Every later
# update is content-addressed by the exact accepted source revision so receipt
# identity is deterministic, append-only, and independent of update counters.
if [ ! -e "$LEGACY_UPDATE_RECEIPT" ] && [ ! -e "$LEGACY_UPDATE_MAP" ]; then
  UPDATE_RECEIPT="$LEGACY_UPDATE_RECEIPT"
  UPDATE_MAP="$LEGACY_UPDATE_MAP"
else
  test -f "$LEGACY_UPDATE_RECEIPT" && test -f "$LEGACY_UPDATE_MAP" || {
    echo "legacy update receipt/map pair is incomplete for $ID" >&2
    exit 69
  }
  UPDATE_RECEIPT="$RECEIPT_DIR/$ID.update-$REVISION.md"
  UPDATE_MAP="$RECEIPT_DIR/$ID.update-$REVISION.commit-map"
fi

test ! -e "$UPDATE_RECEIPT" || {
  echo "update receipt already exists: $UPDATE_RECEIPT" >&2
  exit 69
}
test ! -e "$UPDATE_MAP" || {
  echo "update commit map already exists: $UPDATE_MAP" >&2
  exit 69
}

ORIGINAL_RECEIPT_SHA="$(sha256sum "$ORIGINAL_RECEIPT" | awk '{print $1}')"
if [ -f "$ORIGINAL_MAP" ]; then
  ORIGINAL_MAP_SHA="$(sha256sum "$ORIGINAL_MAP" | awk '{print $1}')"
else
  ORIGINAL_MAP_SHA=""
fi
PRIOR_UPDATE_MANIFEST="$(mktemp /root/ordivon-migration-tmp/update-prior-receipts.XXXXXX)"
find "$RECEIPT_DIR" -maxdepth 1 -type f   \( -name "$ID.update*.md" -o -name "$ID.update*.commit-map" \)   -print0 | sort -z | xargs -0 -r sha256sum >"$PRIOR_UPDATE_MANIFEST"

cleanup() {
  git -C "$TARGET_ROOT" update-ref -d "$TEMP_REF" >/dev/null 2>&1 || true
  if [ -n "$INDEX_FILE" ]; then rm -f "$INDEX_FILE"; fi
  if [ -n "$PRIOR_UPDATE_MANIFEST" ]; then rm -f "$PRIOR_UPDATE_MANIFEST"; fi
}
trap cleanup EXIT

git -C "$TARGET_ROOT" fetch --no-tags "$BUNDLE" "$SOURCE_REF_FULL:$TEMP_REF" >/dev/null
FETCHED="$(git -C "$TARGET_ROOT" rev-parse "$TEMP_REF")"
test "$FETCHED" = "$REVISION"

git -C "$TARGET_ROOT" cat-file -e "$PREVIOUS_REVISION^{commit}"
git -C "$TARGET_ROOT" merge-base --is-ancestor "$PREVIOUS_REVISION" "$REVISION" || {
  echo "new source revision does not descend from previous revision" >&2
  exit 67
}
if [ "$PREVIOUS_REVISION" = "$REVISION" ]; then
  echo "new source revision equals previous revision; update is a no-op" >&2
  exit 67
fi

CURRENT_SUBTREE="$(git -C "$TARGET_ROOT" rev-parse "HEAD:$TARGET")"
PREVIOUS_TREE="$(git -C "$TARGET_ROOT" rev-parse "$PREVIOUS_REVISION^{tree}")"
test "$CURRENT_SUBTREE" = "$PREVIOUS_TREE" || {
  echo "target subtree diverged from previous source tree" >&2
  echo "target=$CURRENT_SUBTREE previous=$PREVIOUS_TREE" >&2
  exit 68
}

NEW_TREE="$(git -C "$TARGET_ROOT" rev-parse "$REVISION^{tree}")"
TARGET_BEFORE="$(git -C "$TARGET_ROOT" rev-parse HEAD)"
INDEX_FILE="$(mktemp /root/ordivon-migration-tmp/update-index.XXXXXX)"
rm -f "$INDEX_FILE"
GIT_INDEX_FILE="$INDEX_FILE" git -C "$TARGET_ROOT" read-tree "$TARGET_BEFORE"
GIT_INDEX_FILE="$INDEX_FILE" git -C "$TARGET_ROOT" rm -r --cached -q -- "$TARGET"
GIT_INDEX_FILE="$INDEX_FILE" git -C "$TARGET_ROOT" read-tree --prefix="$TARGET/" "$TEMP_REF^{tree}"
MERGE_TREE="$(GIT_INDEX_FILE="$INDEX_FILE" git -C "$TARGET_ROOT" write-tree)"
MERGE_REVISION="$(
  printf 'chore: update %s identity-preserving history under %s\n' "$ID" "$TARGET" |
    git -C "$TARGET_ROOT" commit-tree "$MERGE_TREE" -p "$TARGET_BEFORE" -p "$REVISION"
)"

test "$(git -C "$TARGET_ROOT" rev-parse "$MERGE_REVISION:$TARGET")" = "$NEW_TREE"
git -C "$TARGET_ROOT" merge-base --is-ancestor "$REVISION" "$MERGE_REVISION"
git -C "$TARGET_ROOT" merge-base --is-ancestor "$PREVIOUS_REVISION" "$MERGE_REVISION"

mkdir -p "$RECEIPT_DIR"
BUNDLE_SHA="$(sha256sum "$BUNDLE" | awk '{print $1}')"
git -C "$TARGET_ROOT" reset --hard "$MERGE_REVISION" >/dev/null

git -C "$TARGET_ROOT" rev-list "$REVISION" | sort | awk '{print $1 " " $1}' >"$UPDATE_MAP"
cat >"$UPDATE_RECEIPT" <<EOF
# Monorepo identity-preserving update receipt: $ID

- historyMode: identity-preserving-update
- Previous source revision: $PREVIOUS_REVISION
- Source revision: $REVISION
- Source advertised ref: $SOURCE_REF_FULL
- Merge revision: $MERGE_REVISION
- Target path: $TARGET
- Previous source tree: $PREVIOUS_TREE
- Source tree: $NEW_TREE
- Bundle: $BUNDLE
- Bundle SHA-256: $BUNDLE_SHA
- Previous import receipt retained at: docs/migration/receipts/$ID.md
- Production cutover: NOT PERFORMED
EOF

test "$(sha256sum "$ORIGINAL_RECEIPT" | awk '{print $1}')" = "$ORIGINAL_RECEIPT_SHA"
if [ -n "$ORIGINAL_MAP_SHA" ]; then
  test "$(sha256sum "$ORIGINAL_MAP" | awk '{print $1}')" = "$ORIGINAL_MAP_SHA"
fi

CURRENT_PRIOR_UPDATE_MANIFEST="$(mktemp /root/ordivon-migration-tmp/update-prior-receipts-current.XXXXXX)"
find "$RECEIPT_DIR" -maxdepth 1 -type f   \( -name "$ID.update*.md" -o -name "$ID.update*.commit-map" \)   ! -path "$UPDATE_RECEIPT" ! -path "$UPDATE_MAP"   -print0 | sort -z | xargs -0 -r sha256sum >"$CURRENT_PRIOR_UPDATE_MANIFEST"
cmp "$PRIOR_UPDATE_MANIFEST" "$CURRENT_PRIOR_UPDATE_MANIFEST"
rm -f "$CURRENT_PRIOR_UPDATE_MANIFEST"

cleanup
trap - EXIT

printf 'updated %s\nprevious=%s\nsource=%s\nmerge=%s\ntarget=%s\nbundle_sha256=%s\n'   "$ID" "$PREVIOUS_REVISION" "$REVISION" "$MERGE_REVISION" "$TARGET" "$BUNDLE_SHA"
