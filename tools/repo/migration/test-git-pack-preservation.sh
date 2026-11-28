#!/usr/bin/env bash
# Native Git storage refinement contract, independent of the operator.
# I: an explicitly selected pack cohort + existing object identities.
# O: original identities and content survive locally (retained union covers
# original union, not necessarily one identical pack); only redundant pack
# representations in the admitted cohort may disappear. Git owns the MIDX.
# Held packs, other packs and local unreachable objects are not deletion
# authority. This isolated fixture does not qualify live concurrency, a
# promisor remote's retention, unknown packs, or reclamation of live source.
set -euo pipefail
export GIT_NO_LAZY_FETCH=1 GIT_TERMINAL_PROMPT=0
tmp="$(mktemp -d -t ordivon-git-pack-preservation-XXXXXX)"
trap 'rm -rf -- "$tmp"' EXIT

fixture() {
  local fmt="$1" repo="$tmp/$1" packdir a b c d e f keep duplicate representative different partial outside outside_duplicate oid
  git init -q --bare --object-format="$fmt" "$repo"
  packdir="$repo/objects/pack"
  git -C "$repo" config gc.auto 0
  git -C "$repo" config maintenance.auto false
  git -C "$repo" config remote.origin.promisor true
  git -C "$repo" config remote.origin.partialclonefilter blob:none
  git -C "$repo" config remote.origin.url "$tmp/unavailable-origin"
  a="$(printf '%4096s\n' a | git -C "$repo" hash-object -w --stdin)"
  b="$(printf '%4096s\n' b | git -C "$repo" hash-object -w --stdin)"
  c="$(printf '%4096s\n' c | git -C "$repo" hash-object -w --stdin)"
  d="$(printf '%4096s\n' d | git -C "$repo" hash-object -w --stdin)"
  e="$(printf 'local-unreachable-preservation-%4096s\n' "$fmt" | git -C "$repo" hash-object -w --stdin)"
  f="$(printf 'another local preservation-%4096s\n' "$fmt" | git -C "$repo" hash-object -w --stdin)"
  representative="pack-$(printf '%s\n' "$a" "$b" | git -C "$repo" pack-objects --no-reuse-object --no-reuse-delta --compression=9 --window=0 "$packdir/pack")"
  duplicate="pack-$(printf '%s\n' "$a" "$b" | git -C "$repo" pack-objects --no-reuse-object --no-reuse-delta --compression=0 --window=0 "$packdir/pack")"
  keep="pack-$(printf '%s\n' "$b" "$a" | git -C "$repo" pack-objects --no-reuse-object --no-reuse-delta --compression=1 --window=0 "$packdir/pack")"
  different="pack-$(printf '%s\n' "$c" "$d" | git -C "$repo" pack-objects --no-reuse-object --no-reuse-delta --compression=0 --window=0 "$packdir/pack")"
  partial="pack-$(printf '%s\n' "$a" "$c" | git -C "$repo" pack-objects --no-reuse-object --no-reuse-delta --compression=0 --window=0 "$packdir/pack")"
  # Nonpreferred ties select newer packs; keep the two covering packs newer.
  touch -t 202001010000 "$packdir/$partial.pack"
  outside="pack-$(printf '%s\n' "$e" "$f" | git -C "$repo" pack-objects --no-reuse-object --no-reuse-delta --compression=0 --window=0 "$packdir/pack")"
  outside_duplicate="pack-$(printf '%s\n' "$e" "$f" | git -C "$repo" pack-objects --no-reuse-object --no-reuse-delta --compression=9 --window=0 "$packdir/pack")"
  test "$outside" != "$outside_duplicate"
  test "$representative" != "$duplicate"
  test "$representative" != "$keep"
  test "$duplicate" != "$keep"
  # These markers simulate a promisor cohort; no external promise is relied
  # upon. In particular, all postconditions must hold with lazy fetch disabled.
  for oid in "$representative" "$duplicate" "$keep" "$different" "$partial"; do
    : > "$packdir/$oid.promisor"
  done
  printf 'fixture-held\n' > "$packdir/$keep.keep"
  git -C "$repo" prune-packed
  for oid in "$representative" "$duplicate" "$keep" "$different" "$partial"; do
    git -C "$repo" show-index --object-format="$fmt" < "$packdir/$oid.idx" |
      awk '{print $2}' | LC_ALL=C sort > "$tmp/$fmt-$oid.ids"
  done
  cmp "$tmp/$fmt-$representative.ids" "$tmp/$fmt-$duplicate.ids"
  cmp "$tmp/$fmt-$representative.ids" "$tmp/$fmt-$keep.ids"
  # Equal object count is not identity. The different pack must survive.
  test "$(wc -l < "$tmp/$fmt-$different.ids")" -eq "$(wc -l < "$tmp/$fmt-$representative.ids")"
  if cmp -s "$tmp/$fmt-$representative.ids" "$tmp/$fmt-$different.ids"; then
    echo "unexpected equal object identities" >&2; exit 1
  fi
  # Union coverage, not one-pack equality: neither retained pack alone
  # contains the partial pack, but their exact OID union does.
  cat "$tmp/$fmt-$representative.ids" "$tmp/$fmt-$different.ids" |
    LC_ALL=C sort -u > "$tmp/$fmt.cover"
  test -z "$(LC_ALL=C comm -23 "$tmp/$fmt-$partial.ids" "$tmp/$fmt.cover")"
  test -n "$(LC_ALL=C comm -23 "$tmp/$fmt-$partial.ids" "$tmp/$fmt-$representative.ids")"
  test -n "$(LC_ALL=C comm -23 "$tmp/$fmt-$partial.ids" "$tmp/$fmt-$different.ids")"
  printf '%s\n' "$a" "$b" "$c" "$d" "$e" "$f" > "$tmp/$fmt.all"
  git -C "$repo" cat-file --batch < "$tmp/$fmt.all" > "$tmp/$fmt.before"
  sha256sum "$packdir/$outside.pack" "$packdir/$outside.idx" "$packdir/$outside_duplicate.pack" "$packdir/$outside_duplicate.idx" > "$tmp/$fmt.outside"
  git -C "$repo" verify-pack "$packdir/$representative.idx"
  git -C "$repo" verify-pack "$packdir/$different.idx"
  printf '%s.idx\n' "$representative" "$duplicate" "$keep" "$different" "$partial" |
    git -C "$repo" multi-pack-index write --stdin-packs --no-bitmap --preferred-pack="$representative.pack"
  git -C "$repo" multi-pack-index verify
  git -C "$repo" multi-pack-index expire
  test ! -e "$packdir/$duplicate.pack"
  test ! -e "$packdir/$duplicate.idx"
  test ! -e "$packdir/$duplicate.promisor"
  test ! -e "$packdir/$partial.pack"
  test ! -e "$packdir/$partial.idx"
  test ! -e "$packdir/$partial.promisor"
  for oid in "$representative" "$keep" "$different"; do
    test -f "$packdir/$oid.pack"
    test -f "$packdir/$oid.promisor"
  done
  test -f "$packdir/$keep.keep"
  sha256sum -c "$tmp/$fmt.outside" >/dev/null
  git -C "$repo" multi-pack-index verify
  git -C "$repo" cat-file --batch < "$tmp/$fmt.all" > "$tmp/$fmt.after"
  cmp "$tmp/$fmt.before" "$tmp/$fmt.after"
  if grep -q ' missing$' "$tmp/$fmt.after"; then
    echo "original object unavailable locally" >&2; exit 1
  fi
  printf 'PASS %s duplicate pack retirement, held/noncohort/unique object preservation\n' "$fmt"
}

fixture sha1
fixture sha256
