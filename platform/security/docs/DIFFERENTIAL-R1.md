# Old Security -> Security v2 differential R1

Date: 2026-09-11

## Frozen inputs

Old Security subject:

- repository: `/root/projects/ordivon-security`
- revision: `5e3142b92fc5aed3259295b63c0300f01b45e04a`
- old native baseline: 477 tests passed, 5 skipped

Security v2 scanner revision at the end of R1/R2 development:

- `3a4fb206ff385859be8bf054150a3284d2772167`

## External-first result

The full old repository was scanned with the Security v2 external provider chain. Every provider completed mechanically and the evidence was bound to the exact old Security revision.

OPA standing:

- `BLOCKED`
- blocking providers: Gitleaks, Semgrep, Trivy
- mechanical-error providers: none
- missing evidence providers: none
- missing result providers: none
- OSV dependency vulnerabilities: none in the observed run

Redacted finding inventory:

- Gitleaks: 5 findings
  - 1 under `docs/`
  - 1 under `evidence/`
  - 2 under `research/`
  - 1 under current `src/`
- Semgrep: 2 findings, both under `research/experiments/`
- Trivy: 1 private-key finding under `research/ca-lic/toydesigner/keys/`

The single Gitleaks hit in current `src/` points at the keyword-argument line containing `run_token=run_token` in `windows_fabric_recovery_ownership.py`; no secret value was inspected or reproduced during this review. Treat it as a likely rule false positive pending rule-native adjudication if that old module were ever selected for migration.

## Migration interpretation

This R1 result does **not** mean the old Security project is globally insecure. It shows that a repository-wide blocking policy mixes production code with research/reproduction apparatus and therefore is too coarse for migration decisions.

The findings reinforce the v2 boundary:

1. research evidence, historical acceptance material, intentionally controlled fixtures, and reproduction apparatus must not automatically become the Security v2 production surface;
2. tool-native findings remain provider evidence until scope/currentness/policy determine applicability;
3. a finding in research apparatus is not a reason to migrate the apparatus into v2;
4. old generic VM/range/security-product mechanics remain deletion/delegation candidates unless a v2 consumer proves they are still required;
5. if an old production module is selected for migration, its provider findings must be resolved using the provider's native suppression/fix mechanisms rather than a new Ordivon exception framework.

## Proven differential properties

- provider finding != mechanical execution failure;
- complete provider evidence can be `BLOCKED` while every provider mechanically succeeds;
- clean evidence on the exact observed revision can be `CURRENT`;
- the same clean evidence relabelled to another revision becomes `STALE_EVIDENCE` before findings are used;
- external provider artifacts remain in SARIF/CycloneDX/provider-native formats; Ordivon stores only digest-bound references and decision metadata.

## Next migration gate

Before migrating old implementation code, establish explicit production/research scan scopes using provider-native configuration, then select one genuinely Ordivon-specific semantic consumer for differential migration. Do not copy old QEMU/KVM lifecycle, scanner wrappers, corpus mirroring, or research runners by default.
