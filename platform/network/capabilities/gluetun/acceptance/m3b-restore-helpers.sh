#!/usr/bin/env bash
# Shared fail-closed primitives for M3B restoration. This file has no top-level effects.

m3b_candidate_teardown() {
  local ctr=$1 rc
  podman container exists "$ctr" >/dev/null 2>&1
  rc=$?
  case "$rc" in
    1) return 0 ;;
    0)
      podman rm -f "$ctr" >/dev/null 2>&1 || return 70
      podman container exists "$ctr" >/dev/null 2>&1
      rc=$?
      test "$rc" -eq 1 || return 70
      return 0
      ;;
    *) return 70 ;;
  esac
}

m3b_start_required_unit() {
  local unit=$1
  systemctl start "$unit" >/dev/null 2>&1 || return 70
  systemctl is-active --quiet "$unit" || return 70
}
