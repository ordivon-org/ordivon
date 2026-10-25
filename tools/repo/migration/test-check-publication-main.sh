#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CHECK="$HERE/check-publication-main.sh"
tmp="$(mktemp -d -t ordivon-publish-cdc-XXXXXX)"
trap 'rm -rf "$tmp"' EXIT
repo="$tmp/source"
remote="$tmp/remote.git"
peer="$tmp/peer"
git init -q -b main "$repo"
git -C "$repo" config user.name "Offline Publication CDC"
git -C "$repo" config user.email "pub-cdc@example.invalid"
printf 'base\n' > "$repo/file.txt"
git -C "$repo" add file.txt
git -C "$repo" commit -qm "base"
base="$(git -C "$repo" rev-parse HEAD)"
git init -q --bare "$remote"
git -C "$repo" remote add origin "$remote"
git -C "$repo" push -q -u origin main

check() {
  local want_rc="$1" marker="$2" got
  set +e
  "$CHECK" "$repo" >"$tmp/out" 2>&1
  got="$?"
  set -e
  if [ "$got" != "$want_rc" ] || ! grep -F "$marker" "$tmp/out" >/dev/null; then
    echo "publication contract failed: wanted rc=$want_rc marker=$marker got=$got" >&2
    cat "$tmp/out" >&2
    exit 1
  fi
  test -z "$(git -C "$repo" status --porcelain)"
}
check 0 'publication=SYNCED'
# Negative controls: Git hides source-byte drift behind index flags even
# when write-tree, diff --quiet and status would otherwise certify main.
git -C "$repo" update-index --assume-unchanged file.txt
printf 'undetected-source-change\n' > "$repo/file.txt"
check 65 'tracked source index hides'
git -C "$repo" update-index --no-assume-unchanged file.txt
git -C "$repo" restore --worktree -- file.txt
check 0 'publication=SYNCED'
git -C "$repo" update-index --skip-worktree file.txt
printf 'other-hidden-source-change\n' > "$repo/file.txt"
check 65 'tracked source index hides'
git -C "$repo" update-index --no-skip-worktree file.txt
git -C "$repo" restore --worktree -- file.txt
check 0 'publication=SYNCED'
printf 'local-only\n' > "$repo/local.txt"
git -C "$repo" add local.txt
git -C "$repo" commit -qm "local"
check 20 'publication=LOCAL_AHEAD_PR_REQUIRED'
git clone -q -b main "$remote" "$peer"
git -C "$peer" config user.name "Offline Publication CDC"
git -C "$peer" config user.email "pub-cdc@example.invalid"
printf 'remote-only\n' > "$peer/remote.txt"
git -C "$peer" add remote.txt
git -C "$peer" commit -qm "remote"
git -C "$peer" push -q origin main
check 23 'publication=TRACKING_REF_STALE'
git -C "$repo" fetch -q origin refs/heads/main:refs/remotes/origin/main
check 22 'publication=DIVERGED_RECONCILE_WITH_PR'
git -C "$repo" reset -q --hard "$base"
check 21 'publication=LOCAL_BEHIND_REVIEW_AND_FETCH'
git -C "$repo" update-ref -d refs/remotes/origin/main
check 23 'publication=TRACKING_REF_MISSING'
printf 'dirty\n' >> "$repo/file.txt"
set +e
"$CHECK" "$repo" >"$tmp/out" 2>&1
got="$?"
set -e
test "$got" -eq 65
grep -F 'primary checkout is not synchronized with main' "$tmp/out" >/dev/null
# SHA-256 is a supported native Git repository object format. A remote's
# valid 64-digit object name must not be mistaken for a corrupt SHA-1 identity.
sha256_repo="$tmp/sha256-source"
sha256_remote="$tmp/sha256-remote.git"
git init -q -b main --object-format=sha256 "$sha256_repo"
git -C "$sha256_repo" config user.name "Offline Publication SHA256 CDC"
git -C "$sha256_repo" config user.email "pub-sha256-cdc@example.invalid"
printf 'sha256-base\n' > "$sha256_repo/proof.txt"
git -C "$sha256_repo" add proof.txt
git -C "$sha256_repo" commit -qm "sha256-base"
git init -q --bare --object-format=sha256 "$sha256_remote"
git -C "$sha256_repo" remote add origin "$sha256_remote"
git -C "$sha256_repo" push -q -u origin main
previous_repo="$repo"
repo="$sha256_repo"
check 0 'publication=SYNCED'
sha256_peer="$tmp/sha256-peer"
git clone -q -b main "$sha256_remote" "$sha256_peer"
git -C "$sha256_peer" config user.name "Offline Publication SHA256 CDC"
git -C "$sha256_peer" config user.email "pub-sha256-cdc@example.invalid"
printf 'sha256-remote-advance\n' > "$sha256_peer/new-proof.txt"
git -C "$sha256_peer" add new-proof.txt
git -C "$sha256_peer" commit -qm "advance-sha256"
git -C "$sha256_peer" push -q origin main
check 23 'publication=TRACKING_REF_STALE'
git -C "$sha256_repo" fetch -q origin refs/heads/main:refs/remotes/origin/main
check 21 'publication=LOCAL_BEHIND_REVIEW_AND_FETCH'
repo="$previous_repo"
echo 'PASS publication source/main/remote contract: sync, ahead, stale, divergent, behind, missing, dirty'
