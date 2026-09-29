# AI Red-Team Foundry R4 — Adversarial Experiment Environment Contract

Status: EXPERIMENTAL SECURITY STUDY / STACKED SUCCESSOR TO R3 / NOT PRODUCTION SECURITY AUTHORITY
Date: 2026-09-26

## Objective

R4 defines a machine-checkable isolation contract for adversarial AI experiments. It deliberately rejects
one-bit `sandboxed=true` claims. A sandbox claim is meaningful only relative to a threat model and an
explicit isolation vector.

R4 does not implement a hypervisor, container runtime, network proxy, secret broker, or policy engine.
Those remain external providers. Security v2 owns target authority/admission and evidence standing; Runtime
owns physical Job/Attempt truth; the sandbox provider owns physical isolation realization.

## Core law

`SandboxLabel != IsolationContract`

For hostile/adversarial-code experiments, current Runtime `contained_local` is not sufficient by itself.
It is a reduced-ambient-authority engineering profile. Hostile-code experiments require an independent
isolation owner such as a disposable VM or another provider whose contract proves the required isolation
vector.

## Isolation vector

R4 binds these dimensions independently:

- process isolation;
- kernel isolation;
- filesystem isolation;
- network policy;
- credential exposure;
- resource containment;
- device exposure;
- external-effect mediation;
- lifecycle/disposability;
- observer independence.

## Threat classes

R4 distinguishes three initial experiment classes:

- `semantic_only`: model/provider text evaluation with no Runtime tools or external effects;
- `synthetic_agent`: tool-bearing experiment against an in-memory/synthetic world;
- `hostile_code`: attacker/target may execute arbitrary generated code and must not be trusted with host authority.

The required isolation vector becomes strictly stronger as the threat class increases.

## Provider boundary

The selected hostile-code baseline is an external disposable VM provider. Existing Ordivon evidence shows
libvirt/QEMU/KVM lifecycle displacement is already proven for create/start/inspect/destroy mechanics, but
R4 does not infer that every libvirt domain automatically satisfies the hostile experiment profile.
The exact VM image, network, mounts, credentials, devices, budgets, observer, and teardown behavior must be
bound per experiment.

## Verification

```bash
python3 -m unittest discover -s studies/security/ai-redteam-foundry-r4/tests -p 'test_*.py' -v
python3 studies/security/ai-redteam-foundry-r4/scripts/run_contract_fixture.py
```

The fixture is local and synthetic. It creates no VM and performs no network action.
