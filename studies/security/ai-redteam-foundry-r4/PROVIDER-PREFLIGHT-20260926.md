# R4 hostile-sandbox provider preflight — 2026-09-26/27

Standing: `PROVIDER_LIFECYCLE_REQUALIFIED_ON_DEMAND_NOT_HOSTILE_ENVIRONMENT_READY`

This is a point-in-time provider capability observation. It is not a production availability guarantee and
not proof that any VM instance satisfies the complete R4 hostile-code isolation contract.

## Initial current-truth census

Observed on the Ordivon Linux host through Runtime:

- `virsh --version` -> `12.7.0`;
- `/dev/kvm` exists as a character device, mode `0666`, owner `root`, group `kvm`;
- `qemu-system-x86_64 --version` -> QEMU `11.0.3`;
- `virtqemud.socket` -> `inactive` and `disabled`;
- `libvirtd.socket` -> `inactive` / disabled;
- `virsh -c qemu:///system list --all --name` initially failed because `/run/libvirt/virtqemud-sock` was absent.

The installed provider was therefore not initially live. Historical Security-v2 lifecycle acceptance was kept
as implementation evidence, not promoted to current provider availability.

## Reversible liveness transition

Repository/systemd ownership inspection showed modular libvirt is an external on-demand provider, not an
Ordivon intended-running infrastructure service. `virtqemud.socket` exists normally, is not masked, and owns
`/run/libvirt/virtqemud-sock`; `virtqemud.service` declares the expected `virtlogd` / `virtlockd` dependencies.

For qualification, Runtime performed only:

```text
systemctl start virtqemud.socket
```

No unit was enabled and no persistent configuration was changed.

After activation:

- `virtqemud.socket` -> `active`;
- `virsh -c qemu:///system` connected;
- an independent pre-test `virsh list --all --name` returned no domains.

## Authoritative lifecycle requalification

The existing Security-v2 owner script was reused rather than reimplementing VM lifecycle:

`platform/security/scripts/smoke_libvirt_lifecycle.sh ai-redteam-r4-libvirt-authoritative-20260927`

Executed through the Linux Runtime, it returned:

```text
libvirtLifecycle=RUNNING_QMP_OBSERVED
pciBusCount=1
networkInterfaces=0
postDestroy=ABSENT
```

The fixture is a transient KVM domain with 256 MiB RAM, one vCPU, q35, no guest disk, and no network
interface. The provider therefore re-proved create/start, running state, zero interfaces, libvirt-mediated
QMP observation, destroy, and transient-domain absence.

A second independent `virsh list --all --name` after the smoke returned no domains, so cleanup was not
accepted solely on the executor's own claim.

## Baseline restoration

Qualification activated the modular provider/helper sockets. Because R4 does not establish libvirt as
always-on Ordivon infrastructure, the experiment explicitly stopped the units it activated. Final
`ActiveState` observations for `virtqemud.socket`, `virtqemud-ro.socket`, `virtqemud-admin.socket`,
`virtlogd.socket`, and `virtlockd.socket` were all `inactive`.

No unit was enabled or disabled during qualification.

## Evidence-bound conclusion

Current evidence supports:

`INSTALLED -> ON_DEMAND_ACTIVATABLE -> LIBVIRT_LIFECYCLE_REQUALIFIED -> BASELINE_RESTORED`

It does **not** support `R4_HOSTILE_SANDBOX_READY`.

That stronger claim remains gated on realization of the exact R4 environment contract:

1. disposable base image/overlay identity and digest;
2. network policy realization (`none`, simulated, or explicitly mediated rather than open egress);
3. mount/device/credential isolation realization;
4. bounded resource controls;
5. independent observer binding;
6. exact `ExperimentEnvironmentSpec -> SandboxRealizationReceipt` reconciliation;
7. create -> observe -> teardown -> independent absence verification for that exact environment digest.

The R4 contract can therefore close independently of the later hostile-environment realization. R5-R7 own
the missing synthetic-world/effect/observer pieces needed before a real adversarial-code environment should
be admitted.
