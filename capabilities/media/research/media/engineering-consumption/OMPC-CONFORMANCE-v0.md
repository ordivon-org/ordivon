# OMPC-v0 Conformance Corpus

**Status:** technology-neutral recovery/conformance index. This file is not a production schema, validator implementation, API contract, database design, or authority registry.

The corpus exists to answer four questions for each OMPC invariant:

1. Which real consumer falsified or exercised it?
2. What exact source fence/evidence anchors the result?
3. What negative equivalence is rejected?
4. What concrete future observation would reopen the invariant or contract wording?

## Fixture families

### Fixture A — Host continuity/currentness projection

Files:

- `fixtures/host-task-rev3-human.md`
- `fixtures/host-task-rev3-agent.json`
- `fixtures/host-task-rev3-dogfood.md`

Source fence:

- owner: Ordivon Host;
- Task: `task:ordivon-media-project-inception-m0-m1-20260818`;
- exact source revision: 3;
- source checkpoint digest: `sha256:695cf6a3cba795a3a93c774c65517b6741f093fd953d6ca20978fcffff7988b0`;
- destructive currentness observation: the same Host Task later advanced to revision 4.

Primary pressure: observer-relative projection, source authority, omission, currentness, action exposure.

### Fixture B — Studio transformation/provenance/identity

Files:

- `fixtures/studio-expression-card-lineage.json`
- `fixtures/studio-expression-card-dogfood.md`

Source fence/evidence:

- Production: `productions/studio-expression-card`;
- historical source binding: `ordivon-studio` revision `90e2b5d46b0f16171d242633454714017a14f2f2`;
- Production introduced by Git commit `1061d740c01aec9272fd3bc50bdbf8a32da2c1b1`;
- editable SVG Blob: `sha256:a8ed35e9f9e4ab993a9e62ad6935e4a111eba3c391ea1854e954036364824128`;
- selected PNG Blob: `sha256:fc19d4cf27982fd177c9411245fb994a970551e105866348ee03e9deed6bcce4`;
- non-visual source-byte variant: `sha256:71ad25b513075412f51ae9f155209df68a5bcf110023fb356e646e042957d541`, still rendering to the exact selected PNG bytes.

Primary pressure: transformation lineage, semantic identity vs Blob identity, editable-source loss, lifecycle standing.

### Fixture C — Web interaction trajectory/time/state/feedback

Files:

- `fixtures/web-m7-trajectory-lineage.json`
- `fixtures/web-m7-trajectory-dogfood.md`

Source fence/evidence:

- owner: Ordivon Web;
- observed source revision: `407d151f0939de87286be50ec24ca35fc2c04bb4`;
- runner introduced by `fa3b00c210a14bb58a50350870eb4322fcabed37`;
- runner: `scripts/run-m7-interaction.mjs`;
- fresh real-Chromium evidence digest: `sha256:1469ce31fc89f064087ca12a4db163ac1975d84bde4bd115b9dd5d38f25cd14e`;
- common final screenshot digest across lawful/premature-success/silent-delay: `sha256:d2b7d88af0ecffd3d96b25a21df53604a6998ee3f98f87db78750ff5f4dae84e`.

Primary pressure: temporal coverage, transient state, action→feedback trajectory, endpoint-equivalence failure.

### Fixture D — Finance metric/proxy/legibility

Files:

- `fixtures/finance-qb6-metric-legibility-lineage.json`
- `fixtures/finance-qb6-metric-legibility-dogfood.md`

Source fence/evidence:

- owner: Ordivon Finance;
- observed source revision: `6ed0730ce6f7b067ddb56d806a744e121b987402`;
- first QB6 evidence file digest: `sha256:261887acd11177c43ed9e03f07003e8b586658bd485384fcc0a4910b928590bb`;
- followup QB6 evidence file digest: `sha256:343f541d87e002be407f62d7d53e0dc7530ff9b813d44f94175b37602e732ccd`;
- both introduced by `ac882d94c94700e8558b39003c00cdf41271ca5b`;
- supporting APF anti-law digest: `sha256:1cc4cef93bceca95cfd4f74268707b79bd33e60e359ebb1bb61cfebe6e9bc717`, introduced by `42c92b4ca539c0d0b1b93317bc7b5df8fb6ec34b`.

Primary pressure: datafication/legibility, metric/proxy scope, owner/context omission, decision non-lifting.

## Invariant coverage matrix

| # | Invariant | A Host | B Studio | C Web | D Finance | Rejected collapse |
|---|---|---|---|---|---|---|
| 1 | Source Authority Conservation | primary | primary | primary | primary | projection == source truth |
| 2 | No Semantic/Standing Lifting | primary | primary | primary | primary | display/output/metric/transient claim silently strengthens source standing |
| 3 | Exact Fence Traceability | primary | primary | primary | primary | recent recovery locator/render/report substitutes for exact source fence |
| 4 | Observer Relativity | primary | supporting | supporting | supporting | same source requires identical observer realization |
| 5 | Loss/Omission Disclosure | primary | primary | primary | primary | omitted material is treated as absent from source/encounter/domain context |
| 6 | Currentness Non-Fabrication | primary | primary | supporting | primary | latest render/recovery/metric card implies current source applicability |
| 7 | Action Non-Execution | primary | not exercised | primary | supporting | affordance/request/displayed metric or success == authorization/execution |
| 8 | Cross-Modality Semantic Equivalence | primary | supporting | supporting | supporting | byte/form equality is required for semantic equivalence |
| 9 | Identity Non-Collapse | supporting | primary | supporting | supporting | semantic ID, Blob, realization, source identity, locator collapse |
| 10 | Temporal Coverage Non-Collapse | not exercised | not exercised | primary | not exercised | same initial+final == same encounter |
| 11 | Metric / Proxy Non-Collapse | not exercised | supporting | supporting | primary | visible metric/score/proxy == underlying target truth or decision eligibility |

`primary` means the fixture directly falsified/exercised the invariant. `supporting` means the fixture independently preserves the distinction but was not designed as its strongest falsifier. `not exercised` means no positive conformance claim is made for that fixture/invariant pair.

## Reopen/failure criteria

OMPC-v0 is a falsifiable reference contract. A future consumer reopens contract wording when real evidence demonstrates one of the following:

1. **Authority failure** — a useful projection cannot preserve source-owner authority without becoming unusably incomplete, and the failure cannot be repaired by disclosure/scope.
2. **Fence failure** — a real owner has no meaningful exact or bounded source fence, and OMPC cannot represent the owner-specific standing honestly.
3. **Observer failure** — two materially different observers require incompatible source-claim semantics rather than merely different representations.
4. **Loss failure** — material omission/transformation loss cannot be described without importing source-owner semantics Media does not own.
5. **Identity failure** — a real consumer requires identity relations not expressible without collapsing semantic, byte, realization, authority, or locator identity.
6. **Temporal failure** — a trajectory/encounter claim requires temporal semantics that cannot remain inside projection coverage/provenance without a new Media responsibility.
7. **Action failure** — observer-facing action cannot be separated from external authorization/admission/execution without duplicating source-owner authority.
8. **Cross-modality failure** — materially equivalent source claims cannot be maintained across modalities without a stronger relation than current semantic-equivalence wording.
9. **Metric/proxy failure** — a decision- or interpretation-facing projection cannot disclose a metric's material definition, scope, proxy/attribution standing or omitted eligibility context without importing domain semantics Media does not own.

A failure may revise OMPC roles/invariants. It does **not** automatically reopen MF0–MF9, admit MF10, or justify a shared Media runtime.

## Extraction gate

The corpus currently demonstrates repeated **semantic contract pressure** across four materially different consumers. It does not demonstrate repeated **implementation machinery**.

Therefore the admitted shared artifact is:

```text
OMPC-v0 reference contract
+ conformance corpus
+ destructive fixtures
```

Not admitted:

```text
Media Engine
Media Runtime
Media SDK
universal OMPC serializer/schema
universal validator service
```

A shared implementation extraction requires at least one real cross-consumer duplication/failure case where owner-local implementations repeat the same machinery and a shared capability reduces responsibility or error rather than merely centralizing code.
