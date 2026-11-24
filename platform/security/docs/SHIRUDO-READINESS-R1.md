# Shirudo adoption and Arch/WSL readiness R1

Date: 2026-11-25 (UTC+08). Standing: conditional experimental candidate; no installation, protected target, or production admission.
Source baseline: e7950043189504ff37b1eda385720ee42b5c0a08 (observed origin/main).

## Decision and natural consumers

Shirudo is a signed BPF enforcement and measurement substrate, not a replacement for Security policy, Runtime, a vulnerability scanner, or a general sandbox. Reuse its Operator, target, signed upatches, OCI distribution and attestation verifier. Do not create another loader, registry, signing authority, daemon, or VM lifecycle service. Falco stays the baseline detection selection on compatible ordinary hosts; Tetragon remains conditional. On a Shirudo target the existing eBPF loaders are not assumed compatible.

| Route | Standing |
|---|---|
| Current Arch WSL2 as Operator | Conditional: native build prerequisites incomplete |
| Arch as host of official isolated x86-64 test VM | KVM primitive verified; Quickstart not run |
| Current WSL2 kernel as enforcing target | NO-GO: necessary kernel and device conditions fail |
| Separate production Linux VM or bare metal | Deferred; qualify trusted boot, TPM identity and actual consumers |

## Observed host readiness

Native Linux PG Runtime, Arch rolling, x86_64, WSL, kernel 6.18.58.1-microsoft-standard-WSL2. 16 visible CPUs, 9.7 GiB total / 5.6 GiB available memory, swap 3.3/4.0 GiB occupied, 136 GiB free on root filesystem. This is a dated snapshot, not a reservation.

| Predicate | Result |
|---|---|
| KVM API and VM object creation | API 12; KVM_CREATE_VM succeeded, FD closed; no guest boot |
| BPF, JIT, BTF, ftrace, BPF LSM, dm-verity, keys | config present; BTF exists; actual active LSM unknown (securityfs not mounted in observed namespace) |
| TPM and EFI | /dev/tpm0, /dev/tpmrm0 and /sys/firmware/efi absent in observed namespace |
| Required module signing / verity root signature | CONFIG_MODULE_SIG and CONFIG_DM_VERITY_VERIFY_ROOTHASH_SIG explicitly unset; sufficient negative evidence for current target |
| Signed-loader ABI | exact Shirudo preflight not run; BTF string witnesses keyring_serial, bpf_inode_init_xattr, bpf_real_data_inode, tpm_command, mm_read_access absent; not a structural ABI proof |
| Compiler and crypto | clang/LLVM 23.1.5; BPF targets present; OpenSSL 4.1.0 advertises ML-DSA-87; actual upstream build/sign untested |
| Dynamic libraries | libelf 0.197, libcurl 8.23.0, tss2-esys/mu/tctildr 4.2.1, swtpm TCTI present; zlib 1.4, zstd 1.5.7; LuaJIT pkg-config absent |
| Virtualization tools | QEMU 11.1.3, swtpm 0.10.2, swtpm_setup/ioctl, qemu-img, Podman 6.2.0; virsh installed but qemu:///system socket absent |
| Other present tools | GCC 16.2.1, make 4.4.1, pkg-config, git, Python 3.15.1, veritysetup, mkfs.ext4, llvm-strip, readelf, autoconf, automake, libtool, nix |
| Quickstart gaps | dpkg-deb, tpm2_getcap, dracut, cloud-localds, guestfish, virt-customize, dhclient, luajit not on PATH; static libz.a, libzstd.a, libluajit-5.1.a not in /usr/lib; libelf.a and libc.a present; GC64 and alternate paths unverified |
| Locked memory | soft/hard 65536 KiB; official Quickstart expects unlimited; actual mlock capability not tested |

Windows physical TPM, firmware and Hyper-V were not observed. A guest swtpm is experimental evidence only, not a hardware trust root. Current libvirt connection failure is not proof of package removal; historical VM displacement remains historical.

## Evidence coordinates

Native jobs (succeeded, stdout retained, exact SHA-256; use Runtime artifact.read, not a workspace path):
- job-01a20f6a-abff-7215-b3ba-74c72f9619de / attempt-01a20f6a-abff-7215-b3ba-74c8da1e743d.stdout / 5f7ae706ae732349a7afd0027efcb24fd9916f90c05827120af5952749c12649
- job-01a20f6a-fd31-73aa-ac05-6cf42eeaf1bb / attempt-01a20f6a-fd31-73aa-ac05-6cf51d87b6f0.stdout / e65f4873d7ab318c22c0c57b24934dd6d8386d737a61b9195316ced2f57fdf15
- job-01a20f6b-505c-7609-adf4-6478d0f8b434 / attempt-01a20f6b-505c-7609-adf4-64795bf04c4f.stdout / 0baba7ec8cc3daddb30d8ffa8fcb4d52469f672267a476908e63c52c82295cfe

## Consumer incompatibility and acceptance

Upstream interoperability explicitly reports denial of ordinary userspace BPF loads, including Falco eBPF, Tetragon, Cilium, bcc/bpftrace. systemd 262 can start services without BPF-dependent restrictions; cgroup device rules have no equivalent upatch attachment per upstream. systemd 263 keyring setup may prevent Shirudo initialization. Do not infer safety from service liveness. nftables can cover some network restrictions, not device restrictions. Verify actual Runtime isolation, Podman device rules, networking, monitoring and recovery with positive and negative consumer tests before any production candidate. No host kernel, package, service or keyring changes made.

## Work sequence (not yet executed)

1. Freeze upstream source commit, test kernel artifact digest and metadata; prefer upstream Quickstart and its test VM. Do not compile against host BTF.
2. Inspect upstream dependency resolution; prefer isolated reproducible build environment (existing Nix/Podman where appropriate), not unsafe partial Arch upgrade. Resolve static archives, GC64 LuaJIT, image tools and scoped memlock. Check actual source build and binary identity.
3. Use one isolated disposable guest, no production credentials, no production network exposure. Budget one VM at a time; official example 4 vCPU/4 GiB, recheck swap and current pressure before admission. Use upstream VM lifecycle first; reuse libvirt for a real later consumer only if needed and qualified. No new lifecycle abstraction.
4. Verify guest boot, `shirudo init --check-only`, enforcement conditions, signed benign upatch behavior, rejection of invalid/tampered signature, unload and recovery, fresh TPM quote/event-log verification with independent expected identities and nonce, reboot and cleanup. Quickstart direct kernel/initrd boot does not measure UKI phases into PCR11; no production attestation claim.
5. Test normal/negative Runtime job, device/network restrictions and observability consumers; retain evidence, not just exit codes. Distinguish failed initialization from healthy protected boot.
6. Only after real consumer and evidence, compose Security semantic binding with provider-native artifacts, Runtime execution/Artifact, Harness research, Host decision history and Gateway existing route if needed. Separate candidate generation, authorized signing and independent verification. Do not give model unrestricted signing authority.
7. For production, qualify boot-chain measurements, real TPM identity, exact kernel patches/ABI, key lifecycle, rollback, formal proof coverage and risk-tiered authorization. A model proof does not prove deployed enforcement.

## Upstream references (consulted 2026-11-25)

- [Announcement](https://openai.com/index/introducing-shirudo/)
- [Source](https://github.com/shirudo-dev/shirudo)
- [System requirements](https://docs.shirudo.dev/operate/plan/system-requirements.html)
- [Quickstart](https://docs.shirudo.dev/start/quickstart.html)
- [Interoperability](https://docs.shirudo.dev/operate/plan/interoperability.html)
- [Operator and target](https://docs.shirudo.dev/concepts/operator-and-target.html)
- [Deployment checklist](https://docs.shirudo.dev/operate/deploy/deployment-checklist.html)

The upstream page named “Arch support” refers to CPU architectures, not Arch Linux distribution support. No native Arch package admission is claimed.
