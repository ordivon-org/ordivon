# Ordivon Harness capability-to-consumer coverage (source-bound)

Scope: current independent review based on A+B three-crate integrated HEAD
6d97f2a08265152a2771addb87877f85e2338c40 (Python code from remote
main 485fbcdc). B's newer, separately reviewed clean commit
110c792cd669d6c1ec1904c1c275250a0fb2a439 adds Provider V4 read-only
and Domain Tool Surface; those are NOT in the 6d97 baseline branch.
This report does not claim live production installation or deployed consumers.

| Logical consumer stage | Existing Python producer/consumer | Rust ability verified | Missing actual consumer transition |
| --- | --- | --- | --- |
| Run Admission / binding | core_contracts.HarnessRunContract; agent_run.HarnessAgentRun; CLI entrypoint | CanonicalDocument and PG RunProjection/read_run_readonly | Versioned full Contract validator and native create/claim/lease writer. Independent scratch PG RED a377fc shows semantic mismatch even with correct hashes |
| Provider request/recovery | ordivon/provider_lifecycle.py; ordivon/run_continuity.py; continuity_records.py V3/V4 | B provider_head.inspect_v4 in 86868d8 / 110c792, read-only, 525 source vectors; model effects absent | Durable dispatch admission, v3 legacy continuity, native Provider callback/receipt reconciliation; UNKNOWN remains unknown |
| Model-visible Context | ordivon/turn_projection.py; working_view.py; ordivon/loop.py | B evidence pure progress/Tool selector; source oracle 640+400 | A validated Contract + actual Context Compiler + token/compaction/provider dialect per caller; not yet one Rust model request |
| Domain Tool selection | domain_tools.DomainToolCatalog / _GrantedDomainToolBridge | B tool_surface.rs in 110c792 exact catalog/grant digest+definitions; 224 real Python source vectors | Real execution capability admitted by Gateway/Runtime, separate no-tool/runtime-search modes, Tool Intent/Receipt/UNKNOWN bridging |
| Physical Tool execution | ordivon/runtime_bridge.py; tool_program.py; runtime_port.py | None in reviewed Rust crates | Existing Runtime job identity/fence/foreign refs and owner-native reconcile, not a second shell or custom scheduler |
| Journal + CAS | postgres_store.PostgresHarnessStore; store.py | Rust harness-pg read_run_readonly; PG18 Python writer -> SELECT-only Rust read 5/5; malformed digest/refs/revision rejected, deep legacy UNKNOWN | Full contract semantic validator, exact native writer with lease/revision, old Run takeover/consumer acceptance |
| Completion / domain result | completion.py; Domain consumers | Rust has pure progress gates only | Candidate completion vs Domain acceptance with explicit proof/receipt and consumer |
| External client API | cli.py, agent_run.py | No Rust production CLI/SDK verified | One versioned Run command/progress/interrupt/resume API, not one CLI per tool |
| Durable work and cross-agent cooperation | Ordivon Host Space/Topic/Work | Host externally established; not Harness crate | Maintain owner boundary; Harness may consume bounded assignment, never duplicate Host |
| Long-term artifact + memory | object_store.py, Artifact/Media and domain owners | CAS value/PG readback only | Return artifact and context references, not a second global memory owner |

## Admission distinction that mattered in this review

Hash-valid CAS object != semantically valid Run Contract != dispatch-authorized
Provider/Tool != observed physical effect != domain goal success. Current
Rust reader checks the first (and parts of Journal chain) but not full
HarnessRunContract. A test-only, scratch PostgreSQL case produces a valid
hash+event chain with blank providerId; Python source rejects, Rust accepts.
See the companion README and local C test commit a377fcfe109ff56fcdc1f4ba96f8104fb50f50a6.

## Explicit current acceptance posture

- Rust Canonical / PG read-only *source and database transport*: qualified
  for the bounded Python-generated cases, not all Python Contract semantics.
- Rust B Provider V4 / ToolSurface *pure source projections*: independently
  rebuilt on 110c792; source-oracle tests pass but no live Provider/Tool Run.
- Rust History consumer *full legacy Contract*: **REJECT promotion** because
  of the reproducible semantic source mismatch described above.
- Native Rust PG Writer, Tool execution, Context→Model, privacy and
  recovery-to-domain consumer: **UNKNOWN / not built or not independently
  qualified**. UNKNOWN is not false and cannot be called PASS.
