#!/usr/bin/env bash
set -euo pipefail
owner_root="$(cd "$(dirname "$0")/.." && pwd)"
jar="${ORDIVON_TLA_TOOLS_JAR:-}"
if [[ "$jar" != /* || ! -f "$jar" || -L "$jar" ]]; then
  echo "Edge TLC needs the pinned absolute regular TLA+ JAR" >&2
  exit 2
fi
# Qualify the external TLC binary, not another Owner\x27s private source tree.
# TLA+ TLC v1.7.4 (official release), SHA-256 of tla2tools.jar.
expected="936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88"
test "$(sha256sum -- "$jar" | cut -d' ' -f1)" = "$expected" || { echo "Unqualified TLA+ JAR digest" >&2; exit 2; }
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cp "$owner_root"/formal/EdgeCommitEvidenceR1.* "$owner_root"/formal/EdgeArtifactEpochR1.* "$tmp/"
cd "$tmp"

verify_model() {
  local model="$1"
  shift
  java -cp "$jar" tla2sany.SANY "$model.tla"
  java -cp "$jar" tlc2.TLC -workers 1 -config "$model.cfg" "$model.tla" > "$model.positive.log" || { cat "$model.positive.log"; exit 1; }
  grep -F 'Model checking completed. No error has been found.' "$model.positive.log"
  grep -E 'states generated|distinct states|depth' "$model.positive.log"
  local check variant inv rc
  for check in "$@"; do
    variant="${check%%:*}"
    inv="${check#*:}"
    set +e
    java -cp "$jar" tlc2.TLC -workers 1 -config "$model.$variant.cfg" "$model.tla" > "$model.$variant.log" 2>&1
    rc=$?
    set -e
    if [[ "$rc" != 12 ]] || ! grep -Fx "Error: Invariant $inv is violated." "$model.$variant.log"; then
      cat "$model.$variant.log"
      exit 1
    fi
  done
}

verify_model EdgeCommitEvidenceR1 \
  unsafe:CommittedEvidenceExists late-probe:NeverLateAfterPendingObservation \
  cleanup-probe:NeverCleanup recover-probe:NeverRecover
verify_model EdgeArtifactEpochR1 \
  unsafe:RetainedEvidenceUnchanged collision-probe:NeverCollision commit-probe:NeverNewCommit
