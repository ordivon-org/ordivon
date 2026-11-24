#!/usr/bin/env bash
set -euo pipefail
owner_root="$(cd "$(dirname "$0")/.." && pwd)"
repo_root="$(cd "$owner_root/../../../.." && pwd)"
jar="${ORDIVON_TLA_TOOLS_JAR:-$repo_root/services/runtime/target/formal-tools/tla2tools-v1.7.4.jar}"
if [[ "$jar" != /* || ! -f "$jar" || -L "$jar" ]]; then
  echo "Edge TLC needs the pinned absolute regular TLA+ JAR" >&2
  exit 2
fi
expected="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["sha256"])' "$repo_root/services/runtime/formal/toolchain.lock.json")"
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
