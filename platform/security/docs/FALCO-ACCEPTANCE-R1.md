# Falco runtime-detection acceptance R1

Date: 2026-09-12
Standing: `ENGINE_START_VERIFIED / EVENT_DELIVERY_BLOCKED_IN_CURRENT_RUNTIME_NAMESPACE`.

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
3. the official host tarball binary, directly invoked from the Runtime Job, with a custom rule matching **any `execve`** event.

All three reached modern-eBPF engine startup but produced no matching runtime event. The broad final rule generated no output even after multiple explicit process executions.

Falco also reported:

`libpman: disabled BPF iterators (not running in the root PID namespace, or failed to determine it)`

The OCI attempt additionally showed missing WSL tracepoints for several optional TOCTOU-mitigation hooks. Falco stated detection should continue despite those TOCTOU-hook failures, so those warnings alone are not promoted as the root cause.

## Interpretation

R1 does **not** prove that Falco is incompatible with WSL2. It proves that a Falco process launched through the current Ordivon Runtime execution context cannot yet demonstrate host syscall event delivery. The Runtime execution context is not an acceptable substitute for a true host-level Falco deployment when validating kernel-wide observation.

Therefore:

- Falco remains the selected P1 runtime-detection provider;
- Falco is **not** admitted as current Security runtime evidence on this host;
- Security must not fall back to Tetragon merely to make the checkbox green;
- the next acceptance belongs at the Operations/host-service boundary, where Falco can run in the real host PID/kernel observation context;
- after Operations materialization, Security should rerun one bounded event-delivery smoke and bind the resulting native Falco event by digest/currentness.

No persistent Falco service or package was installed during R1. All acceptance artifacts were temporary.
