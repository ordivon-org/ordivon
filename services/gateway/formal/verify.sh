#!/usr/bin/env bash
set -euo pipefail
jar="${ORDIVON_TLA_TOOLS_JAR:-$PWD/services/runtime/target/formal-tools/tla2tools-v1.7.4.jar}"
if [[ "$jar" != /* || ! -f "$jar" || -L "$jar" ]]; then
  echo "Gateway TLC needs a pinned absolute, regular TLA+ JAR" >&2
  exit 2
fi
expected=$(python3 -c 'import json;print(json.load(open("services/runtime/formal/toolchain.lock.json"))["sha256"])')
observed=$(sha256sum -- "$jar" | cut -d' ' -f1)
test "$observed" = "$expected" || { echo "Unqualified TLA+ JAR digest" >&2; exit 2; }
cd services/gateway/formal
java -cp "$jar" tla2sany.SANY GatewayRoutingR1.tla
routing_positive=$(java -cp "$jar" tlc2.TLC -workers 1 -config GatewayRoutingR1.cfg GatewayRoutingR1.tla)
printf '%s
' "$routing_positive" | grep -F 'Model checking completed. No error has been found.'
for check in 'GatewayRoutingR1.reachability.cfg:NeverForward' 'GatewayRoutingR1.unsafe.cfg:ForwardedImpliesExactRoute'; do
  config=$(printf '%s' "$check" | cut -d: -f1)
  invariant=$(printf '%s' "$check" | cut -d: -f2)
  set +e
  output=$(java -cp "$jar" tlc2.TLC -workers 1 -config "$config" GatewayRoutingR1.tla 2>&1)
  result=$?
  set -e
  [[ $result -eq 12 ]] || { printf '%s
' "$output" | tail -30; exit 1; }
  printf '%s
' "$output" | grep -Fx "Error: Invariant $invariant is violated."
done
java -cp "$jar" tla2sany.SANY GatewayOwnerObservationR1.tla
owner_positive=$(java -cp "$jar" tlc2.TLC -workers 1 -config GatewayOwnerObservationR1.cfg GatewayOwnerObservationR1.tla)
printf '%s
' "$owner_positive" | grep -F 'Model checking completed. No error has been found.'
for check in 'GatewayOwnerObservationR1.reachability.cfg:NeverAvailable' 'GatewayOwnerObservationR1.unsafe.cfg:NoFalsePositive'; do
  config=$(printf '%s' "$check" | cut -d: -f1)
  invariant=$(printf '%s' "$check" | cut -d: -f2)
  set +e
  output=$(java -cp "$jar" tlc2.TLC -workers 1 -config "$config" GatewayOwnerObservationR1.tla 2>&1)
  result=$?
  set -e
  [[ $result -eq 12 ]] || { printf '%s
' "$output" | tail -30; exit 1; }
  printf '%s
' "$output" | grep -Fx "Error: Invariant $invariant is violated."
done
java -cp "$jar" tla2sany.SANY GatewayCapabilityAuthzR1.tla
positive=$(java -cp "$jar" tlc2.TLC -workers 1   -config GatewayCapabilityAuthzR1.cfg GatewayCapabilityAuthzR1.tla)
printf '%s
' "$positive" | grep -F 'Model checking completed. No error has been found.'
printf '%s
' "$positive" | grep -E '^[0-9]+ states generated, [0-9]+ distinct states found, 0 states left on queue'
for check in 'GatewayCapabilityAuthzR1.reachability.cfg:ForwardUnreachable'              'GatewayCapabilityAuthzR1.unsafe.cfg:ForwardImpliesBinding'; do
  config="${check%%:*}"
  invariant="${check#*:}"
  set +e
  output=$(java -cp "$jar" tlc2.TLC -workers 1 -config "$config" GatewayCapabilityAuthzR1.tla 2>&1)
  result=$?
  set -e
  [[ $result -eq 12 ]] || { printf '%s
' "$output" | tail -30; exit 1; }
  printf '%s
' "$output" | grep -Fx "Error: Invariant $invariant is violated."
  printf '%s
' "$output" | grep -Eq '^State [1-9][0-9]*:'
done

# One bounded Agent consumer boundary, distinct from physical Runtime close.
java -cp "$jar" tla2sany.SANY GatewayAgentWorkspaceBindingR1.tla
workspace_positive=$(java -cp "$jar" tlc2.TLC -workers 1 -config GatewayAgentWorkspaceBindingR1.cfg GatewayAgentWorkspaceBindingR1.tla)
printf '%s
' "$workspace_positive" | grep -F 'Model checking completed. No error has been found.'
for check in 'GatewayAgentWorkspaceBindingR1.reachability.cfg:NeverAccepted' 'GatewayAgentWorkspaceBindingR1.unsafe.cfg:AcceptedRequiresExactOwnerWorkspace'; do
  config=$(printf '%s' "$check" | cut -d: -f1)
  invariant=$(printf '%s' "$check" | cut -d: -f2)
  set +e
  output=$(java -cp "$jar" tlc2.TLC -workers 1 -config "$config" GatewayAgentWorkspaceBindingR1.tla 2>&1)
  result=$?
  set -e
  [[ $result -eq 12 ]] || { printf '%s
' "$output" | tail -30; exit 1; }
  printf '%s
' "$output" | grep -Fx "Error: Invariant $invariant is violated."
  printf '%s
' "$output" | grep -Eq '^State [1-9][0-9]*:'
done
