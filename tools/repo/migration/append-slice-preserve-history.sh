#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 6 ]; then
  echo "usage: $0 ID BUNDLE SOURCE_REF REVISION TARGET_PREFIX TARGET_ROOT" >&2
  exit 64
fi

ID=$1
BUNDLE=$2
SOURCE_REF=$3
REVISION=$4
TARGET_PREFIX=$5
TARGET_ROOT=$6
TEMP_REF="refs/ordivon/slice-sources/$ID"
RECEIPT_DIR="$TARGET_ROOT/docs/migration/receipts"
INDEX_FILE=""

case "$ID" in
  *[!A-Za-z0-9._-]*|'') echo "invalid ID: $ID" >&2; exit 64 ;;
esac
case "$TARGET_PREFIX" in
  /*|''|../*|*/../*|*/..) echo "invalid TARGET_PREFIX: $TARGET_PREFIX" >&2; exit 64 ;;
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
test -d "$TARGET_ROOT/$TARGET_PREFIX" || {
  echo "target prefix does not exist: $TARGET_ROOT/$TARGET_PREFIX" >&2
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
  echo "temporary slice ref already exists: $TEMP_REF" >&2
  exit 65
fi

SLICE_RECEIPT="$RECEIPT_DIR/$ID.slice.md"
SLICE_MAP="$RECEIPT_DIR/$ID.slice.commit-map"
test ! -e "$SLICE_RECEIPT" || {
  echo "slice receipt already exists: $SLICE_RECEIPT" >&2
  exit 69
}
test ! -e "$SLICE_MAP" || {
  echo "slice commit map already exists: $SLICE_MAP" >&2
  exit 69
}

cleanup() {
  git -C "$TARGET_ROOT" update-ref -d "$TEMP_REF" >/dev/null 2>&1 || true
  if [ -n "$INDEX_FILE" ]; then rm -f "$INDEX_FILE"; fi
}
trap cleanup EXIT

git -C "$TARGET_ROOT" fetch --no-tags "$BUNDLE" "$SOURCE_REF_FULL:$TEMP_REF" >/dev/null
test "$(git -C "$TARGET_ROOT" rev-parse "$TEMP_REF")" = "$REVISION"

SOURCE_TREE="$(git -C "$TARGET_ROOT" rev-parse "$REVISION^{tree}")"
SOURCE_PATHS="$(mktemp /root/ordivon-migration-tmp/slice-paths.XXXXXX)"
EXPECTED_DIFF="$(mktemp /root/ordivon-migration-tmp/slice-expected.XXXXXX)"
ACTUAL_DIFF="$(mktemp /root/ordivon-migration-tmp/slice-actual.XXXXXX)"
cleanup_files() {
  rm -f "$SOURCE_PATHS" "$EXPECTED_DIFF" "$ACTUAL_DIFF"
}
trap 'cleanup; cleanup_files' EXIT

git -C "$TARGET_ROOT" ls-tree -r --name-only "$REVISION" | sort >"$SOURCE_PATHS"
test -s "$SOURCE_PATHS" || {
  echo "source slice is empty" >&2
  exit 67
}

collision=0
while IFS= read -r path; do
  case "$path" in
    /*|''|../*|*/../*|*/..) echo "invalid source path: $path" >&2; exit 67 ;;
  esac
  if git -C "$TARGET_ROOT" cat-file -e "HEAD:$TARGET_PREFIX/$path" 2>/dev/null; then
    echo "slice path collision: $TARGET_PREFIX/$path" >&2
    collision=1
  fi
  printf 'A\t%s/%s\n' "$TARGET_PREFIX" "$path" >>"$EXPECTED_DIFF"
done <"$SOURCE_PATHS"
test "$collision" -eq 0 || exit 68
sort -o "$EXPECTED_DIFF" "$EXPECTED_DIFF"

TARGET_BEFORE="$(git -C "$TARGET_ROOT" rev-parse HEAD)"
TARGET_TREE_BEFORE="$(git -C "$TARGET_ROOT" rev-parse "HEAD:$TARGET_PREFIX")"
INDEX_FILE="$(mktemp /root/ordivon-migration-tmp/slice-index.XXXXXX)"
rm -f "$INDEX_FILE"
GIT_INDEX_FILE="$INDEX_FILE" git -C "$TARGET_ROOT" read-tree "$TARGET_BEFORE"
GIT_INDEX_FILE="$INDEX_FILE" git -C "$TARGET_ROOT" read-tree --prefix="$TARGET_PREFIX/" "$TEMP_REF^{tree}"
MERGE_TREE="$(GIT_INDEX_FILE="$INDEX_FILE" git -C "$TARGET_ROOT" write-tree)"
MERGE_REVISION="$(
  printf 'chore: append %s identity-preserving slice under %s\n' "$ID" "$TARGET_PREFIX" |
    git -C "$TARGET_ROOT" commit-tree "$MERGE_TREE" -p "$TARGET_BEFORE" -p "$REVISION"
)"

git -C "$TARGET_ROOT" diff --name-status "$TARGET_BEFORE" "$MERGE_REVISION" | sort >"$ACTUAL_DIFF"
cmp "$EXPECTED_DIFF" "$ACTUAL_DIFF" || {
  echo "slice merge changed paths outside the exact append-only source set" >&2
  diff -u "$EXPECTED_DIFF" "$ACTUAL_DIFF" >&2 || true
  exit 68
}

while IFS= read -r path; do
  source_meta="$(git -C "$TARGET_ROOT" ls-tree "$REVISION" -- "$path" | cut -f1)"
  target_meta="$(git -C "$TARGET_ROOT" ls-tree "$MERGE_REVISION" -- "$TARGET_PREFIX/$path" | cut -f1)"
  test -n "$source_meta"
  test "$source_meta" = "$target_meta" || {
    echo "prefixed slice blob/mode mismatch: $path" >&2
    echo "source=$source_meta" >&2
    echo "target=$target_meta" >&2
    exit 68
  }
done <"$SOURCE_PATHS"

git -C "$TARGET_ROOT" merge-base --is-ancestor "$REVISION" "$MERGE_REVISION"
test "$(git -C "$TARGET_ROOT" rev-parse "$MERGE_REVISION:$TARGET_PREFIX")" != "$TARGET_TREE_BEFORE"

mkdir -p "$RECEIPT_DIR"
BUNDLE_SHA="$(sha256sum "$BUNDLE" | awk '{print $1}')"
RESULT_TARGET_TREE="$(git -C "$TARGET_ROOT" rev-parse "$MERGE_REVISION:$TARGET_PREFIX")"
git -C "$TARGET_ROOT" reset --hard "$MERGE_REVISION" >/dev/null
git -C "$TARGET_ROOT" rev-list "$REVISION" | sort | awk '{print $1 " " $1}' >"$SLICE_MAP"
cat >"$SLICE_RECEIPT" <<EOF
# Monorepo identity-preserving append-only slice receipt: $ID

- historyMode: identity-preserving-append-only-slice
- Source revision: $REVISION
- Source advertised ref: $SOURCE_REF_FULL
- Source tree: $SOURCE_TREE
- Merge revision: $MERGE_REVISION
- Target prefix: $TARGET_PREFIX
- Target tree before: $TARGET_TREE_BEFORE
- Target tree after: $RESULT_TARGET_TREE
- Bundle: $BUNDLE
- Bundle SHA-256: $BUNDLE_SHA
- Path policy: append-only, zero collisions, exact source blob/mode identity
- Production cutover: NOT PERFORMED
EOF

cleanup
cleanup_files
trap - EXIT

printf 'appended %s\nsource=%s\nmerge=%s\ntarget_prefix=%s\nbundle_sha256=%s\n' \
  "$ID" "$REVISION" "$MERGE_REVISION" "$TARGET_PREFIX" "$BUNDLE_SHA"
