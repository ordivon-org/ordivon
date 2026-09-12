#!/usr/bin/env bash
set -euo pipefail

URI="${LIBVIRT_URI:-qemu:///system}"
NAME="${1:-security-v2-libvirt-smoke}"
XML="$(mktemp --suffix=.xml)"

cleanup() {
  virsh -c "$URI" destroy "$NAME" >/dev/null 2>&1 || true
  virsh -c "$URI" undefine "$NAME" >/dev/null 2>&1 || true
  rm -f "$XML"
}
trap cleanup EXIT

cat > "$XML" <<EOF
<domain type='kvm'>
  <name>${NAME}</name>
  <memory unit='MiB'>256</memory>
  <currentMemory unit='MiB'>256</currentMemory>
  <vcpu placement='static'>1</vcpu>
  <os><type arch='x86_64' machine='q35'>hvm</type></os>
  <features><acpi/></features>
  <clock offset='utc'/>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>destroy</on_reboot>
  <on_crash>destroy</on_crash>
  <devices>
    <emulator>/usr/bin/qemu-system-x86_64</emulator>
    <controller type='pci' model='pcie-root'/>
    <serial type='pty'><target type='isa-serial' port='0'/></serial>
    <console type='pty'><target type='serial' port='0'/></console>
  </devices>
</domain>
EOF

virsh -c "$URI" create "$XML" >/dev/null
[[ "$(virsh -c "$URI" domstate "$NAME" | tr -d '\r')" == "running" ]]

if [[ -n "$(virsh -c "$URI" domiflist "$NAME" | awk 'NR>2 && NF {print}')" ]]; then
  echo "unexpected network interface on lifecycle smoke domain" >&2
  exit 2
fi

STATUS="$(virsh -c "$URI" qemu-monitor-command "$NAME" '{"execute":"query-status"}')"
PCI="$(virsh -c "$URI" qemu-monitor-command "$NAME" '{"execute":"query-pci"}')"
python - "$STATUS" "$PCI" <<'PY'
import json, sys
status=json.loads(sys.argv[1])["return"]
pci=json.loads(sys.argv[2])["return"]
assert status["running"] is True
assert status["status"] == "running"
assert isinstance(pci, list) and pci
print("libvirtLifecycle=RUNNING_QMP_OBSERVED")
print(f"pciBusCount={len(pci)}")
PY

virsh -c "$URI" destroy "$NAME" >/dev/null
if virsh -c "$URI" dominfo "$NAME" >/dev/null 2>&1; then
  echo "transient domain survived destroy" >&2
  exit 3
fi

echo "networkInterfaces=0"
echo "postDestroy=ABSENT"
trap - EXIT
rm -f "$XML"
