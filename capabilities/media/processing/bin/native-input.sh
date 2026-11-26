#!/usr/bin/env bash
# Shared local carrier observation for the shell-native media adapters.
# A copy is private to this attempt, not a persistent Blob or archive.

input_custody_identity() {
  stat -Lc '%d:%i:%s:%y:%z' -- "$1"
}

input_custody_retire() {
  if [[ -n ${input_stage:-} ]]; then
    rm -rf -- "$input_stage"
    input_stage=
  fi
}

input_custody_start() {
  local source=$1 out=$2 before after
  [[ -f "$source" ]] || { echo "input is not a regular file" >&2; return 66; }
  before=$(input_custody_identity "$source")
  input_stage=$(mktemp -d -- "$out/.input.XXXXXX")
  trap input_custody_retire EXIT
  input_snapshot="$input_stage/$(basename -- "$source")"
  # Native COW where available; ordinary copy otherwise. Never hardlink.
  cp --reflink=auto -- "$source" "$input_snapshot"
  after=$(input_custody_identity "$source")
  if [[ "$before" != "$after" ]]; then
    echo "input changed during snapshot creation" >&2
    return 75
  fi
  chmod a-w -- "$input_snapshot"
  input_identity=$(input_custody_identity "$input_snapshot")
  # Exported as shell variables to the sourcing adapters.
  # shellcheck disable=SC2034
  input_digest="sha256:$(sha256sum < "$input_snapshot" | awk '{print $1}')"
  # shellcheck disable=SC2034
  input_size=$(stat -Lc '%s' -- "$input_snapshot")
  if [[ "$input_identity" != "$(input_custody_identity "$input_snapshot")" ]]; then
    echo "input snapshot changed during hashing" >&2
    return 75
  fi
}

input_custody_finish() {
  if [[ "$input_identity" != "$(input_custody_identity "$input_snapshot")" ]]; then
    echo "input snapshot changed during native observation" >&2
    return 75
  fi
  # Retire the temporary copy before a qualified receipt is published.
  input_custody_retire
  trap - EXIT
}
