#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
jar="${ORDIVON_TLA_TOOLS_JAR:-}"
test "$jar" = "${jar#/}" && { echo 'Use absolute qualified TLC jar' >&2; exit 2; }
test -f "$jar" && test ! -L "$jar"
test "$(sha256sum "$jar" | cut -d' ' -f1)" = 936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88
tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT
cp "$here"/PGOfflineMaintenanceR1.{tla,cfg} "$tmp/"
cd "$tmp"
java -cp "$jar" tla2sany.SANY PGOfflineMaintenanceR1.tla
java -cp "$jar" tlc2.TLC -workers 1 -config PGOfflineMaintenanceR1.cfg PGOfflineMaintenanceR1.tla > safe.log 2>&1 || { cat safe.log; exit 1; }
grep -F 'Model checking completed. No error has been found.' safe.log
grep -E 'states generated|distinct states|depth' safe.log
for pair in OmitRoots:NoLiveRootsAfterHandoff OmitEpoch:ExactHandoff OmitDetach:NativeDetachBeforeCompact OmitAccept:RecoveryBeforeReopen BlockDrain:DrainProgress OmitFresh:ExactHandoff OmitBackup:ExactHandoff Reachable:NeverReopened; do
    flag="${pair%:*}"; inv="${pair#*:}"
    if test "$flag" = Reachable; then
        sed '/^CHECK_DEADLOCK/i\  NeverReopened' PGOfflineMaintenanceR1.cfg > negative.cfg
    else
        sed "s/$flag = FALSE/$flag = TRUE/" PGOfflineMaintenanceR1.cfg > negative.cfg
    fi
    set +e
    java -cp "$jar" tlc2.TLC -workers 1 -config negative.cfg PGOfflineMaintenanceR1.tla > "$flag.log" 2>&1
    rc=$?
    set -e
    if test "$rc" != 12 || ! grep -Fx "Error: Invariant $inv is violated." "$flag.log"; then
        cat "$flag.log"
        exit 1
    fi
done
