#!/usr/bin/env bash
set -euo pipefail

URI="${LIBVIRT_URI:-qemu:///system}"
NAME="${1:-security-v2-libtpm-smoke}"
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
  <vcpu>1</vcpu>
  <os><type arch='x86_64' machine='q35'>hvm</type></os>
  <devices>
    <emulator>/usr/bin/qemu-system-x86_64</emulator>
    <controller type='pci' model='pcie-root'/>
    <tpm model='tpm-tis'>
      <backend type='emulator' version='2.0'/>
    </tpm>
  </devices>
</domain>
EOF

libvirt_swtpm_present() {
  pgrep -af '/usr/bin/swtpm socket' | grep -F -- "$NAME" >/dev/null
}

virsh -c "$URI" create "$XML" >/dev/null
[[ "$(virsh -c "$URI" domstate "$NAME" | tr -d '\r')" == "running" ]]

TPM_JSON="$(virsh -c "$URI" qemu-monitor-command "$NAME" '{"execute":"query-tpm"}')"
python - "$TPM_JSON" <<'PY'
import json, sys
entries=json.loads(sys.argv[1])["return"]
assert len(entries) == 1
assert entries[0]["model"] == "tpm-tis"
assert entries[0]["options"]["type"] == "emulator"
print("libvirtTpm=QMP_OBSERVED_TPM2_EMULATOR")
PY

if ! libvirt_swtpm_present; then
  echo "libvirt-managed swtpm process not observed" >&2
  exit 2
fi

echo "swtpmProcess=LIBVIRT_MANAGED"
virsh -c "$URI" destroy "$NAME" >/dev/null

closed=false
for _ in $(seq 1 50); do
  domain_present=false
  swtpm_present=false
  virsh -c "$URI" dominfo "$NAME" >/dev/null 2>&1 && domain_present=true
  libvirt_swtpm_present && swtpm_present=true
  if [[ "$domain_present" == false && "$swtpm_present" == false ]]; then
    closed=true
    break
  fi
  sleep 0.1
done

if [[ "$closed" != true ]]; then
  echo "libvirt TPM lifecycle did not close within 5 seconds" >&2
  exit 3
fi

echo "postDestroyDomain=ABSENT"
echo "postDestroySwtpm=ABSENT"
trap - EXIT
rm -f "$XML"
