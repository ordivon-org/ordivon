# Falco runtime-detection acceptance R1

Date: 2026-09-12
Standing: `ENGINE_START_VERIFIED / EVENT_DELIVERY_BLOCKED_ON_CURRENT_WSL2_HOST`.

## Provider identity

Security v2 selected Falco as the default runtime **detection** provider, not as an enforcement authority.

R1 used Falco `0.44.1` (libs `0.25.4`, engine `0.62.0`). Two official distribution paths were exercised:

- OCI image: `public.ecr.aws/falcosecurity/falco:0.44.1`;
- observed OCI digest: `sha256:9f02feb5544a54a4ca2974bd8ab3a0cca287f3fe7c697d612814357af0cc55e5`;
- official host tarball: `https://download.falco.org/packages/bin/x86_64/falco-0.44.1-x86_64.tar.gz`;
- observed tarball SHA-256: `bc5b7a3bdf26fc91e520fc20b3461613c6e725148437121697a8d20243132127`.

The host is WSL2 Linux `6.6.123.2-microsoft-standard-WSL2`, x86_64, with `/sys/kernel/btf/vmlinux` present. Falco's shipped configuration selects `engine.kind: modern_ebpf`.

## What physically worked

Both the OCI and extracted host binary reported Falco `0.44.1`. Falco loaded the syscall event source and reached:

`Opening 'syscall' source with modern BPF probe.`

No kernel module installation was attempted. No Network configuration was changed.

## Falsification sequence

Three progressively broader event-delivery checks were attempted:

1. OCI Falco with a custom marker-process rule;
2. OCI Falco with the standard sensitive-file behavior (`cat /etc/shadow`);
3. the official host tarball binary, directly invoked from the Runtime Job, with a custom rule matching **any `execve`** event;
4. a transient **PID-1 systemd service** created with `systemd-run`, using the same official host binary and broad `evt.type=execve` rule, followed by explicit `/bin/echo`, `/usr/bin/id`, and `/usr/bin/date` executions.

All four reached modern-eBPF engine startup but produced no matching runtime event. The broad final rule generated no output even after multiple explicit process executions.

Falco also reported:

`libpman: disabled BPF iterators (not running in the root PID namespace, or failed to determine it)`

The OCI attempt additionally showed missing WSL tracepoints for several optional TOCTOU-mitigation hooks. Falco stated detection should continue despite those TOCTOU-hook failures, so those warnings alone are not promoted as the root cause.

## Interpretation

R1 still does **not** prove that Falco is generically incompatible with WSL2, but the additional PID-1 systemd falsifier eliminates the earlier hypothesis that the failure was only caused by the Runtime Job cgroup/process scope. On the current WSL2 host substrate, Falco `0.44.1` can initialize modern eBPF but cannot yet demonstrate syscall event delivery.

Therefore:

- Falco remains the selected P1 runtime-detection provider;
- Falco is **not** admitted as current Security runtime evidence on this host;
- Security must not fall back to Tetragon merely to make the checkbox green;
- no persistent Falco package/service should be materialized on this node until the host/kernel event-delivery blocker changes;
- a future acceptance should start from a kernel/tracepoint compatibility change or a standard Linux host, not from another wrapper/service rewrite.

No persistent Falco service or package was installed during R1. All acceptance artifacts were temporary.
