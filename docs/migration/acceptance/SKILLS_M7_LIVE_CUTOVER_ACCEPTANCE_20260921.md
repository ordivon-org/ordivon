# Skills M7 live cutover acceptance — 2026-09-21

Standing: **ACCEPTED_LIVE**

Scope: cut the production Skills MCP from the pre-monorepo Harness snapshot and Workstation-owned Python carrier to the canonical platform/skills owner, revision-bound release, Skills-owned Python 3.14.7 environment, and monorepo project Skill binding.

This acceptance is separate from M6 source relocation. M6 established owner boundaries; M7 proves the live service and a real connected consumer now use those boundaries.

## Exact source and release identity

Accepted Skills source revision:

60ed225ba271e21127a89a5a3b870f05ce2ff568

Accepted platform/skills tree:

41c0d8713f79df1585c6043fd896fb46148a5117

The immutable release was built as an exact Git archive of platform/skills at that revision:

/opt/ordivon/skills-mcp/releases/60ed225ba271e21127a89a5a3b870f05ce2ff568

The tracked release file set matched the Git tree exactly: 39 files.

Concurrent monorepo work later advanced main without changing the platform/skills tree. The accepted release revision remained an ancestor of current main and retained exact owner-tree identity, so the already validated release was not rebuilt merely because unrelated owners advanced.

## Runtime carrier cutover

Before M7, the Skills service executed through the Workstation-owned carrier:

/root/.local/share/ordivon-workstation/skills-mcp-v1/.venv/bin/python

Python version: 3.12.13.

M7 moved runtime ownership to the Skills release family:

/opt/ordivon/skills-mcp/current-env/bin/python

Current environment:

/opt/ordivon/skills-mcp/envs/60ed225ba271e21127a89a5a3b870f05ce2ff568

Python version: **3.14.7**.

The live systemd MainPID command was read back after cutover and uses the new current-env Python plus the current release scripts. OAuth environment/drop-in ownership remained unchanged.

## Project binding cutover

The prior live project binding was:

ordivon-next -> /root/projects/ordivon-next

The accepted live binding is:

ordivon-next -> /root/projects/ordivon/meta/next

All other live config source/trust rows were preserved. M7 did not rewrite vendor/user source semantics.

Active release source/config/unit census found zero references to:

- /root/projects/ordivon-next/.agents/skills
- /root/projects/ordivon-harness
- the old Workstation Skills Python carrier

## Preflight and false-negative diagnosis

The candidate source check passed before production cutover:

- nine catalog sources READY
- four tools: skills.list, skills.read, skills.resolve, skills.search
- Agent Skills standard exportable: 24
- standard rejected: 19
- catalog revision: sha256:cddfdd894a87e9632b22ad06ef6f369bd4d53c4d984a2b8351ed3d23952614cd

An initial candidate readiness attempt used port 8896 and returned 401. This result was discarded after physical inspection showed that 8896 was already owned by Ordivon Agent Automation MCP. The request had reached the wrong service.

The Skills candidate was rerun on isolated port 18995 and passed the complete readiness check. No authentication regression existed.

## Live source and protocol acceptance

After atomic cutover:

- service: active / running
- bind: 127.0.0.1:8895
- current release: 60ed225...
- current environment: 60ed225...
- Python: 3.14.7
- live source check: ok
- catalog revision: sha256:cddfdd894a87e9632b22ad06ef6f369bd4d53c4d984a2b8351ed3d23952614cd
- public Cloudflare OAuth boundary: PASS
- local four-tool surface: PASS
- SEP-2640 discover/list/get/resources-read and resource-integrity path: PASS
- consumer readiness: ready

The live cutover operation used prepared rollback state and restored the prior release/config/unit automatically on any failed postcondition. No rollback was triggered.

## Real connected consumer acceptance

Mechanical service liveness was not treated as sufficient.

A real connected Skills consumer executed:

1. skills.search in workspace ordivon-next;
2. skills.resolve under the returned exact snapshot;
3. skills.read under exact snapshot, instruction-digest, and package-revision fences.

The search returned catalog revision:

sha256:cddfdd894a87e9632b22ad06ef6f369bd4d53c4d984a2b8351ed3d23952614cd

and snapshot revision:

sha256:7aac9e23c06477ad047a596e2c99379eee8c05072e88ca0bca6f0475ea43a334

The accepted project-owned binding was:

- skillId: project-ordivon-next/design-structure-matrix
- sourceId: project-ordivon-next
- scope: project
- trust: TRUSTED
- scan: PASS
- instruction digest: sha256:f4bd81409e067108115797ab24d80dd8bbb8f2368ca94ac1ce6be3836b8fbbc7
- package revision: sha256:56b1b9e63421fc78ff9df145ae82cf65d8762cdba38ff093fe41c857c59e34d3

Exact SKILL.md read succeeded:

- size: 2299 bytes
- read digest: sha256:f4bd81409e067108115797ab24d80dd8bbb8f2368ca94ac1ce6be3836b8fbbc7
- projection: ADVISORY_SANITIZED

This proves the consumer is resolving project Skills through the live monorepo-owned source binding rather than merely consuming an unrelated vendor source.

## Fail-closed fence acceptance

Three deliberately incorrect fences were tested independently:

- wrong snapshot revision -> SNAPSHOT_STALE
- wrong instruction digest -> DIGEST_MISMATCH
- wrong package revision -> PACKAGE_CHANGED

No stale or mismatched content was substituted.

## Rollback witness

Rollback material is retained under:

/opt/ordivon/skills-mcp/rollback/60ed225ba271e21127a89a5a3b870f05ce2ff568

The previous release remains present:

/opt/ordivon/skills-mcp/releases/3d1943e349c21141468f95551e4ee37adc40f7f4

Without bouncing the accepted production service, the old Python 3.12.13 carrier and the preserved pre-cutover config were used to run the old release source check successfully. This proves the rollback artifacts and old carrier remain mechanically usable.

An actual rollback-and-forward rehearsal was deliberately not performed after successful live acceptance because it would introduce production churn without adding a new owner-boundary claim.

## Evidence digests

- external cutover receipt SHA-256: eb8d8c9a4e8b2e0d4b88e04a22d024de875c8ae7523325f4dbb594595f3068e1
- pre-cutover config backup SHA-256: 76f036ae3f965df070bbd94b2204375a4fda6ed637842d1ba151be9a93d27eff
- pre-cutover unit backup SHA-256: 227400597155aaa4e76bd2e5b8359d6d52aa4d1d88d9026fc49511800e622c29
- accepted live config SHA-256: 15e888c4000f7755889384ad983aa3dd6e5c5a93d5319ab9d4465c6347ab2381
- accepted live unit SHA-256: fe922776e223680302cdd55e4012b29334445cfa0004f50b68cd4879bfb4a73e

No credential material is present in the repository receipt.

## Accepted boundary

M7 establishes that production Skills MCP now consumes the platform/skills owner and monorepo project source through exact revision/currentness fences.

It does not make platform/skills a semantic owner of Agent Skills, does not make Agent Plugin the canonical Skill owner, does not grant Skill execution authority, and does not authorize retirement of historical source repositories by itself.
