#!/usr/bin/env bash
set -euo pipefail
jar="${ORDIVON_TLA_TOOLS_JAR:?absolute pinned TLC jar required}"
expected="${ORDIVON_TLA_TOOLS_SHA256:?expected digest from existing toolchain pin required}"
[[ "$jar" = /* && -f "$jar" && ! -L "$jar" && "$expected" =~ ^[0-9a-f]{64}$ ]]
test "$(sha256sum "$jar" | cut -d' ' -f1)" = "$expected"
cd "$(dirname "$0")"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
java -cp "$jar" tla2sany.SANY ObservationGenerationR1.tla
java -cp "$jar" tlc2.TLC -workers 1 -metadir "$tmp/safe" -config ObservationGenerationR1.safe.cfg ObservationGenerationR1.tla > "$tmp/safe.log"
grep -F 'Model checking completed. No error has been found.' "$tmp/safe.log"
grep -F 'distinct states found' "$tmp/safe.log"
for pair in legacy:DenialNotReplacedByStale legacy-lifecycle:NoPrivateRowsWhenInactive legacy-hint:NoPrivateRowsAfterHint reach-observed:NeverObserved reach-denied:NeverDenied reach-suspended:NeverSuspended reach-hinted:NeverHinted; do
 name=${pair%:*}; inv=${pair#*:}
 set +e
 java -cp "$jar" tlc2.TLC -workers 1 -metadir "$tmp/$name" -config "ObservationGenerationR1.$name.cfg" ObservationGenerationR1.tla > "$tmp/$name.log" 2>&1
 rc=$?
 set -e
 test "$rc" = 12 || { cat "$tmp/$name.log"; exit 1; }
 grep -F "Invariant $inv is violated" "$tmp/$name.log"
done
