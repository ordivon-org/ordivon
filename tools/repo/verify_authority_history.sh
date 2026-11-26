#!/usr/bin/env bash
# Check immutable registration provenance for the supplied Git event.
set -euo pipefail
case "$EVENT_NAME" in
  pull_request) base="$PR_BASE"; head="$PR_HEAD" ;;
  merge_group) base="$GROUP_BASE"; head="$GROUP_HEAD" ;;
  push) base="$PUSH_BEFORE"; head="$PUSH_HEAD" ;;
esac
if [[ -n "$base" && ! "$base" =~ ^0+$ ]]; then
  python3 catalogs/authorities/scripts/check_historical_registration.py --base "$base" --head "$head"
fi
