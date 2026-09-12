# VM provider displacement R1

Date: 2026-09-12

## Purpose

Old Security directly owns a large Windows/KVM mechanism surface: QEMU process lifecycle, QMP sockets/commands, swtpm process state, image handling, network namespaces, NBD/partition manipulation, recovery, and many provider-specific receipts. The major Windows/KVM-related modules alone are roughly 8,094 LOC.

Security v2 does not assume this machinery must migrate. The displacement direction is mature external ownership first.

## Current host provider state

Verified current physical state:

- libvirt `12.7.0` installed;
- virt-install `5.1.0` installed;
- Packer `1.16.0` installed;
- QEMU/QEMU-img `11.0.3` installed;
- swtpm `0.10.1` installed;
- `/dev/kvm` available;
- modular libvirt sockets `virtqemud`, `virtlogd`, and `virtlockd` active;
- `virsh -c qemu:///system` connects successfully.

`libguestfs` is **not installed**. An installation attempt failed before transaction commit because the local Arch package database referenced QEMU `11.1.1-1` artifacts that the configured mirrors no longer served. The installed QEMU packages remained at `11.0.3-1`. This is treated as package/mirror skew, not as a completed provider migration.

## R1 lifecycle proof

A real transient KVM domain was created through libvirt with:

- 256 MiB memory;
- one vCPU;
- q35 machine;
- no guest disk;
- no network interface.

The external provider then proved:

1. create/start through libvirt;
2. domain state `running`;
3. zero interfaces through `domiflist`;
4. QMP `query-status` through libvirt returned running state;
5. QMP `query-pci` through libvirt returned the live PCI topology;
6. destroy through libvirt;
7. transient domain absent after destroy.

This is now reproducible through `scripts/smoke_libvirt_lifecycle.sh`.

## Displacement conclusion

The following old mechanical responsibilities are no longer justified as Security-owned primitives merely for VM lifecycle:

- direct QEMU `Popen` ownership;
- QEMU PID lifecycle bookkeeping;
- hand-owned QMP socket connection lifecycle;
- direct `quit`/process-terminate fallback as the primary lifecycle API;
- basic create/start/inspect/destroy domain mechanics.

Security v2 should consume libvirt/QEMU provider evidence and retain only the semantic bindings already proven elsewhere: authority, exact subject/effect identity, current evidence, and verified consequence.

## libvirt-managed TPM proof

A second real transient domain delegated TPM 2.0 lifecycle to libvirt using an emulator backend. QMP `query-tpm` reported one `tpm-tis` device backed by an emulator chardev, and the live process table showed libvirt-owned `/usr/bin/swtpm socket ...` state for the domain.

After domain destruction, swtpm shutdown was asynchronous rather than instantaneous. A bounded follow-up confirmed that both domain and swtpm process/state disappeared. `scripts/smoke_libvirt_tpm.sh` therefore uses a five-second bounded closure window instead of assuming synchronous process disappearance.

This removes another reason for Security to own swtpm PID/socket lifecycle directly.

## Packer boundary

Packer `1.16.0` is adopted as the candidate image-construction owner. The official HashiCorp QEMU plugin `v1.1.6` was initialized successfully from `github.com/hashicorp/qemu`.

The v2 Packer template now requires both `iso_url` and an exact lowercase `sha256:<64 hex>` checksum from the caller. A negative validation proved `iso_checksum=none` fails closed. Syntax validation and full provider configuration validation with structurally valid bound inputs both pass.

This proves image-build toolchain availability, **not** a real Windows image build. A real build remains blocked until an authoritative installation image/fixture is selected and its real digest is frozen.

## Still open

R1 does not yet prove displacement of:

- image construction from the real Windows installation source;
- qemu-nbd/partx/mtools/NTFS manipulation;
- disk readback and offline inspection;
- network namespace/traffic-capture scenarios;
- recovery/compensation semantics under host or process failure.

`libguestfs` remains unavailable. Its installation was retried only after reconciling a stale pacman lock, but the transaction then failed before commit because the local Arch package database referenced QEMU `11.1.1-1` artifacts no longer present on the configured mirrors. The installed QEMU family was re-verified unchanged at `11.0.3-1`. Do not perform an unsafe partial upgrade merely to satisfy this migration; restore package database/mirror consistency first.
