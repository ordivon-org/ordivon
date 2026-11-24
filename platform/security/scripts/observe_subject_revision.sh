#!/usr/bin/env bash
# Point-in-time Git identity observation, not an immutable scan-input witness.
set -uo pipefail
target="${1:?target repository path is required}"
if ! revision="$(git -C "$target" rev-parse --verify HEAD 2>/dev/null)" ||
   [[ ! "$revision" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ ]] ||
   ! status="$(git -C "$target" status --porcelain --untracked-files=all 2>/dev/null)" ||
   [[ -n "$status" ]] ||
   ! final_revision="$(git -C "$target" rev-parse --verify HEAD 2>/dev/null)" ||
   [[ "$final_revision" != "$revision" ]]; then
  printf '%s\n' UNKNOWN
else
  printf '%s\n' "$revision"
fi
