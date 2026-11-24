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
cp "$owner_root"/formal/EdgeCommitEvidenceR1.* "$tmp/"
cd "$tmp"
java -cp "$jar" tla2sany.SANY EdgeCommitEvidenceR1.tla
java -cp "$jar" tlc2.TLC -workers 1 -config EdgeCommitEvidenceR1.cfg EdgeCommitEvidenceR1.tla > positive.log || { cat positive.log; exit 1; }
grep -F 'Model checking completed. No error has been found.' positive.log
grep -E 'states generated|distinct states|depth' positive.log
for check in 'unsafe:CommittedEvidenceExists' 'late-probe:NeverLateAfterPendingObservation' 'cleanup-probe:NeverCleanup' 'recover-probe:NeverRecover'; do
  variant="${check%%:*}"
  inv="${check#*:}"
  set +e
  java -cp "$jar" tlc2.TLC -workers 1 -config "EdgeCommitEvidenceR1.$variant.cfg" EdgeCommitEvidenceR1.tla > "$variant.log" 2>&1
  rc=$?
  set -e
  if [[ "$rc" != 12 ]] || ! grep -Fx "Error: Invariant $inv is violated." "$variant.log"; then
    cat "$variant.log"
    exit 1
  fi
done
