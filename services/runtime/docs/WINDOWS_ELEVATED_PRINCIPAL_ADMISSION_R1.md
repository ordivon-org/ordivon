# Windows Privileged Admission R1

Status: SOURCE CANDIDATE — release only with explicit operator principal/profile configuration and live acceptance.

## Incident trigger

A generic `windows_native` Runtime Job obtained an elevated token and invoked `Optimize-VHD` directly against the WSL distro VHDX. That bypassed the existing Workstation D-drive R3/R4 owner protocol. Parallel recovery actors then restarted WSL while the offline effect was still uncertain. The repair therefore separates authentication, token privilege, privileged-effect admission, maintenance exclusion, provider effect truth, and semantic completion.

## Authority split

1. **Authentication** — Runtime derives the effective principal from trusted transport state.
2. **Token availability** — the native broker can physically realize limited/elevated Windows tokens.
3. **Principal ceiling** — `ORDIVON_WINDOWS_ELEVATED_PRINCIPALS_JSON` names principals allowed to request any elevated profile.
4. **Effect profile** — `ORDIVON_WINDOWS_ELEVATED_PROFILES_JSON` binds a stable profile id to allowed principals and exact executable/argument surfaces.
5. **Profile selection** — a Job selects one operator profile with a `foreignReference` `{namespace:"ordivon.windows", type:"privileged_profile", id:"..."}`. The caller-authored reference is only a selector; it never creates or widens authority.
6. **Maintenance exclusion** — `ORDIVON_WINDOWS_MAINTENANCE_LEASE_PATH` points at the owner-native D-drive R3 `active-request.json`. A valid unexpired transaction fences every *new* `windows_native` execution, including limited/active-user recovery attempts.
7. **Provider truth** — D-drive R3/R4 still owns drain, READY, authorization, WSL offline, detached/exclusive VHD proof, exactly one compact pass, recovery, and receipts.
8. **Semantic completion** — process exit or Job cancellation is not proof that an external storage effect quiesced.

Exact Job replay is resolved before the new admission policy. Historical committed Jobs therefore remain reattachable even after the operator tightens current policy. `job.get/list/observe` are observation/control surfaces rather than new execution admission.

## Operator configuration

`ORDIVON_WINDOWS_ELEVATED_PRINCIPALS_JSON` is a JSON array of authenticated Runtime principal ids. An empty/absent set fails closed for new elevated Jobs. Limited Windows execution remains available outside an active maintenance lease.

`ORDIVON_WINDOWS_ELEVATED_PROFILES_JSON` is a JSON array. Each profile has:

- `id`: stable operator id;
- `principals`: subset allowed to select that profile;
- `commands`: exact executable plus exact argument prefix;
- `allowAdditionalArguments`: whether arguments beyond the bound prefix are allowed.

The primary command and **every structured step** must match a command rule. Non-elevated execution cannot select a privileged profile. Caller-supplied profile generation/digest claims are rejected because the profile is operator policy, not caller-owned evidence.

D-drive example (abbreviated):

```json
[{
  "id": "workstation.d-drive-compact-r3",
  "principals": ["principal:windows-main"],
  "commands": [{
    "executable": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "argumentPrefix": ["-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass","-File","D:\\OrdivonStudio\\d-drive-compact-run-r3.ps1"],
    "allowAdditionalArguments": false
  }]
}]
```

This allows the owner provider entrypoint; it does **not** allow arbitrary `PowerShell -Command`, `Optimize-VHD`, `wsl.exe`, `vmcompute`, or HCS recovery effects. Other legitimate elevated consumers require their own bounded provider/profile migration.

`ORDIVON_WINDOWS_MAINTENANCE_LEASE_PATH` should point to `D:\OrdivonStudio\maintenance\active-request.json`. R3 writes schema-v3 request evidence with both human-readable `expiresAtUtc` and machine `expiresAtUnixMs`. Runtime fails closed on malformed present lease state, fences new Windows execution while the lease is live, and permits admission again when the lease is absent or expired. R3 additionally suppresses the canonical `Ordivon WSL Control Plane Recovery` scheduled task after publishing the lease and restores it before deleting the lease.

## Why this is not a command blacklist

The model does not search PowerShell text for dangerous verbs. Elevated authority is granted only through operator-owned capability profiles tied to natural-owner entrypoints. Token privilege is an implementation resource; it is not effect authorization. This is closer to constrained administration/JEA and provider capabilities than to denylisting command strings.

## Migration and acceptance

Before live cutover:

- census current elevated consumers; generic diagnostics/mutations that still need elevation must move to dedicated owner profiles;
- configure the intended principal ceiling, at least one positive provider profile, and the maintenance lease path;
- prove generic elevated PowerShell without a profile is rejected;
- prove a valid provider profile admits only its bound entrypoint and rejects profile escape through extra structured steps;
- prove active maintenance lease rejects new limited and elevated Windows execution while exact historical replay remains observable;
- prove expired lease does not deadlock future admission;
- prove D-drive R3 publishes lease before suppressing recovery and restores recovery before releasing the lease;
- release through the structured Windows Runtime release path and verify live configuration/currentness.

## Non-goals

R1 does not infer user intent, create global IAM, parse arbitrary PowerShell commands, claim OS-wide exclusion against an unrelated administrator outside Runtime/provider authority, or treat process cancellation as external-effect quiescence. Social Work Fabric remains the human/agent coordination layer; owner-native lease/admission is the machine enforcement layer.
