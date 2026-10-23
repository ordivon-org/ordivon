#!/usr/bin/env bash
# Read-only source-publication fence: no fetch, push, ref update or checkout.
set -euo pipefail
[ "$#" -eq 1 ] || { echo "usage: $0 PRIMARY_REPOSITORY" >&2; exit 64; }
repo="$1"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
"$script_dir/check-primary-main.sh" "$repo" >/dev/null
local_head="$(git -C "$repo" rev-parse refs/heads/main)"
tracking="$(git -C "$repo" rev-parse --verify refs/remotes/origin/main 2>/dev/null)" || {
  echo "publication=TRACKING_REF_MISSING" >&2; exit 23;
}
live="$(git -C "$repo" ls-remote --exit-code origin refs/heads/main 2>/dev/null)" || {
  echo "publication=REMOTE_UNREACHABLE_OR_BRANCH_MISSING" >&2; exit 24;
}
remote_head="${live%%[[:space:]]*}"
[[ "$remote_head" =~ ^[[:xdigit:]]{40}$ ]] || {
  echo "publication=REMOTE_IDENTITY_INVALID" >&2; exit 24;
}
printf 'localMain=%s\nremoteMain=%s\ntrackedMain=%s\n' "$local_head" "$remote_head" "$tracking"
if [ "$tracking" != "$remote_head" ]; then
  echo "publication=TRACKING_REF_STALE"
  exit 23
fi
if [ "$local_head" = "$remote_head" ]; then
  echo "publication=SYNCED"
  exit 0
fi
if git -C "$repo" merge-base --is-ancestor "$remote_head" "$local_head"; then
  echo "publication=LOCAL_AHEAD_PR_REQUIRED"
  exit 20
fi
if git -C "$repo" merge-base --is-ancestor "$local_head" "$remote_head"; then
  echo "publication=LOCAL_BEHIND_REVIEW_AND_FETCH"
  exit 21
fi
echo "publication=DIVERGED_RECONCILE_WITH_PR"
exit 22
