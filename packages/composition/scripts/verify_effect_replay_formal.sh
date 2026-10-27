#!/usr/bin/env bash
set -euo pipefail
if [[ "$#" -ne 1 ]]; then echo "exact formal runtime toolchain root required" >&2; exit 2; fi
runtime_root="$(realpath "$1")"
[[ -f "$runtime_root/formal/toolchain.lock.json" ]] || { echo "no pinned runtime formal toolchain lock" >&2;exit 2; }
jar="$(python3 - "$runtime_root" <<'PY'
import json
from pathlib import Path
import sys
p=Path(sys.argv[1]);x=json.loads((p/'formal/toolchain.lock.json').read_text())
print((p/x['cacheRelativePath']).resolve())
PY
)"
if [[ ! -f "$jar" ]];then "$runtime_root/scripts/tla-formal" bootstrap; fi
cd formal
before="$(sha256sum EffectReplayFence.tla EffectReplayFence.cfg EffectReplayFence.*.cfg "$jar" "$runtime_root/formal/toolchain.lock.json" "$runtime_root/scripts/tla-formal")"
java -XX:+UseParallelGC -cp "$jar" tla2sany.SANY EffectReplayFence.tla
java -XX:+UseParallelGC -cp "$jar" tlc2.TLC -workers 1 -config EffectReplayFence.cfg EffectReplayFence.tla
probe="$(mktemp)"
red="$(mktemp -d)"
trap 'rm -f "$probe";rm -rf "$red"' EXIT
for invariant in ReconciliationIsUnreachable TerminalCommittedWithoutEffectIsUnreachable UnindexedUncertaintyIsUnreachable;do
  if java -XX:+UseParallelGC -cp "$jar" tlc2.TLC -workers 1 -config "EffectReplayFence.$invariant.cfg" EffectReplayFence.tla >"$probe" 2>&1;then
    echo "C06 nonvacuity unexpectedly PASS: $invariant" >&2;exit 1
  fi
  grep -Fq "Error: Invariant $invariant is violated." "$probe" || { cat "$probe";exit 1; }
  case "$invariant" in
    ReconciliationIsUnreachable) grep -Fq 'recommendation = "reconcile"' "$probe";;
    TerminalCommittedWithoutEffectIsUnreachable)
      grep -Fq 'terminal = TRUE' "$probe"
      grep -Fq 'delivery = "committed"' "$probe"
      grep -Fq 'effectEstablished = FALSE' "$probe";;
    UnindexedUncertaintyIsUnreachable)
      grep -Fq 'indexed = FALSE' "$probe"
      grep -Fq 'impacted = {"write", "client", "media"}' "$probe";;
  esac
  echo "TLC C06 $invariant nonvacuity PASS"
done
cp EffectReplayFence.tla EffectReplayFence.cfg "$red/"
python3 - "$red/EffectReplayFence.tla" <<'PY'
import sys
from pathlib import Path
p=Path(sys.argv[1]);s=p.read_text()
old="    /"+chr(92)+" retryAllowed' = FALSE"
new="    /"+chr(92)+" retryAllowed' = TRUE"
if s.count(old)!=1:raise SystemExit('unsafe retry mutation target ambiguous')
p.write_text(s.replace(old,new))
PY
if (cd "$red";java -XX:+UseParallelGC -cp "$jar" tlc2.TLC -workers 1 -config EffectReplayFence.cfg EffectReplayFence.tla) >"$probe" 2>&1;then
  echo "TLC unsafe retry mutation incorrectly PASS" >&2;exit 1
fi
grep -Fq 'Error: Invariant NoBlindRetry is violated.' "$probe" || { cat "$probe";exit 1; }
grep -Fq 'retryAllowed = TRUE' "$probe" || { cat "$probe";exit 1; }
echo "TLC C06 unsafe retry mutation negative control PASS"
after="$(sha256sum EffectReplayFence.tla EffectReplayFence.cfg EffectReplayFence.*.cfg "$jar" "$runtime_root/formal/toolchain.lock.json" "$runtime_root/scripts/tla-formal")"
[[ "$before" == "$after" ]] || { echo "TLC C06 inputs drifted during proof window" >&2;exit 1; }
echo "TLC C06 bounded formal input continuity PASS (not an atomic or installed proof)"
