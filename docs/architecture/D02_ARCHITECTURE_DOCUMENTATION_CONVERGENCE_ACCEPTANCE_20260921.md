# D02 — Architecture Documentation Convergence Acceptance

Date: 2026-09-21
Status: **ACCEPTED / COMPLETE**

D02 closes the architecture-convergence documentation programme only after current source, deployed owner topology, live Gateway routing, Runtime/Host owner standing, Skill standing, trace/identity boundaries, and repository drift checks were revalidated from canonical `main`.

## 1. Final canonical source

Final implementation baseline before this acceptance receipt:

```text
f15e7012927f838e0e434294242ab80d9ccf99b9
```

This baseline contains:

- the canonical current architecture projection;
- machine-readable deployed architecture standing;
- architecture documentation drift checks;
- caller-owned Harness Tool lifecycle OpenTelemetry projection;
- Gateway W3C owner propagation;
- Gateway authenticated audit span attributes;
- deployed-on-demand Workstation Vector OTLP → Tempo persistent/queryable trace backend;
- prior D01, E01, and E02 acceptance evidence.

The acceptance receipt itself is documentation-only and may therefore become a descendant of that implementation baseline without requiring a Gateway redeploy.

## 2. D02.1 — deployed-reality mapping

Canonical current architecture is now:

```text
docs/architecture/CURRENT_ARCHITECTURE.md
docs/architecture/deployed-architecture-r1.json
```

Present-tense architecture claims follow those files plus live owner readback. Historical execution plans and acceptance snapshots remain provenance only.

The normal Agent-facing route is:

```text
Agent client
  ├── native Agent Skills
  │      └── Method Router
  └── Agent Plugin
           ↓
     Cloudflare Access / OAuth
           ↓
     Gateway MCP
     Capability Router
       ├── Linux Runtime
       ├── Windows Runtime
       └── Host
```

Harness remains an independent Agent Run owner and is not currently a Gateway-routed capability.

Direct Runtime/Host MCPs are operator/admin/recovery surfaces. Skills MCP remains the exact ChatGPT compatibility edge established by C03.

## 3. D02.2 — Router terminology convergence

The architecture now mechanically distinguishes:

```text
Method Router
  = Agent Skill
  = HOW should an Agent approach the problem?
  = advisory procedure only

Capability Router
  = Gateway static projection
  = WHICH natural owner serves this named capability?
  = non-authoritative routing only
```

Method Router live resolution on the final acceptance pass:

- skill ID: `project-ordivon-next/method-router`;
- trust: `TRUSTED`;
- scan: `PASS`;
- instruction authority: `ADVISORY`;
- instruction digest: `sha256:9bfbc6d4bfde5b9122515d00ab354faaf0f631baab5f285d9846f2e878ca3b47`;
- package revision: `sha256:6de23a88d5ec4036bceda1ca1324fc15915f14350d88c76a714bec9caf0b9d45`.

An intentionally stale snapshot was rejected with `SNAPSHOT_STALE`; exact re-search + same-mode resolve succeeded. The snapshot fence therefore remains fail-closed.

## 4. D02.3 — architecture drift gate

Repository CI now includes:

```text
tools/repo/check_architecture_docs.py
tools/repo/test_architecture_docs.py
```

The gate verifies, among other things:

- default portable Plugin declares exactly one Gateway MCP server;
- default Gateway endpoint is `https://gateway-mcp.ordivon.com/mcp`;
- Gateway is non-authoritative;
- Method Router remains an Agent Skill;
- Capability Router remains a Gateway projection;
- exact Gateway capability set matches source;
- Harness is not silently added as a Gateway route;
- Agent Service remains `RETIRED_DO_NOT_RECONSTRUCT`;
- historical architecture snapshots carry explicit supersession markers;
- optional Tempo tracing remains cold-by-default;
- Gateway trace export remains opt-in;
- observability cannot become product correctness authority.

Final fresh-main `repo:ci` at `f15e7012…` passed:

- affected-owner tests: PASS;
- owner boundary checks: PASS;
- composition architecture graph: PASS;
- composition graph tests: 6/6 PASS;
- architecture documentation drift: PASS;
- architecture drift tests: 11/11 PASS;
- integrate-main smoke: PASS;
- GitHub governance: PASS;
- `git diff --check`: PASS.

## 5. Side-line deployment divergence found and eliminated

The final D02 pass intentionally compared running Gateway source identity with canonical `main`.

It found that the running release was:

```text
c98cf3b5c0cbfdadf74222ed097db3db17428fe3
```

and that this SHA was **not an ancestor of canonical main**.

The side-line contained:

1. `f4ef166b` — standards-native W3C trace propagation to owner MCP calls;
2. `ba70a71f` — an intermediate deployed-owner documentation snapshot;
3. `c98cf3b5` — Gateway trace/audit enrichment plus optional Workstation Tempo profile.

This was treated as a real deployed/source convergence blocker rather than hidden by documentation.

Resolution:

- replayed `f4ef166b` onto current main;
- replayed `c98cf3b5` onto current main;
- intentionally did not replay the superseded intermediate `ba70a71f` documentation snapshot because D02 already owns the newer canonical deployed architecture projection;
- corrected current observability standing;
- verified Gateway and Workstation owners;
- landed the replay using expected-main CAS;
- redeployed Gateway from the exact canonical implementation SHA `eadd7e47…`.

## 6. Gateway / Workstation regression acceptance

After side-line convergence:

### Gateway

`mise run gateway:verify` passed completely.

The canonical Gateway retains MCP 2.2 and external OpenTelemetry runtime dependencies while keeping owner/domain truth outside telemetry.

### Workstation

`mise run workstation:verify` passed completely:

- Workstation Python suite: **182 passed**;
- Cloudflare provider suite: **29/29 passed**;
- provider typecheck/build/policy/operations checks: PASS.

Tempo therefore remains a Workstation-owned deployed-on-demand observability capability rather than Gateway semantic state. The merged candidate additionally passed native Vector validation, Ansible trace-playbook syntax validation, and Tempo 3.0.3 `-config.verify=true`.

## 7. Current observability standing

A previous E01 T05 acceptance proved the then-current Vector OTLP transport while trace storage was deferred.

A later accepted observability slice introduced a mature local trace backend:

```text
Gateway OTLP
   ↓
Vector
   ↓
Tempo
```

Current deployment standing separates **admission** from **activation**:

- Vector → Tempo persistent/queryable tracing: **accepted / deployed on demand**;
- Vector OTLP decoding: **`traces: true`**, preserving the OTLP envelope required by the downstream OpenTelemetry sink;
- Tempo version: **3.0.3**, loopback OTLP/query endpoints and local storage;
- Workstation heavy-observability target: **inactive by default**;
- Tempo service: **inactive by default**;
- Gateway `40-otel-traces.conf`: **absent in the current cold posture**;
- Gateway `OTEL_TRACES_EXPORTER`: **none in the base service**;
- Tempo cold-stop budget: Quadlet **`StopTimeout=60`** under systemd **`TimeoutStopSec=75`**.

The persistent backend is therefore a real, live-accepted capability rather than merely installed source, while activation remains explicit and product correctness remains independent from telemetry availability. The supplemental acceptance is `PERSISTENT_TRACE_BACKEND_ACCEPTANCE_20260921.md`.

## 8. Canonical Gateway redeploy

Gateway was rebuilt using the canonical release installer from exact SHA:

```text
eadd7e474292644b23bdd9cdfc96f52f017f8094
```

Final service readback:

- current release: `eadd7e47…`;
- `ActiveState=active`;
- `SubState=running`;
- `NRestarts=0`;
- health: PASS;
- public Access drop-in: retained;
- Windows service-identity drop-in: retained;
- trace exporter: `none`.

This eliminates the previous side-line deployment/source divergence.

## 9. Final live owner graph

Gateway `system.describe` reports:

- `runtime.linux` configured;
- `runtime.windows` configured;
- `host` configured.

Canonical Gateway capabilities are exactly:

- `artifact.runtime`;
- `continuity.external`;
- `execution.linux`;
- `execution.windows`.

All four were individually observed as `configured=true / available=true`.

Runtime owner readback:

- Linux node: `linux-local`, native Linux, `local_linux` available;
- Windows node: `windows-main-r6-candidate`, native Windows, `windows_native` available;
- Windows authorities: `limited`, `elevated`, `active_user`.

Gateway → Host continuity read also returned D01 revision 3 as completed.

## 10. Fresh post-deploy execution E2E

### Linux

New Gateway operation:

```text
ordivon-exec:v1:runtime.linux:job-01a0c462-fa9d-7b70-9fde-d228f11ea5ac
```

Result:

- state: succeeded;
- terminal: true;
- delivery: committed;
- execution disposition: succeeded;
- exit code: 0;
- recovery required: false;
- artifacts: 4.

### Windows

New Gateway operation:

```text
ordivon-exec:v1:runtime.windows:job-01a0c463-0f60-7093-be9f-d29a6a802d37
```

using limited native authority and the Windows Runtime-owned workspace.

Result:

- state: succeeded;
- terminal: true;
- delivery: committed;
- execution disposition: succeeded;
- exit code: 0;
- recovery required: false;
- artifacts: 5;
- Runtime-owned `windows-start` identity artifact: present.

This is fresh D02 evidence, not reuse of the older C02 Windows success.

## 11. prerequisite gates

Final Host continuity readback:

- D01 compatibility retirement: revision 3, completed;
- E01 trace convergence: revision 2, completed;
- E02 identity convergence: revision 2, completed.

D02 therefore no longer has prerequisite blockers.

## 12. Client metadata non-blocking observation

The current ChatGPT-side tool metadata in this conversation still exposed a historical `capability.list` entry. The live canonical Gateway correctly rejected that old name as unknown.

Canonical server source exposes:

- `system.describe`;
- `capability.describe`;
- execution/artifact/continuity operations.

The old alias is therefore treated as stale client-side schema/cache metadata, not as Gateway deployed architecture or semantic compatibility authority. D02 does not reintroduce a server alias merely to satisfy stale client metadata.


## 13. Concurrent closeout reconciliation

A concurrent D02 closeout writer advanced Host continuity from revision 2 to revision 3 while this acceptance was being finalized. Its newer evidence was not overwritten.

The concurrent isolated line contained:

- `f83b3c0963b1d448acafae603253e777f144edfc` — admit the persistent/queryable Vector → Tempo backend after live differential falsification;
- `eb9e0c1c11e4fc8a4363a4549204594a36f2d455` — add Tempo graceful cold-stop budgets after a live 31-second successful shutdown.

Those commits shared ancestor `81c93f09…` with the current convergence line and therefore required semantic, not mechanical, reconciliation. The final replay on top of the then-current main produced:

- `a32280366898d920466275d98baa7cf325b18196` — reconciled persistent backend;
- `f15e7012927f838e0e434294242ab80d9ccf99b9` — reconciled graceful-stop fix.

The merge retained both classes of evidence:

1. **deployed-on-demand** is the capability/admission standing;
2. **cold/inactive by default** is the current activation posture.

The final merged candidate passed:

- Vector native config validation;
- Ansible trace-playbook syntax validation;
- Tempo 3.0.3 native config verification;
- Gateway full verify;
- Workstation full verify (**182 passed** plus Cloudflare provider **29/29**);
- repository CI;
- architecture drift tests (**11/11**);
- `git diff --check`.

### Shared primary recovery

The primary checkout initially appeared to contain ~50 staged deletions/modifications after the main ref had advanced. Before touching it, its worktree and index were proven identical, with no untracked files, and its index tree was identified exactly as the already-committed tree of `9ecb6685211a841454b926267c36db615e90c979`.

Only after that proof and under the repository's `ordivon-main-integration.lock`, the primary checkout was rematerialized from `refs/heads/main` using `git restore --source=refs/heads/main --staged --worktree -- .`. No branch ref reset or force update was used. The repository-native `check-primary-main.sh` then returned PASS.

Final canonical implementation verification at `f15e7012…` additionally proved:

- primary checkout clean and synchronized;
- installed Tempo config byte-identical to source;
- installed Tempo Quadlet contains `StopTimeout=60` and `TimeoutStopSec=75`;
- live Vector config contains `traces: true` and the Tempo OTLP sink;
- heavy observability target inactive;
- Tempo inactive;
- Gateway trace drop-in absent;
- Gateway base exporter `none`;
- deployed Gateway release `eadd7e47…` is an ancestor of final canonical source.

## 14. Final result

D02.1–D02.4 are complete.

The resulting architecture has one current present-tense projection, explicit natural-owner boundaries, explicit historical-document standing, a machine-checked drift gate, aligned source/deployment lineage for Gateway, an admitted on-demand Vector→Tempo trace backend with falsification-derived OTLP preservation and graceful cold-stop constraints, and fresh Linux/Windows/Host/Skill live acceptance.

No remaining D02 architecture blocker is known.
